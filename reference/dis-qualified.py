"""Wicked Wheels report query, shared by the standalone script and Dash page."""

from datetime import datetime, timedelta, timezone
import sys


ROOT = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications"
MANILA = timezone(timedelta(hours=8))


def report_window(now=None):
    """Use today's 06:00 inclusive to 10:00 exclusive in Manila time."""
    today = now if now is not None else datetime.now(MANILA)
    if today.tzinfo is not None:
        today = today.astimezone(MANILA)
    start = today.replace(hour=6, minute=0, second=0, microsecond=0)
    end = today.replace(hour=22, minute=0, second=0, microsecond=0)
    return start, end


def build_query(now=None):
    start, end = report_window(now)
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end.strftime("%Y-%m-%d %H:%M:%S")
    return f"""
WITH main AS (
    -- TABLE GAMES
    SELECT
        r.PlayerID,
        tg.RatingID,
        tg.StartDateTime AS StartDate,
        tg.EndDateTime AS EndDate,
        CASE
            WHEN r.TransStation LIKE '01%' THEN 'H'
            WHEN r.TransStation LIKE '29%' THEN 'M'
            WHEN r.TransStation LIKE '30%' THEN 'N'
            WHEN r.TransStation LIKE '80%' THEN 'X'
            WHEN r.TransStation LIKE '81%' THEN 'X'
            ELSE ''
        END AS Zone,
        td.TierPoint AS TP,
        r.TransactionDateTime AS TransactionDate
    FROM ENGAGEDB.dbo.UC_PL_RatingTableGame tg
    LEFT JOIN ENGAGEDB.dbo.UC_PL_Rating r
        ON r.RatingID = tg.RatingID
    LEFT JOIN ENGAGEDB.dbo.UC_PL_TierPointDetail td
        ON td.RatingID = r.RatingID
    WHERE tg.EndDateTime >= '{start_str}'
      AND tg.EndDateTime < '{end_str}'
      AND tg.TableTheoWin > 0
      AND (
            r.TransStation LIKE '01%'
         OR r.TransStation LIKE '29%'
         OR r.TransStation LIKE '30%'
         OR r.TransStation LIKE '80%'
         OR r.TransStation LIKE '81%'
      )
      AND tg.TableRatingType = 'MCASH'
      AND td.BucketID = 10024

    UNION ALL

    -- SLOT GAMES
    SELECT
        r.PlayerID,
        eg.RatingID,
        eg.StartDateTime AS StartDate,
        eg.EndDateTime AS EndDate,
        eg.Zone AS Zone,
        td.TierPoint AS TP,
        r.TransactionDateTime AS TransactionDate
    FROM ENGAGEDB.dbo.UC_PL_RatingSlotGame eg
    LEFT JOIN ENGAGEDB.dbo.UC_PL_Rating r
        ON r.RatingID = eg.RatingID
    LEFT JOIN ENGAGEDB.dbo.UC_PL_TierPointDetail td
        ON td.RatingID = r.RatingID
    WHERE eg.EndDateTime >= '{start_str}'
      AND eg.EndDateTime < '{end_str}'
      AND eg.SlotTheoWin > 0
      AND (
            eg.Zone LIKE 'H%'
         OR eg.Zone LIKE 'M%'
         OR eg.Zone LIKE 'N%'
         OR eg.Zone LIKE 'X%'
      )
      AND td.BucketID = 10024
),

coding AS (
    SELECT
        host.FirstName + ' ' + host.LastName AS Coding,
        player.UniversalPlayerID
    FROM ENGAGEDB.dbo.UC_PL_PlayerHost player_host
    LEFT JOIN ENGAGEDB.dbo.UC_PL_Player player
        ON player_host.PlayerID = player.PlayerID
    LEFT JOIN ENGAGEDB.dbo.UC_PL_PlayerHostDetail host_detail
        ON player_host.ID = host_detail.PlayerHostID
    LEFT JOIN ENGAGEDB.dbo.UC_H_Host host
        ON host_detail.HostID = host.ID
    WHERE player_host.Active = 1
      AND host_detail.Active = 1
)

SELECT
    p.UniversalPlayerID,
    tn.TierName,
    c.Coding,
	CONCAT(
        LEFT(p.FirstName, 1),
        '. ',
        LEFT(p.LastName, 1),
        '.'
    ) AS Initials,
    SUM(m.TP) AS TP
FROM main m
LEFT JOIN ENGAGEDB.dbo.UC_PL_Player p
    ON p.PlayerID = m.PlayerID
LEFT JOIN ENGAGEDB.dbo.UC_PL_Tier t
    ON t.PlayerID = p.PlayerID
LEFT JOIN ENGAGEDB.dbo.UC_X_Tier tn
    ON tn.TierID = t.TierID
LEFT JOIN coding c
    ON p.UniversalPlayerID = c.UniversalPlayerID
WHERE tn.TierName IN (
    'SLOT VVIP',
    'Supreme',
    'Maharlika',
    'Okada Club',
    'Premium'
)
GROUP BY
    p.UniversalPlayerID,
    tn.TierName,
    c.Coding,
    p.FirstName,
    p.LastName
HAVING SUM(m.TP) >= 1;
"""


def generate_report(now=None, loader=None):
    """Run the Wicked Wheels rating query only when explicitly requested."""
    if loader is None:
        okada_path = rf"{ROOT}\okada"
        if okada_path not in sys.path:
            sys.path.append(okada_path)
        from okada import SQL

        loader = SQL("engage").get_loader()
    return loader.load_data(build_query(now))


if __name__ == "__main__":
    data = generate_report()
    print(data)
