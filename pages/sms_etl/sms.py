import pandas as pd
import os
import logging
from datetime import datetime

import sys
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService

hloader = SQL("hive").get_loader()
"""
    TODO:
    DUPLICATES
    REMOVE FOLDER WHEN DELETING SMS BULK
    ADD EVENT CODE TO SMS BULK

    Add for EDM
"""
class SMS:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)


    def read_sms_content(self,  eventname: str = None , eventcode: str = None):
        sql = f"""
        select 
        eventname as EventName
        ,content as Content
        ,createddate as CreatedDate
        ,contenttype as ContentType
        ,eventcode as EventCode
        FROM default.db_communications_content
        where eventname like '%{eventname}%'
        """

        sms_content_df = hloader.load_data(sql)
        if len(sms_content_df)>0:
            sms_content_df.columns = ['eventname','content','createddate','contenttype','eventcode']
            
        # Apply filters if eventcode or eventname are provided
        # if eventcode:
        #     sms_content_df = sms_content_df[sms_content_df['eventcode'] == eventcode]
        # if eventname:
        #     sms_content_df = sms_content_df[sms_content_df['eventname'] == eventname]

        # Check if the DataFrame is empty before trying to access the content
        if sms_content_df.empty:
            return ""  # Return empty string if no matching content is found
        
        # Return the first content if it exists, or an empty string if the column is empty
        return sms_content_df['content'].iloc[0] if not sms_content_df['content'].empty else ""

    def read_sms_blast(
        self,
        eventcode: str = None,
        universalplayerid: str = None,
        eventname: str = None,
        startblastdate: datetime = None,
        endblastdate: datetime = None
    ):
        filters = []

        if eventcode:
            filters.append(f"eventid = '{eventcode}'")

        if universalplayerid:
            filters.append(f"universalplayerid like '%{universalplayerid}%'")

        if eventname:
            filters.append(f"upper(eventname) like upper('%{eventname}%')")

        if startblastdate:
            filters.append(f"blastdate >= '{startblastdate:%Y-%m-%d} 06:00:00'")

        if endblastdate:
            filters.append(f"blastdate <= '{endblastdate:%Y-%m-%d %H:%M:%S}'")

        conditions = ""
        if filters:
            conditions = "WHERE " + " AND ".join(filters)

        sql = f"""
        select universalplayerid as UniversalPlayerID
        ,firstname as FirstName
        ,lastname as lastname
        ,mobile as mobile
        ,prize as prize
        ,val1 as val1
        ,val2 as val2
        ,val3 as val3
        ,val4 as val4
        ,val5 as val5
        ,val6 as val6
        ,val7 as val7
        ,eventname as promotionname
        ,smscontent as smscontent
        ,channel as channel
        ,createddate as createddate
        ,blastdate as blastdate
        ,eventid as eventid
        FROM default.db_communications_blast
        {conditions}
        """
        df = hloader.load_data(sql)
        if len(df)>0:
            df.columns = ['UniversalPlayerID','FirstName','LastName','Mobile','Prize','Val1','Val2','Val3','Val4','Val5','Val6','Val7','PromotionName', 'SMSContent','Channel','CreatedDate','BlastDate','EventID']
        return df