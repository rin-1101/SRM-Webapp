# %%
import pandas as pd
import numpy as np
import pyodbc
import datetime as dt
from datetime import datetime, date, timedelta, time
from pandas.tseries.offsets import MonthBegin, MonthEnd
from dateutil.relativedelta import relativedelta
import sys
server = "10.36.21.40"
try:
    connection_string = ("DRIVER={ODBC Driver 13 for SQL Server};SERVER=" + server + ";Trusted_Connection=yes")
    conn =  pyodbc.connect(connection_string, autocommit=True)
except:
    connection_string = ("DRIVER={SQL Server};SERVER=" + server + ";Trusted_Connection=yes")
    conn =  pyodbc.connect(connection_string, autocommit=True)
server2 = "10.36.184.43"
# Build connection string
connection_string2 = (
    f"DRIVER={{Cloudera ODBC Driver for Apache Hive}};"
    f"Host={server2};Port=10000;"
    "AuthMech=3;"  # Authentication mechanism: User & Password
    "UseSASL=1;"   # Ensure SASL is enabled
    "SSL=1;"       # Enable SSL
    "AllowSelfSignedServerCert=1;"  # Trust self-signed certs
    "AllowHostNameCNMismatch=1;"  # Ignore hostname mismatches
)
conn_hive = pyodbc.connect(connection_string2, HIVESERVERTYPE=2, autocommit=True, UID="hive", PWD="hive")

# %%

# exclude 108, 107, 105

today=dt.date.today()
# today=dt.date(2024,9,9)
yest=today-timedelta(days=1)
p3m=pd.to_datetime(yest-timedelta(days=89))
p6m=pd.to_datetime(yest-timedelta(days=189))
p7d=pd.to_datetime(yest-timedelta(days=6))
p14=pd.to_datetime(yest-timedelta(days=13))
min_date = p6m
yest, p3m , p6m, p7d

sql="""
SELECT gdate, SUM(hotelnights) as hotelnights, SUM(hotelcomp) as hotelcomp
FROM `dws`.`dws_mkt_reinvestment` 
where gdate>='{}'
GROUP BY gdate
ORDER BY gdate
""".format(p14.date())
hotel=pd.read_sql(sql,conn_hive)
hotel.columns=hotel.columns.str.replace('dws_mkt_reinvestment.','')

if hotel.shape[0] < 14:
    raise Exception("Please review the Reinvestment (Hotel)")
elif hotel['hotelnights'].min() == 0:
    raise Exception("Please review the Reinvestment (Hotel)")
elif hotel['hotelcomp'].min() == 0:
    raise Exception("Please review the Reinvestment (Hotel)")

# %%
sql="""
SELECT uid  as UniversalPlayerID, fullname as fullname, hostname_mass as Team, nationality as Nationality
FROM `dws`.`dws_mkt_memberprofile`

"""
profile=pd.read_sql(sql,conn_hive)
profile.head(2)

# %%
sql="""
SELECT universalplayerid as UniversalPlayerID, gdate, hotelnights, hotelcomp, dcomp_fp,dcomp_prize, comp_fnb,comp_cigarette,comp_spa,comp_transport,comp_retail
FROM `dws`.`dws_mkt_reinvestment` 
where gdate>='{}'
""".format(min_date.date())
ri=pd.read_sql(sql,conn_hive)
ri.columns=ri.columns.str.replace('dws_mkt_reinvestment.','')
ri['gdate']=pd.to_datetime(ri['gdate'])
ri['Dcomp_NonRoom']=ri.iloc[:,4:].sum(axis=1)
ri.head(2)

# %%
ri.keys()

# %%
def grouping(x,y,z,j):
    temp=x[x[y]>=z].groupby('UniversalPlayerID',as_index=False)[j].sum()
    return temp

# %%
ri_p6m=grouping(ri,'gdate',p6m,['hotelnights', 'hotelcomp', 'Dcomp_NonRoom'])
ri_p3m=grouping(ri,'gdate',p3m,['hotelnights', 'hotelcomp', 'Dcomp_NonRoom'])
ri_p7d=grouping(ri,'gdate',p7d,['hotelnights', 'hotelcomp', 'Dcomp_NonRoom'])
ri_p6m.head()

# %%
sql="""
select universalplayerid as UniversalPlayerID, gamingdate as gamingdate, total_theowincash as TwinCash
FROM `dws`.`dws_mkt_memberdaily_ooc` 
where total_theowincash>0 and gamingdate>='{}'
""".format(min_date.date())
mdg=pd.read_sql(sql,conn_hive)
mdg['gamingdate']=pd.to_datetime(mdg['gamingdate'])
mdg.head(2)

# %%
theo_p6m=grouping(mdg,'gamingdate',p6m,['TwinCash'])
theo_p3m=grouping(mdg,'gamingdate',p3m,['TwinCash'])
theo_p7d=grouping(mdg,'gamingdate',p7d,['TwinCash'])
theo_p7d.head(2)

# %%
def merging(x,y):
    temp=x.merge(y,on='UniversalPlayerID',how='outer').fillna(0)
    temp['RI']=(temp['hotelcomp']+temp['Dcomp_NonRoom'])/temp['TwinCash']
    return temp

# %%
df_p6m=merging(theo_p6m,ri_p6m).fillna(np.inf)
df_p3m=merging(theo_p3m,ri_p3m).fillna(np.inf)
df_p7d=merging(theo_p7d,ri_p7d).fillna(np.inf)
df_p7d.head() 

# %%
ri_p6m[ri_p6m['UniversalPlayerID']=='OM000154385']

# %%
overcomp=df_p6m[(df_p6m['RI']>0.5) & ((df_p6m['hotelcomp']+df_p6m['Dcomp_NonRoom'])>0) ].sort_values('RI',ascending=False).merge(profile,on='UniversalPlayerID')
overcomp=overcomp[['UniversalPlayerID','fullname', 'Team','Nationality','RI','TwinCash', 'hotelnights', 'hotelcomp','Dcomp_NonRoom']].merge(df_p3m,on='UniversalPlayerID',how='left',suffixes=('_p6m','_p3m')).merge(df_p7d,on='UniversalPlayerID',how='left').fillna({'Team':'Uncoded'}).fillna(0)
overcomp=overcomp.rename(columns={'TwinCash':'TwinCash_p7d','hotelnights':'hotelnights_p7d','Dcomp_NonRoom':'Dcomp_NonRoom_p7d','RI':'RI_p7d'})
overcomp=overcomp[~overcomp['Team'].str.contains('IA|OB')]
overcomp=overcomp.sort_values(['RI_p6m','hotelnights_p6m'],ascending=False)
overcomp.head()

# %%
# overcomp.to_excel(r'L:\Strategic Marketing\Shared Folder\CM Audit\Overcomp Report - Weekly\Weekly Overcomp Report {}.xlsx'.format(str(yest)),index=False)
# overcomp.to_excel(r'L:\Strategic Marketing\Shared Folder\CM Programs\Overcomp Report\Weekly Overcomp Report {}.xlsx'.format(str(yest)),index=False)
def get_overcomp():
    return overcomp
PATH = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\overcomp"
df = get_overcomp()
df.to_csv(f"{PATH}\\overcomp_{today}.csv",index=False)


import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")

from okada import EmailService
from okada.contacts import GAMING_ANALYTICS

BD = "Gizelle.Leong@okadamanila.com;Jennylyn.Ang@okadamanila.com;Kangnae.Lee@okadamanila.com;Nick.Park@okadamanila.com;Sandy.Valeriano@okadamanila.com;Weng.Sim@okadamanila.com"
subject = f"Overcomp Report - {today}"
recepients = "<Louie.Urrutia@okadamanila.com>;  <MariaTheresa.Romero@okadamanila.com>; <Sue.Gooi@okadamanila.com>;  <Seiya.Kishimoto@okadamanila.com>; <Ashley.Chen@okadamanila.com>; <Chin.Yang@okadamanila.com>;  <Sasha.Lan@okadamanila.com>; <Kryzler.Sanga@okadamanila.com>"
copys = f"{GAMING_ANALYTICS};{BD}"
mailer = EmailService(recepients, copys, subject)
mailer.send_mail(f"Overcomp Report updated for {today} on below URL: \n https://srm.okadamanila.com/overcomp")