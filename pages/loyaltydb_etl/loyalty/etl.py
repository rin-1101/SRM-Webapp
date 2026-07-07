#!/usr/bin/env python
# coding: utf-8
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 11:17:30 2020

@author: Wendy.Ni
"""
"""
Edited on Tue Oct 28 2024

@editor: Rin
- converted from CRM to HIVE
"""

import numpy as np
import pandas as pd
import pyodbc
from openpyxl import load_workbook
import datetime as dt
from datetime import datetime, time, date, timedelta
import pyodbc
from functools import reduce
import xlsxwriter as xw


# Connection
server = "ominfstdpsd10001p-fs.int.okadamanila.com"

import sys
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService

# Connection
server = "ominfstdpsd10001p-fs.int.okadamanila.com"

import sys
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService

hloader = SQL("hive").get_loader()
# import patron profile & ratings data from SQL


# import member profile
sql_profile = """ 
SELECT 
    DISTINCT uid AS `PID`,
    nationality AS `NatGrp`,
    gender AS `Gender`,
    tier AS `LoyGrp`,
    CASE 
        WHEN contactable = '1' THEN 'Cont' 
        ELSE 'NonCont' 
    END AS `Contactable`,
    language AS `Language`,
    agegroup2 AS `Age`,
    createdgamedate AS `SU_date`,
    YEAR(createdgamedate) AS `SU_year`,
    CAST(DATEDIFF(CURRENT_TIMESTAMP, createdgamedate) AS FLOAT) / 365 AS `Tenure_yrs`
FROM 
    dws.dws_mkt_memberprofile;
"""
# import 12 month cash play rated KPIs
sql_kpi = """
SELECT 
    universalplayerid `pid`, 
    DATEDIFF(DATE_SUB(CURRENT_TIMESTAMP, 1), MAX(gamingdate)) AS DSLV, 
    COUNT(DISTINCT gamingdate) AS visits,
    COUNT(DISTINCT CASE WHEN tg_theowin_cash + tg_theowin_cash_online > 0 THEN gamingdate ELSE NULL END) AS Visits_TG,
    COUNT(DISTINCT CASE WHEN slot_theowin_cash + slot_theowin_cash_online + etg_theowin_cash > 0 THEN gamingdate ELSE NULL END) AS Visits_EG,
    SUM(total_theowincash) AS Theo,
    SUM(tg_theowin_cash + tg_theowin_cash_online) AS Theo_TG,
    SUM(slot_theowin_cash + slot_theowin_cash_online + etg_theowin_cash) AS Theo_EG,
    SUM(total_timeplayed) AS TimeMins,
    SUM(slot_timeplayed + etg_timeplayed) AS TimeMinsTG,
    SUM(tg_timeplayed_cash + tg_timeplayed_cash_online) AS TimeMinsEG,
    CASE 
        WHEN SUM(tg_theowin_cash + tg_theowin_cash_online) / SUM(total_theowincash) >= 0.6 THEN 'TGDom' 
        WHEN SUM(slot_theowin_cash + slot_theowin_cash_online + etg_theowin_cash) / SUM(total_theowincash) >= 0.6 THEN 'EGDom' 
        ELSE 'Cross' 
    END AS dom,
    CASE 
        WHEN SUM(total_theowincash) / COUNT(DISTINCT gamingdate) >= 30000 THEN 'A.30k'
        WHEN SUM(total_theowincash) / COUNT(DISTINCT gamingdate) >= 20000 THEN 'B.20k' 
        WHEN SUM(total_theowincash) / COUNT(DISTINCT gamingdate) >= 10000 THEN 'C.10k'
        WHEN SUM(total_theowincash) / COUNT(DISTINCT gamingdate) >= 5000 THEN 'D.5k'
        WHEN SUM(total_theowincash) / COUNT(DISTINCT gamingdate) >= 1000 THEN 'X.1k'
        ELSE 'Z' 
    END AS ADTGrp,
    CASE 
        WHEN COUNT(DISTINCT gamingdate) >= 156 THEN '1.3x pw'
        WHEN COUNT(DISTINCT gamingdate) >= 104 THEN '2.2x pw'
        WHEN COUNT(DISTINCT gamingdate) >= 52 THEN '3.Weekly'
        WHEN COUNT(DISTINCT gamingdate) >= 26 THEN '4.Fortnightly'
        WHEN COUNT(DISTINCT gamingdate) >= 12 THEN '5.Monthly'
        WHEN COUNT(DISTINCT gamingdate) >= 4 THEN '6.Quarterly'
        ELSE '7.Low' 
    END AS VFreqGrp,
    CASE 
        WHEN SUM(total_timeplayed) / 60 / COUNT(DISTINCT gamingdate) >= 5 THEN '1.5 hours'
        WHEN SUM(total_timeplayed) / 60 / COUNT(DISTINCT gamingdate) >= 4 THEN '2.4 hours'
        WHEN SUM(total_timeplayed) / 60 / COUNT(DISTINCT gamingdate) >= 3 THEN '3.3 hours'
        WHEN SUM(total_timeplayed) / 60 / COUNT(DISTINCT gamingdate) >= 2 THEN '4.2 hours'
        WHEN SUM(total_timeplayed) / 60 / COUNT(DISTINCT gamingdate) >= 1 THEN '5.1 hours'
        ELSE '6.Low' 
    END AS VLenGrp
FROM 
    dws.dws_mkt_memberdaily_ooc
WHERE 
    gamingdate BETWEEN DATE_SUB(CURRENT_TIMESTAMP, 365) AND DATE_SUB(CURRENT_TIMESTAMP, 1)
    AND total_theowincash <> 0 
GROUP BY 
    universalplayerid
"""

# import 13 month cash play rated stats - run at 1st day of each month
sql_rated = """
SELECT 
    universalplayerid AS `PID`,
    YEAR(gamingdate) * 100 + MONTH(gamingdate) AS `vint`,
    WEEKOFYEAR(gamingdate) AS `week`,
    tg_casinowin_cash AS `AwinCash`,
    slot_casinowin + slot_casinowin_online + etg_casinowin AS `AwinEG`,
    tg_casinowin_cash + tg_casinowin_cash_online AS `AwinTG`,
    total_theowincash AS `TwinCash`,
    tg_theowin_cash + tg_theowin_cash_online AS `Twin_TG`,
    slot_theowin_cash + slot_theowin_cash_online + etg_theowin_cash AS `Twin_EG`,
    slot_turnover_cash AS `CoinIn_EG`,
    total_timeplayed AS `TimeMins`,
    slot_timeplayed + slot_timeplayed_online + etg_timeplayed AS `TimeMinsEG`,
    tg_timeplayed_cash + tg_timeplayed_cash_online AS `TimeMinsTG`,
    total_tierpoints + ng_lifestylepoints AS `Points`,
    total_tierpoints AS `PointsG`,
    ng_lifestylepoints AS `PointsNG`,
    tg_tierpoints + tg_tierpoints_online AS `PointsTG`,
    slot_tierpoints + slot_tierpoints_online + etg_tierpoints AS `PointsEG`
FROM 
    dws.dws_mkt_memberdaily_ooc
WHERE 
    gamingdate BETWEEN DATE_SUB(ADD_MONTHS(CURRENT_DATE, -13), 1) AND DATE_SUB(CURRENT_DATE, 1)
    AND total_theowincash <> 0;

"""

patron_profile = hloader.load_data(sql_profile)
patron_kpi = hloader.load_data(sql_kpi)
patron_rated = hloader.load_data(sql_rated)

patron_profile['loygrp'] = np.where(patron_profile['loygrp'].str.contains('Okada'),'1.Okada VIP',
                        np.where(patron_profile['loygrp']=='Maharlika','2.Maharlika',
                        np.where(patron_profile['loygrp']=='Supreme','3.Supreme',
                        np.where(patron_profile['loygrp']=='Premium','4.Premium',
                        np.where(patron_profile['loygrp']=='Elite','5.Elite',
                        np.where(patron_profile['loygrp']=='Prime','6.Prime','7.Others'))))))



patron_db = patron_profile.merge(patron_kpi, on="pid", how="left")
patron_db["12moactive"] = np.where(np.isnan(patron_db["dslv"]), "Inactive", "Active")
patron_db["dom"] = patron_db["dom"].fillna("Inactive")
patron_db["adtgrp"] = patron_db["adtgrp"].fillna("Inactive")
patron_db["vfreqgrp"] = patron_db["vfreqgrp"].fillna("8.Inactive")
patron_db["vlengrp"] = patron_db["vlengrp"].fillna("7.Inactive")

db_summ = (
    patron_db.groupby(
        [
            "natgrp",
            "gender",
            "loygrp",
            "contactable",
            "language",
            "age",
            "su_year",
            "12moactive",
            "dom",
            "adtgrp",
            "vfreqgrp",
            "vlengrp",
        ]
    )
    .aggregate(
        {
            "theo": sum,
            "theo_tg": sum,
            "theo_eg": sum,
            "visits": sum,
            "visits_tg": sum,
            "visits_eg": sum,
            "pid": "nunique",
            "timemins": sum,
            "timeminstg": sum,
            "timeminseg": sum,
        }
    )
    .reset_index()
)

patron_db.head(10)
db_summ.head()
patron_db["dom"].value_counts()
patron_db["12moActive"].describe()


#%%
import os

path = r"L:\Strategic Marketing\Database Admin\Python Training\zz_Rin\loyalty\LoyaltyDBNew.xlsx"

# Check if the file exists
if not os.path.exists(path):
    # Create an empty DataFrame
    df = pd.DataFrame()
    
    # Save it as an Excel file
    df.to_excel(path, index=False)

# Now you can proceed to load the workbook as before
from openpyxl import load_workbook

# Load existing workbook
book = load_workbook(path)
writer = pd.ExcelWriter(path, engine="openpyxl")
writer.book = book

# Replace existing sheets
db_summ.to_excel(writer, sheet_name="DB", index=False)
writer.save()



