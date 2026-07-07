import pandas as pd
import os
import logging
from datetime import datetime
"""
TODO:
DUPLICATES
REMOVE FOLDER WHEN DELETING SMS BULK
ADD EVENT CODE TO SMS BULK

Add for EDM
"""
class SMS:
    def __init__(self):
        self.path_sms_content = r"//ominfstdpsd10001p-fs.int.okadamanila.com/Casino/Strategic Marketing/Database Admin/ETL/Applications/okada/okada/utils/SMSDB/csv-test/blast"
        self.path_sms_blast = r"//ominfstdpsd10001p-fs.int.okadamanila.com/Casino/Strategic Marketing/Database Admin/ETL/Applications/okada/okada/utils/SMSDB/csv-test/content"

        os.makedirs(self.path_sms_content, exist_ok=True)
        os.makedirs(self.path_sms_blast, exist_ok=True)

        logging.basicConfig(level=logging.INFO)

    def clean_sms_blast_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        # new_df = dataframe[['UniversalPlayerID', 'mobile', 'prize']].copy()
        return dataframe

    def write_sms_content(self, eventcode, eventname, sms_content):
        file_path = os.path.join(self.path_sms_content, f"smscontent.csv")

        try:
            existing_df = pd.read_csv(file_path)
            logging.info(f"Loaded existing file: {file_path}")
        except (FileNotFoundError, OSError):
            logging.info(f"File not found, initializing new DataFrame for {file_path}")
            existing_df = pd.DataFrame(columns=["eventcode", "eventname", "content", "type"])

        if eventcode in existing_df['eventcode'].values:
            raise ValueError(f"Duplicate event code found: {eventcode}")

        sms_content_df = pd.DataFrame({
            "eventcode": [eventcode],
            "eventname": [eventname],
            "content": [sms_content],
            "type": ["SMS"]
        })

        updated_df = pd.concat([existing_df, sms_content_df], ignore_index=True)

        try:
            updated_df.to_csv(file_path, index=False, engine='pyarrow')
            logging.info(f"Successfully added SMS content for event code: {eventcode}")
        except Exception as e:
            logging.error(f"Error saving SMS content: {e}")



    def write_sms_blast(self, dataframe: pd.DataFrame, eventcode: str, blastdate: datetime):
        clean_df = self.clean_sms_blast_dataframe(dataframe)

        event_folder = os.path.join(self.path_sms_blast, eventcode)
        os.makedirs(event_folder, exist_ok=True)

        file_path = os.path.join(event_folder, f"blast_{blastdate.strftime('%Y-%m-%d_%H-%M-%S')}.csv")

        clean_df.to_csv(file_path, index=False, engine='pyarrow')
        logging.info(f"SMS blast for event code {eventcode} saved successfully.")

    def read_sms_content(self, eventcode: str = None, eventname: str = None):
        file_path = os.path.join(self.path_sms_content, f"smscontent.csv")

        try:
            sms_content_df = pd.read_csv(file_path)
        except FileNotFoundError:
            sms_content_df = pd.DataFrame()
            logging.warning("SMS content file not found. Returning empty DataFrame.")

        if eventcode:
            sms_content_df = sms_content_df[sms_content_df['eventcode'] == eventcode]
        if eventname:
            sms_content_df = sms_content_df[sms_content_df['eventname'] == eventname]

        return sms_content_df

    def remove_sms_content(self, eventcode: str):
        file_path = os.path.join(self.path_sms_content, f"smscontent.csv")

        try:
            sms_content_df = pd.read_csv(file_path)
        except FileNotFoundError:
            logging.warning("SMS content file not found.")
            return

        sms_content_df = sms_content_df[sms_content_df['eventcode'] != eventcode]
        sms_content_df.to_csv(file_path, index=False, engine='pyarrow')
        logging.info(f"SMS content for event code {eventcode} removed successfully.")

    def read_sms_blast(self, eventcode: str = None, universalplayerid: str = None, 
                    eventname: str = None, startblastdate: datetime = None, endblastdate: datetime = None):
        all_blasts = []
        if startblastdate:
            startblastdate = pd.to_datetime(startblastdate)

        if endblastdate:
            endblastdate = pd.to_datetime(endblastdate)

        for event_folder in os.listdir(self.path_sms_blast):
            event_path = os.path.join(self.path_sms_blast, event_folder)
            
            if not os.path.isdir(event_path):
                continue

            if eventcode and event_folder != eventcode:
                continue

            for file_name in os.listdir(event_path):
                file_path = os.path.join(event_path, file_name)
                
                if file_name.endswith(".csv"):
                    blast_df = pd.read_csv(file_path)
                    blast_df['UniversalPlayerID'] = blast_df['UniversalPlayerID'].astype(str)
                    blast_df['Promotion Name'] = blast_df['Promotion Name'].astype(str)

                    if universalplayerid:
                        blast_df = blast_df[blast_df['UniversalPlayerID'].str.contains(str(universalplayerid))]

                    if eventname:
                        blast_df = blast_df[blast_df['Promotion Name'].str.contains(str(eventname))]

                    blast_df['BlastDate'] = pd.to_datetime(blast_df['BlastDate'], errors='coerce')

                    if startblastdate and blast_df['BlastDate'].min() < startblastdate:
                        continue

                    if endblastdate and blast_df['BlastDate'].max() > endblastdate:
                        continue

                    all_blasts.append(blast_df)
        return pd.concat(all_blasts, ignore_index=True) if all_blasts else pd.DataFrame()

    def remove_sms_blast(self, eventcode: str, blastdate: datetime):
        event_folder = os.path.join(self.path_sms_blast, eventcode)
        if not os.path.isdir(event_folder):
            logging.warning(f"No such event folder: {eventcode}")
            return

        for file_name in os.listdir(event_folder):
            if file_name.endswith(".csv") and blastdate.strftime('%Y-%m-%d_%H-%M-%S') in file_name:
                os.remove(os.path.join(event_folder, file_name))
                logging.info(f"Blast file for event code {eventcode} on {blastdate} removed successfully.")
                return

        logging.warning(f"No blast file found for event code {eventcode} on {blastdate}.")
