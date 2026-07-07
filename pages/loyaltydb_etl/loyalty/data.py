import numpy as np
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


ROOT = "\\\\OMINFFLSD05001V.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada")

from okada import SQL


# Create the connection
conn = SQL("datamart").get_loader()

def get_last_update():
    sql = f"""
    SELECT MAX(updatedate) FROM dws.dws_mkt_loyaltydb
    """

    data = conn.load_data(sql)
    return data.values[0][0]


class Data:
    def __init__(self):
        sql = f"""
        SELECT  
            natgrp,
            gender,
            loygrp,
            contactable,
            language,
            age,
            su_year,
            `12moactive` as `12moactive`,
            dom,
            adtgrp,
            vfreqgrp,
            vlengrp,
            total_theo,
            total_theo_tg,
            total_theo_eg,
            total_visits,
            total_visits_tg,
            total_visits_eg,
            unique_pid_count,
            total_timemins,
            total_timeminstg,
            total_timeminseg,
            updatedate
        FROM dws.dws_mkt_loyaltydb
        """
        self.data = conn.load_data(sql)
        self.data.columns = ["NatGrp",
            "Gender",
            "LoyGrp",
            "Contactable",
            "Language",
            "Age",
            "SU_year",
            "12moActive",
            "Dom",
            "ADTGrp",
            "VFreqGrp",
            "VLenGrp",
            "Theo",
            "Theo_TG",
            "Theo_EG",
            "Visits",
            "Visits_TG",
            "Visits_EG",
            "PID",
            "TimeMins",
            "TimeMinsTG",
            "TimeMinsEG",
            "UpdateDate"]
        print(f"reading data")
        self._preprocess()

    def _preprocess(self):
        self.data["Hours"] = self.data["TimeMins"] / 60
        self.data = self.data.drop("TimeMins", axis=1)
    def load(self):
        return self.data
