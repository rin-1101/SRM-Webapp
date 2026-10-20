# %% [markdown]
# # Duplicate Accounts

# %%
import pandas as pd
import numpy as np
import calendar
import re
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
import datetime as dt
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService

import warnings
warnings.filterwarnings("ignore")

loader = SQL("engage").get_loader()

# %% [markdown]
# # Full Scan

# %%
# timestamps
today = pd.Timestamp.today().normalize()

# first day of the previous month
start_month = today.replace(day=1) - pd.offsets.MonthBegin(1)

# last day of the previous month
end_month = today.replace(day=1) - pd.Timedelta(days=1)

start_month, end_month

# %%
# assumption: 
# today is sept 1
# start month is aug 1
# end month is aug 31

# %%
# gets the info of players as well as their gender and flags
# revoked accounts are EXCLUDED as per admin's request

query = f"""

WITH gender AS (
    SELECT 
        PlayerID, 
        MAX(Gender) AS Gender
    FROM ENGAGEDB.dbo.UC_PL_Identification
    GROUP BY PlayerID),

flag AS (
    SELECT
        pf.PlayerID,
        STRING_AGG(NULLIF(LTRIM(RTRIM(xf.FlagShortName)), ''), ' | ') AS Flag
    FROM ENGAGEDB.FLG.UC_PL_Flag pf
    INNER JOIN ENGAGEDB.FLG.UC_X_Flag xf
        ON pf.FlagTypeID = xf.FlagID
    WHERE pf.Active = 1
    GROUP BY pf.PlayerID)

SELECT 
    p.PlayerID, 
    UPPER(LTRIM(RTRIM(p.UniversalPlayerID))) AS UniversalPlayerID, 
    UPPER(LTRIM(RTRIM(p.FirstName))) AS FirstName, 
    UPPER(LTRIM(RTRIM(p.MiddleName))) AS MiddleName, 
    UPPER(LTRIM(RTRIM(p.LastName))) AS LastName,
    p.BirthDate, 
    p.CreatedDate, 
    p.CreatedBy, 
    g.Gender,
    f.Flag AS Flag
FROM ENGAGEDB.dbo.UC_PL_Player p
LEFT JOIN gender g ON p.PlayerID = g.PlayerID
LEFT JOIN flag f ON p.PlayerID = f.PlayerID
WHERE p.BirthDate IS NOT NULL
  AND (f.Flag IS NULL
        OR (UPPER(f.Flag) NOT LIKE '%ZZ%'
            AND UPPER(f.Flag) NOT LIKE '%TA%'
            AND UPPER(f.Flag) NOT LIKE '%RE%'))

"""

fullscan = loader.load_data(query)
fullscan['FirstName'] = fullscan['FirstName'].str.strip().str.title()
fullscan['MiddleName'] = fullscan['MiddleName'].str.strip().str.title()
fullscan['LastName'] = fullscan['LastName'].str.strip().str.title()
fullscan['UniversalPlayerID'] = fullscan['UniversalPlayerID'].str.strip()
fullscan['Flag'] = fullscan['Flag'].fillna('')
print(fullscan.shape)
pd.DataFrame(fullscan)
fullscan.head()

# %%
# function to find the group they belong to; used for duplicates
def find_group(account):
    current_group = groups[account]
    while current_group != account:
        next_group = groups[current_group]
        account = current_group
        current_group = next_group
    final_group = current_group
    return final_group

# %%
# function to group duplicates
def combine_accounts(account1, account2):
    account1_group = find_group(account1)
    account2_group = find_group(account2)
    
    if account1_group == account2_group:
        return 
    else:
        groups[account2_group] = account1_group 

# %%
# lists the accounts as indexes
groups = list(range(len(fullscan)))

# places them in numpy arrays for better row accessing (pls para di na gumamit nung .loc wahaha di q kabisado syntax mb)
last_names = fullscan['LastName'].to_numpy()
middle_names = fullscan['MiddleName'].to_numpy()
genders = fullscan['Gender'].to_numpy()

# %%
# checks duplicates by same firstname and birthdate
for _, i in fullscan.groupby(['FirstName', 'BirthDate'], sort=False):
    
    indexes = i.index.to_numpy()

    if len(indexes) < 2:
        continue
    else:
        same_last_name = {}
        
        # sorts by last name
        for account in indexes:
            last_name = last_names[account]
            
            if last_name not in same_last_name:
                same_last_name[last_name] = []
            else:
                pass
            
            same_last_name[last_name].append(account)
        
        # groups accounts with the same last names
        for account in indexes:
            current_last_name = last_names[account]
            
            accounts_with_same_last_name = (same_last_name[current_last_name])
            
            for other_account in accounts_with_same_last_name:
                combine_accounts(account, other_account)
            
            # female maiden-married
            current_gender = genders[account]
            current_middle_name = middle_names[account]
            
            if current_gender == 'F':
                if pd.notna(current_middle_name):
                    if current_middle_name != "":
                        if current_middle_name in same_last_name:
                            accounts_with_matching_name = (same_last_name[current_middle_name])
                            for other_account in accounts_with_matching_name:
                                combine_accounts(account, other_account)

# %%
# assigns the final group to every account
duplicate_groups = []

for account in range(len(fullscan)):
    account_group = find_group(account)
    duplicate_groups.append(account_group)

fullscan['DupGroup'] = duplicate_groups
fullscan.head()

# %%
group_counts = fullscan.groupby('DupGroup')['UniversalPlayerID'].nunique().reset_index()
group_counts = group_counts.rename(columns={'UniversalPlayerID': 'Count'})
duplicate_groups = group_counts[group_counts['Count'] >= 2]
duplicates = fullscan[fullscan['DupGroup'].isin(duplicate_groups['DupGroup'])].copy()
duplicates = duplicates.sort_values(['FirstName', 'BirthDate', 'CreatedDate']).reset_index(drop=True)
print(duplicates.shape)
duplicates.head()

# %%
COLS = ['PlayerID', 'UniversalPlayerID', 'FirstName', 'MiddleName', 'LastName', 'Gender', 'BirthDate', 'CreatedDate', 'CreatedBy', 'Flag']

duplicates = duplicates.drop_duplicates()
duplicates[COLS].head()

# %% [markdown]
# # Monthly Report

# %%
# full scan vs new sign ups for the month

# %%
# gets the fullscan of profiles historical and monthly
# historical - until end of full scan (end of previous month)
historical = fullscan[fullscan['CreatedDate'] < start_month].copy()

# monthly - first day of the current month until the last day
monthly = fullscan[(fullscan['CreatedDate'] >= start_month) & (fullscan['CreatedDate'] <= end_month)].copy()

# reset indices
historical = historical.reset_index(drop=True)
monthly = monthly.reset_index(drop=True)

monthlyscan = pd.concat([historical, monthly], ignore_index=True).reset_index(drop=True)
print(monthly.shape)

# %%
groups = list(range(len(monthlyscan)))

last_names = monthlyscan['LastName'].fillna('').to_numpy()
middle_names = monthlyscan['MiddleName'].fillna('').to_numpy()
genders = monthlyscan['Gender'].fillna('').to_numpy()

# %%
# checks duplicates by same firstname and birthdate
for _, i in monthlyscan.groupby(['FirstName', 'BirthDate'], sort=False):
    
    indexes = i.index.to_numpy()

    if len(indexes) < 2:
        continue
    else:
        same_last_name = {}
        
        # sorts by last name
        for account in indexes:
            last_name = last_names[account]
            
            if last_name not in same_last_name:
                same_last_name[last_name] = []
            else:
                pass
            
            same_last_name[last_name].append(account)
        
        # groups accounts with the same last names
        for account in indexes:
            current_last_name = last_names[account]
            
            accounts_with_same_last_name = (same_last_name[current_last_name])
            
            for other_account in accounts_with_same_last_name:
                combine_accounts(account, other_account)
            
            # female maiden-married
            current_gender = genders[account]
            current_middle_name = middle_names[account]
            
            if current_gender == 'F':
                if pd.notna(current_middle_name):
                    if current_middle_name != "":
                        if current_middle_name in same_last_name:
                            accounts_with_matching_name = (same_last_name[current_middle_name])
                            for other_account in accounts_with_matching_name:
                                combine_accounts(account, other_account)

# %%
duplicate_groups = []

for account in range(len(monthlyscan)):
    account_group = find_group(account)
    duplicate_groups.append(account_group)

monthlyscan['DupGroup'] = duplicate_groups
monthly_groups = set(monthlyscan.iloc[len(historical):]['DupGroup'])

group_counts = monthlyscan.groupby('DupGroup').size()
duplicate_groups = set(group_counts[group_counts >= 2].index)
monthly_duplicate_groups = (monthly_groups.intersection(duplicate_groups))

monthly_duplicates = monthlyscan[monthlyscan['DupGroup'].isin(monthly_duplicate_groups)].copy()
monthly_duplicates = monthly_duplicates.sort_values(['DupGroup', 'CreatedDate']).reset_index(drop=True)
monthly_duplicates

# %%
first_accounts = monthly_duplicates.groupby('DupGroup', as_index=False).first()
first_accounts = first_accounts[['DupGroup', 'UniversalPlayerID']]
first_accounts = first_accounts.rename(columns={'UniversalPlayerID': 'FirstAccount'})

monthly_duplicates = monthly_duplicates.merge(first_accounts,on='DupGroup',how='left')
monthly_duplicates = monthly_duplicates.sort_values(['FirstName', 'BirthDate','CreatedDate']).reset_index(drop=True)
print(len(monthly_duplicates))
monthly_duplicates

# %%
COLS = ['PlayerID', 'UniversalPlayerID', 'FirstName', 'MiddleName', 'LastName', 'Gender', 'BirthDate', 'CreatedDate', 'CreatedBy', 'Flag', 'FirstAccount']

monthly_duplicates = monthly_duplicates.drop_duplicates()
monthly_duplicates[COLS].head()

# %% [markdown]
# # Automation

# %%
ed = end_month.strftime('%b %Y')
md = end_month.strftime('%B %d, %Y')
ed, md

# %%
path = r'\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Shared Folder\Admin\Duplicate Account/'
sm_path = r'\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Regular Reports\AML Report\Duplicate Account/'

file_name = f'Duplicate Accounts as of {ed}.xlsx'

with pd.ExcelWriter(path + file_name, engine='xlsxwriter') as file_path:
    monthly_duplicates[COLS].to_excel(file_path, sheet_name='Duplicate Accounts',index=False)

with pd.ExcelWriter(sm_path + file_name, engine='xlsxwriter') as sm_file_path:
    monthly_duplicates[COLS].to_excel(sm_file_path, sheet_name='Duplicate Accounts',index=False)



