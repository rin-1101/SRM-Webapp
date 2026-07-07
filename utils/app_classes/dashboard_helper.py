def tp_earn(uid): 
    if uid =='OM000000001':
        return 999999
    today = datetime.today()
    today = today.strftime('%Y-%m-%d')
    
    sql = f"""

     with main as ( 
    SELECT 
        p.UniversalPlayerID,
        CASE 
                WHEN DATEPART(HOUR, r.TransactionDateTime) >= 6
                    THEN CONVERT(date, r.TransactionDateTime)
                ELSE CONVERT(date, DATEADD(DAY, -1, r.TransactionDateTime)) 
        END AS GameDate, 
        tp.PlayerID, 
        tp.TierPoint 
     FROM [ENGAGEDB].[dbo].[UC_PL_TierPointDetailActual] tp 

     LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Rating] r
     ON tp.RatingID = r.RatingID

     LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p
     ON tp.PlayerID = p.PlayerID

     WHERE TransactionDateTime BETWEEN '2025-05-02 06:00:00' AND '2025-05-09 05:59:59'
     and TransactionDate >= '2025-05-01'

     ) 

     select
        UniversalPlayerID as uid, 
        GameDate, 
        SUM(TierPoint) as Sum_TP
    FROM main m 
    WHERE UniversalPlayerID = '{uid}'
    GROUP BY UniversalPlayerID, GameDate 
    """

    tp_earn = loader.load_data(sql)
    tp_earn = tp_earn[tp_earn['Sum_TP']>0]
    tp_earn['uid'] = tp_earn['uid'].str.strip()
    tp_earn['GameDate'] = pd.to_datetime(tp_earn['GameDate'])
    
    return math.ceil(tp_earn['Sum_TP'].sum())

def format_om(om):
    om_str = str(om).upper()
    if re.fullmatch(r"OM\d{9}", om_str):
        return om_str
    digits = ''.join(filter(str.isdigit, om_str))
    return f"OM{digits.zfill(9)}"

def find_initials(om_number):
    sql = f"""
        SELECT 
            [FirstName] AS fn,
            [LastName] AS ln
        FROM [ENGAGEDB].[dbo].[UC_PL_Player]
        WHERE UniversalPlayerID = '{om_number}'
    """
    result = loader.load_data(sql)  # Assuming loader supports parameterized queries

    # if not result:  # Handle empty results
    #     return "Player Not Found."  
    return f"{result.loc[0].fn[0]}.{result.loc[0].ln[0]}."  # Return initials with periods
def check_player(self,om_number):
        if not isinstance(om_number, str) or om_number.strip() == "":
            return None,None,None,None  # Invalid self.om_number
        
        sql = f"""        
            SELECT
                [UniversalPlayerID],
                [PreferredName],
                [FirstName],
                [LastName],
                case when tr.TierName like'%Okada%VIP%' then 'Okada VIP'
                     when tr.TierName like '%SLOT%' then 'Maharlika'
                    else tr.TierName
                end as tiergroup
            FROM [ENGAGEDB].[dbo].[UC_PL_Player] pl
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Tier] t
                ON pl.PlayerID = t.PlayerID
            left join ENGAGEDB.dbo.UC_X_Tier tr
                on tr.TierID = t.TierID
            WHERE UniversalPlayerID = '{om_number}'
        """
        result = loader.load_data(sql)
        user = result.loc[0]
        
        if not user.empty:  # If the player exists
            tier_group  = user['tiergroup']
            first_name = user['FirstName']
            last_name = user['LastName']
            full_name = user['PreferredName']
            return tier_group,first_name, last_name, full_name
        
        return None,None,None,None  # Player not found
def get_tier(om_number):
        sql = f"""        
            SELECT
                [UniversalPlayerID],
                case when tr.TierName like'%Okada%VIP%' then 'Okada VIP'
                     when tr.TierName like '%SLOT%' then 'Maharlika'
                    else tr.TierName
                end as tiergroup
            FROM [ENGAGEDB].[dbo].[UC_PL_Player] pl
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Tier] t
                ON pl.PlayerID = t.PlayerID
            left join ENGAGEDB.dbo.UC_X_Tier tr
                on tr.TierID = t.TierID
            WHERE UniversalPlayerID = '{om_number}'
        """
        result = loader.load_data(sql)
        user = result.loc[0]
        
        if not user.empty:  # If the player exists
            tier_group  = user['tiergroup']
            return tier_group
        
        return None
