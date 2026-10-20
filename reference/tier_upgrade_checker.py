import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
import os
import sys
ROOT = "L:\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService

loader = SQL("ENGAGE").get_loader()
hloader = SQL("hive").get_loader()

import warnings
warnings.filterwarnings("ignore")
pd.options.display.float_format = '{:,.0f}'.format


uid = input("Enter your UID: ").strip()

print("Your UID is:", uid)

query = f"""
SELECT [UniversalPlayerID],
		t.[PlayerID] ,
		[FromTierID] ,
		[ToTierID], 
		[TierReasonId], 
		t.[UpdatedDate], 
		t.[CreatedDate], 
		t.[CreatedBy]
  FROM [ENGAGEDB].[dbo].[UC_PL_TierHist] t
  LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p
  ON p.PlayerID = t.PlayerID 	
  WHERE UniversalPlayerID = '{uid}'
  AND t.[CreatedDate] >= '2020-11-01'
  ORDER BY UpdatedDate DESC
""" 

hist = loader.load_data(query)
print(len(hist))
hist


query = f"""
WITH subq AS (
    SELECT ENGAGEDB.AWA.UC_PL_PrizeRedemption.PlayerID
         , ENGAGEDB.AWA.UC_X_EventDefinition.Name as EventName
         , ENGAGEDB.AWA.UC_X_EventDefinition.Description as EventDescription
         , ENGAGEDB.AWA.UC_X_PrizeInventory.Name as PrizeName
         , ENGAGEDB.AWA.UC_X_PrizeInventory.Description as PrizeDescription               
         , ENGAGEDB.AWA.UC_X_PrizeInventory.Value
         , ENGAGEDB.AWA.UC_PL_PrizeRedemption.RedemptionDate
         , ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail.[PrizeRedemptionID] as VoucherNumber
         , cast(convert(varchar(10),iif(datepart(hour,ENGAGEDB.AWA.UC_PL_PrizeRedemption.RedemptionDate)<6,dateadd(day,-1,ENGAGEDB.AWA.UC_PL_PrizeRedemption.RedemptionDate),ENGAGEDB.AWA.UC_PL_PrizeRedemption.RedemptionDate),101) as date)  as RedemptionGamingDate
         , UPPER(ENGAGEDB.AWA.UC_PL_PrizeRedemption.RedeemedBy) AS RedeemedBy
         , ENGAGEDB.awa.UC_PL_PrizeRedemptionDetail.Returned
         , ENGAGEDB.awa.UC_PL_PrizeRedemptionDetail.ReturnedDate
         , ENGAGEDB.awa.UC_PL_PrizeRedemptionDetail.ReturnedBy
    FROM  ENGAGEDB.AWA.UC_PL_PrizeRedemption LEFT OUTER JOIN ENGAGEDB.AWA.UC_X_EventDefinition ON ENGAGEDB.AWA.UC_PL_PrizeRedemption.EventDefinitionID = ENGAGEDB.AWA.UC_X_EventDefinition.ID LEFT OUTER JOIN
          ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail LEFT OUTER JOIN ENGAGEDB.AWA.UC_X_PrizeInventory ON ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail.PrizeID = ENGAGEDB.AWA.UC_X_PrizeInventory.ID ON 
          ENGAGEDB.AWA.UC_PL_PrizeRedemption.ID = ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail.PrizeRedemptionID LEFT OUTER JOIN
          ENGAGEDB.dbo.UC_X_Bucket AS UC_X_Bucket_1 ON ENGAGEDB.AWA.UC_X_PrizeInventory.RequiredBucketTypeID = UC_X_Bucket_1.BucketID
    )
    SELECT UniversalPlayerID, EventName, RedemptionGamingdate, Value
    FROM subq
	left join ENGAGEDB.dbo.UC_PL_Player pl
	on subq.PlayerID = pl. PlayerID
    WHERE EventName like '%upgrade%gift%'
	AND UniversalPlayerID = '{uid}'
    AND Returned is null
"""

prize_red = loader.load_data(query)
print(len(prize_red))
prize_red.head(2)

query = f"""SELECT 
    universalplayerid UniversalPlayerID, 
    gamingdate gamingdate, 
    tierpoints tierpoints
FROM dwd.dwd_mkt_pointbalance
where universalplayerid = '{uid}'
and gamingdate >= '2024-01-01' 
order by gamingdate desc
"""

tp_bal = hloader.load_data(query)
print(len(tp_bal))
tp_bal.head()

res = tp_bal[tp_bal['tierpoints']>=14500]

res 