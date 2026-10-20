import pandas as pd
import os
import logging
from datetime import datetime, timedelta

import sys
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService

hloader = SQL("datamart").get_loader()
loader = SQL("engage").get_loader()


def fmt(value):
    """Format a number into b/m/k shorthand with 1 decimal place."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}b"
    elif abs_val >= 1_000_000:
        return f"{value / 1_000_000:.1f}m"
    elif abs_val >= 1_000:
        return f"{value / 1_000:.1f}k"
    else:
        return f"{value:.1f}"


def fmt_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply fmt() to all numeric columns in a DataFrame."""
    result = df.copy()
    for col in result.select_dtypes(include="number").columns:
        result[col] = result[col].apply(fmt)
    return result


class Patron:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.universalplayerid = None

    def set_patron(self, universalplayerid):
        self.universalplayerid = universalplayerid

    def set_reference(self, reference):
        self.referencedate = reference

    def get_patron_details(self):
        sql = f"""
            SELECT 
                concat(firstname, ' ', lastname) AS fullname, 
                mp.nationality AS nationality,
                hostname_mass AS host,
                tier AS tier,
                CASE 
                    WHEN contactable = '1' THEN 'True'
                    ELSE 'False'
                END AS marketable,
                lastplaydate AS lastplaydate,
                daysinactive AS daysinactive,
                'NA' AS churn,
                mp.createdgamedate AS createddate,
                mp.birthdate as birthdate
            FROM dws.dws_mkt_memberprofile mp 
            LEFT JOIN dws.dws_mkt_memberbuild mb
                ON mp.universalplayerid = mb.universalplayerid
            WHERE mp.universalplayerid = '{self.universalplayerid}'
            AND mb.gamingdate = '{(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")}'
        """

        main_df = hloader.load_data(sql)

        if main_df.empty:
            return "Patron Not Found", sql, None, None, None, None, None, None, None

        row = main_df.iloc[0]

        return (
            row['fullname'],
            row['nationality'],
            row['host'],
            row['tier'],
            row['marketable'],
            row['lastplaydate'],
            row['daysinactive'],
            row['churn'],
            row['createddate'],
            row['birthdate']
        )

    def get_cash(self):
        sql = f"""
            SELECT 
                adt_30days, adt_90days, adt_180days, total_theowincash_lifetime/visits_lifetime as adt_lifetime,
                visits_30days, visits_90days, visits_180days, visits_lifetime,
                totalri_p3m, totalri_p6m,
                total_theowincash_30days, total_theowincash_90days, total_theowincash_180days, total_theowincash_lifetime,
                total_casinowincash_30days, total_casinowincash_90days, total_casinowincash_180days, total_casinowincash_lifetime,
                adt_last12, onday_total_casinowincash 
            FROM dws.dws_mkt_memberbuild 
            WHERE gamingdate = '{(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")}'
            AND universalplayerid = '{self.universalplayerid}'
        """
        main_df = hloader.load_data(sql)
        main_df = main_df.round(2)

        adt_df = main_df[['adt_30days', 'adt_90days', 'adt_180days', 'adt_lifetime']].copy()
        adt_df.columns = ['past 30 days', 'past 90 days', 'past 180 days', 'Lifetime']

        visit_df = main_df[['visits_30days', 'visits_90days', 'visits_180days', 'visits_lifetime']].copy()
        visit_df.columns = ['past 30 days', 'past 90 days', 'past 180 days', 'Lifetime']

        ri_df = main_df[['totalri_p3m', 'totalri_p6m']].copy()
        ri_df.columns = ['RI% past 3 months', 'RI% past 6 months']

        twin_df = main_df[['total_theowincash_30days', 'total_theowincash_90days', 'total_theowincash_180days', 'total_theowincash_lifetime']].copy()
        twin_df.columns = ['past 30 days', 'past 90 days', 'past 180 days', 'Lifetime']

        cwin_df = main_df[['total_casinowincash_30days', 'total_casinowincash_90days', 'total_casinowincash_180days', 'total_casinowincash_lifetime']].copy()
        cwin_df.columns = ['past 30 days', 'past 90 days', 'past 180 days', 'Lifetime']
        
        last12_df = main_df[['adt_last12']].copy()
        last12_df.columns = ['ADT Last 12 Visits']

        return (
            fmt_df(adt_df),
            fmt_df(visit_df),
            fmt_df(ri_df),
            fmt_df(twin_df),
            fmt_df(cwin_df),
            fmt_df(last12_df)
        )

    def get_last12visit(self):
        # FIX: changed TOP 12 (T-SQL) to LIMIT 12 (Hive)
        # 
        # return None, None
        sql = f"""
        SELECT gamingdate, casinowin, theowin
            FROM (
                SELECT
                    o.gamingdate,
                    o.total_casinowincash AS casinowin,
                    o.total_theowincash   AS theowin
                FROM dws.dws_mkt_memberdaily_ooc o
                JOIN dws.dws_mkt_memberprofile p
                ON p.universalplayerid = o.universalplayerid
                WHERE o.universalplayerid = '{self.universalplayerid}'
                AND o.total_theowincash > 0
                AND o.gamingdate >= p.createdgamedate
                ORDER BY o.gamingdate DESC
                LIMIT 12
            ) x
            ORDER BY gamingdate ASC;
        """
        main_df = hloader.load_data(sql)
        twinl12 = main_df[['gamingdate', 'theowin']].copy()
        cwinl12 = main_df[['gamingdate', 'casinowin']].copy()
        return twinl12, cwinl12

    def get_rolling(self):
        sql = f"""
            SELECT
                gamingdate,
                tripcode,
                tripstart,
                tripend,
                rolling,
                casinowin
            FROM dwd.dwd_tg_rollingprogram r
            LEFT JOIN dws.dws_mkt_memberprofile p
                ON p.universalplayerid = r.universalplayerid
            WHERE r.universalplayerid = '{self.universalplayerid}'
            AND r.tripend >= p.createddate
        """
        
        df = hloader.load_data(sql)

        if df.empty:
            empty = pd.DataFrame(columns=['past 30 days', 'past 90 days', 'past 180 days', 'Lifetime'])
            return empty, empty, empty

        df['tripend'] = pd.to_datetime(df['tripend'])

        end_date = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)

        windows = {
            'past 30 days': 30,
            'past 90 days': 90,
            'past 180 days': 180
        }

        masks = {
            key: (df['tripend'] >= (end_date - pd.Timedelta(days=days))) &
                (df['tripend'] <= end_date)
            for key, days in windows.items()
        }

        def agg_sum(col):
            result = {
                key: df.loc[mask, col].sum()
                for key, mask in masks.items()
            }
            result['Lifetime'] = df[col].sum()
            return result

        rp_df = pd.DataFrame([agg_sum('rolling')])
        cwp_df = pd.DataFrame([agg_sum('casinowin')])

        trip_df = pd.DataFrame([{
            key: df.loc[mask, 'tripcode'].nunique()
            for key, mask in masks.items()
        }])

        return fmt_df(rp_df), fmt_df(cwp_df), fmt_df(trip_df)
