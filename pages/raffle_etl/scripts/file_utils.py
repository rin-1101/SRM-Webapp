import os
import pandas as pd
from datetime import datetime

class FileUtils:
    def __init__(self, date_utils):
        self.date_utils = date_utils

    def write_draw(self, df):
        path = r'\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\JSON\raffle'
        
        file_name = f"result-{datetime.now().strftime('%y%m%d %H%M%S')}.csv"
        
        if not os.path.exists(path):
            os.makedirs(path)
    
        df.to_csv(os.path.join(path, file_name), index=False)
