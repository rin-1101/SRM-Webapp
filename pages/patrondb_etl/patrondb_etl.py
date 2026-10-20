import re
from pathlib import Path

import pandas as pd
import yaml
from dash import dash_table, html
from datetime import datetime, timedelta


REPORTS_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMMS_CONFIG_PATH = REPORTS_ROOT / "config" / "comms.yaml"
DEFAULT_EDM_DIR = REPORTS_ROOT / "documents" / "EDM"
DEFAULT_FLOORNAME_PATH = Path(
    r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\Data Science\Jobs\FP Checker\promotions.yaml"
)


PATRONS_COLUMNS = ["uid", "name", "tier", "birthdate"]
OFFERS_COLUMNS = [
    "uid",
    "offer_name",
    "offer_type",
    "reward",
    "validity",
    "offer_details",
    "status",
]
PROMOTIONS_COLUMNS = ["offer_name", "offer_type", "active_period", "status", "summary"]
DISPLAY_LABELS = {
    "contactable": "Marketable",
    "non_contactable_reason": "Non Marketable Reason",
    "FloorName": "Floor Name",
    "promo_name": "Promo Name",
    "PromoName": "Promo Name",
    "promo_group": "Promo Group",
}



def format_om(om):
    om_str = str(om).upper()
    if re.fullmatch(r"OM\d{9}", om_str):
        return om_str
    digits = ''.join(filter(str.isdigit, om_str))
    return f"OM{digits.zfill(9)}"

DF_PATRONS = pd.DataFrame(
    [
        {"uid": "OM1", "name": "Juan Dela Cruz", "tier": "Premium", "birthdate": "March 15, 1980"},
        {"uid": "OM-87654321", "name": "Maria Santos", "tier": "Elite", "birthdate": "July 22, 1975"},
    ],
    columns=PATRONS_COLUMNS,
)

DF_OFFERS = pd.DataFrame(
    [
        {
            "uid": "OM1",
            "offer_name": "Premium Play & Stay",
            "offer_type": "Gaming + Hotel",
            "reward": "PHP 5,000 Free Play",
            "validity": "Jun 1 – Jun 30, 2025",
            "offer_details": "PHP 5,000 Free Play • 1 Complimentary Room Night • Dining Voucher",
            "status": "ACTIVE",
        },
        {
            "uid": "OM1",
            "offer_name": "Weekend Bonus",
            "offer_type": "Bonus",
            "reward": "2x Points Multiplier",
            "validity": "May 10 – May 31, 2025",
            "offer_details": "Double points every Saturday and Sunday",
            "status": "ACTIVE",
        },
        {
            "uid": "OM-87654321",
            "offer_name": "Summer Cashback",
            "offer_type": "Cashback",
            "reward": "15% Cashback",
            "validity": "May 15 – Jun 15, 2025",
            "offer_details": "15% Cashback on Gaming • PHP 2,000 F&B Credit",
            "status": "ACTIVE",
        },
    ],
    columns=OFFERS_COLUMNS,
)

DF_PROMOTIONS = pd.DataFrame(
    [
        {
            "offer_name": "Premium Play & Stay",
            "offer_type": "Gaming + Hotel",
            "active_period": "Jun 1 – Jun 30, 2025",
            "status": "ACTIVE",
            "summary": "PHP 5,000 FP + Room + Dining",
        },
        {
            "offer_name": "Summer Cashback",
            "offer_type": "Cashback",
            "active_period": "May 15 – Jun 15, 2025",
            "status": "ACTIVE",
            "summary": "15% Cashback + PHP 2,000 F&B",
        },
        {
            "offer_name": "Weekend Bonus",
            "offer_type": "Bonus",
            "active_period": "May 10 – May 31, 2025",
            "status": "ACTIVE",
            "summary": "2x Points every Sat & Sun",
        },
    ],
    columns=PROMOTIONS_COLUMNS,
)


def detail_field(label: str, field_id: str) -> html.Div:
    return html.Div(
        className="is-flex is-justify-content-space-between mb-2",
        style={"borderBottom": "1px solid #f0f0f0", "paddingBottom": "4px"},
        children=[
            html.Span(label, className="has-text-grey is-size-7"),
            html.Span(id=field_id, className="has-text-weight-semibold is-size-7"),
        ],
    )


def empty_placeholder() -> html.P:
    return html.P("", className="has-text-grey is-size-7")


def make_table(df: pd.DataFrame, table_id: str, page_size: int = 10) -> dash_table.DataTable | html.P:
    if df is None or df.empty:
        return html.P("No data available.", className="has-text-grey is-size-7")

    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": DISPLAY_LABELS.get(c, c.replace("_", " ").title()), "id": c} for c in df.columns],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto", "fontSize": "0.78rem"},
        style_header={
            "backgroundColor": "#2c3e50",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": "6px 10px",
        },
        style_cell={
            "textAlign": "center",
            "padding": "5px 10px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f5f7fa"},
            {
                "if": {"filter_query": '{status} = "ACTIVE"', "column_id": "status"},
                "color": "#257942",
                "fontWeight": "bold",
            },
        ],
        page_size=page_size,
        sort_action="native",
        filter_action="native",
    )


def make_contactable_table(df: pd.DataFrame, table_id: str, page_size: int = 5) -> dash_table.DataTable | html.P:
    if df is None or df.empty:
        return html.P("No data available.", className="has-text-grey is-size-7")

    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": DISPLAY_LABELS.get(c, c.replace("_", " ").title()), "id": c} for c in df.columns],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto", "fontSize": "0.78rem"},
        style_header={
            "backgroundColor": "#2c3e50",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": "6px 10px",
        },
        style_cell={
            "textAlign": "center",
            "padding": "5px 10px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f5f7fa"},
        ],
        page_size=page_size,
        sort_action="native",
    )


def search_patron_offers(om_input: str | None) -> tuple[pd.Series | None, pd.DataFrame, str | None]:
    if not om_input or not om_input.strip():
        return None, pd.DataFrame(columns=OFFERS_COLUMNS), None

    uid = format_om(om_input).replace("'", "''")

    from okada import SQL

    loader = SQL("hive").get_loader()
    sql = f"""
        SELECT
            universalplayerid AS uid,
            concat(firstname, ' ', lastname) AS name,
            tier AS tier,
            birthdate AS birthdate
        FROM dws.dws_mkt_memberprofile
        WHERE universalplayerid = '{uid}'
        LIMIT 1
    """
    patron_row = loader.load_data(sql)

    if patron_row.empty:
        return None, pd.DataFrame(columns=OFFERS_COLUMNS), uid

    offers = DF_OFFERS[DF_OFFERS["uid"] == uid].drop(columns=["uid"])
    return patron_row.iloc[0], offers, uid


def fetch_active_patron_offers(om_input: str | None, start_date, end_date) -> pd.DataFrame:
    if not om_input or not str(om_input).strip() or not start_date or not end_date:
        return pd.DataFrame(columns=["universalplayerid", "promo_name", "FloorName", "promo_start", "promo_end"])

    uid = format_om(om_input).replace("'", "''")
    start = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end = pd.to_datetime(end_date).strftime("%Y-%m-%d")

    from okada import SQL

    loader = SQL("hive").get_loader()
    sql = f"""
        select distinct
            universalplayerid as universalplayerid,
            promo_name as promo_name,
            promo_start as promo_start,
            promo_end as promo_end
        from dwd.dwd_offer_whitelist_promotional_offers
        where universalplayerid = '{uid}'
            and promo_start <= '{end}'
            and promo_end >= '{start}'
        order by promo_start desc, promo_name
    """
    df = loader.load_data(sql)
    if df.empty:
        return pd.DataFrame(columns=["universalplayerid", "promo_name", "FloorName", "promo_start", "promo_end"])

    return map_floor_names(df)


def fetch_contactable_status(om_number: str | None) -> pd.DataFrame:
    if not om_number or not str(om_number).strip():
        return pd.DataFrame(columns=["contactable", "non_contactable_reason"])

    from okada import SQL

    uid = format_om(om_number).replace("'", "''")
    loader = SQL("engage").get_loader()
    sql = f"""
DECLARE @UniversalPlayerID VARCHAR(20) = '{uid}';

WITH phone AS (
    SELECT
        phone_raw.PlayerID,
        phone_raw.PhoneCountry,
        phone_raw.PhoneAreaCode,
        phone_raw.PhoneNumber,
        phone_raw.BadPhone,
        phone_raw.OptIn,
        phone_raw.Preferred,
        phone_raw.ContactStatusTypeID,
        phone_raw.MobileClean
    FROM (
        SELECT
            p.*,

            CASE
                WHEN LEN(LTRIM(RTRIM(p.PhoneNumber))) = 12
                     AND LEFT(LTRIM(RTRIM(p.PhoneNumber)), 3) = '639'
                THEN LTRIM(RTRIM(p.PhoneNumber)) COLLATE DATABASE_DEFAULT

                WHEN LEN(LTRIM(RTRIM(p.PhoneNumber))) = 11
                     AND LEFT(LTRIM(RTRIM(p.PhoneNumber)), 2) = '09'
                THEN CONCAT(
                    '63',
                    SUBSTRING(
                        LTRIM(RTRIM(p.PhoneNumber)) COLLATE DATABASE_DEFAULT,
                        2,
                        10
                    )
                )

                WHEN LEN(LTRIM(RTRIM(p.PhoneNumber))) = 10
                     AND LEFT(LTRIM(RTRIM(p.PhoneNumber)), 1) = '9'
                THEN CONCAT(
                    '63',
                    LTRIM(RTRIM(p.PhoneNumber)) COLLATE DATABASE_DEFAULT
                )

                ELSE NULL
            END AS MobileClean,

            ROW_NUMBER() OVER (
                PARTITION BY p.PlayerID
                ORDER BY p.CreatedDate DESC
            ) AS rn

        FROM ENGAGEDB.dbo.UC_PL_Phone AS p WITH (NOLOCK)
        WHERE p.[Primary] = 1
          AND p.Active = 1
    ) AS phone_raw
    WHERE phone_raw.rn = 1
),

flag AS (
    SELECT
        flag_data.PlayerID,
        MAX(flag_data.BannedTag) AS BannedTag
    FROM (
        SELECT
            player.PlayerID,

            CASE
                WHEN x_flag.FlagShortName LIKE '%Tm%'
                  OR x_flag.FlagShortName LIKE '%Ex%'
                  OR x_flag.FlagShortName LIKE '%Pe%'
                  OR x_flag.FlagShortName LIKE '%Re%'
                  OR x_flag.FlagShortName LIKE '%Fz%'
                THEN 1
                ELSE 0
            END AS BannedTag

        FROM ENGAGEDB.dbo.UC_PL_Player AS player WITH (NOLOCK)

        INNER JOIN ENGAGEDB.flg.UC_PL_Flag AS pl_flag WITH (NOLOCK)
            ON player.PlayerID = pl_flag.PlayerID

        INNER JOIN ENGAGEDB.flg.UC_X_Flag AS x_flag WITH (NOLOCK)
            ON pl_flag.FlagTypeID = x_flag.FlagID

        WHERE pl_flag.Active = 1

        UNION ALL

        SELECT
            player.PlayerID,
            1 AS BannedTag
        FROM ENGAGEDB.dbo.UC_PL_Player AS player WITH (NOLOCK)
        WHERE ENGAGEDB.dbo.fnIsPlayerDAP(player.UniversalPlayerID) = 1
		and player.universalplayerid = @UniversalPlayerID
    ) AS flag_data
    WHERE flag_data.BannedTag = 1
    GROUP BY flag_data.PlayerID
),

email AS (
    SELECT
        email_raw.PlayerID,
        email_raw.EmailAddress,
        email_raw.EmailClean
    FROM (
        SELECT
            e.*,

            CASE
                WHEN UPPER(e.EmailAddress) LIKE '%NOEMAI%'
                  OR UPPER(e.EmailAddress) LIKE '%NOMAIL%'
                THEN NULL
                ELSE LTRIM(RTRIM(e.EmailAddress))
            END AS EmailClean,

            ROW_NUMBER() OVER (
                PARTITION BY e.PlayerID
                ORDER BY e.CreatedDate DESC
            ) AS rn

        FROM ENGAGEDB.dbo.UC_PL_Email AS e WITH (NOLOCK)
        WHERE e.[Primary] = 1
          AND e.Active = 1
    ) AS email_raw
    WHERE email_raw.rn = 1
),

dnd AS (
    SELECT
        pf.PlayerID,
        1 AS IsDND
    FROM ENGAGEDB.dbo.UC_X_FlagType AS ft WITH (NOLOCK)

    INNER JOIN ENGAGEDB.dbo.UC_PL_PlayerFlag AS pf WITH (NOLOCK)
        ON ft.FlagTypeID = pf.FlagTypeID
       AND pf.Active = 1

    WHERE ft.FlagTypeName = 'Do Not Contact'
    GROUP BY pf.PlayerID
),

gcb_raw AS (
    SELECT
        player.PlayerID,
        player.UniversalPlayerID AS UID,
        player.CreatedDate,
        player.FirstName,
        nationality.Name AS Nationality,

        phone.PhoneCountry AS CountryCode,
        phone.PhoneAreaCode AS AreaCode,
        phone.PhoneNumber AS MobileSys,

        CASE
            WHEN player.UniversalPlayerID = 'OM000144849'
            THEN NULL
            ELSE phone.MobileClean
        END AS MobileClean,

        email.EmailAddress AS EmailSys,
        email.EmailClean,
        ISNULL(phone.BadPhone, 0) AS PhoneBad,
        ISNULL(flag.BannedTag, 0) AS BannedTag,

        CASE
            WHEN ISNULL(dnd.IsDND, 0) = 1 THEN 0
            ELSE ISNULL(phone.OptIn, 0)
        END AS OptIn,

        CASE
            WHEN ISNULL(phone.BadPhone, 0) = 1 THEN 0
            WHEN phone.PhoneNumber IS NULL
                 AND email.EmailClean IS NULL THEN 0
            WHEN ISNULL(flag.BannedTag, 0) = 1 THEN 0
            WHEN ISNULL(dnd.IsDND, 0) = 1 THEN 0
            WHEN ISNULL(phone.OptIn, 0) = 0 THEN 0
            ELSE 1
        END AS Contactable

    FROM ENGAGEDB.dbo.UC_PL_Player AS player WITH (NOLOCK)

    LEFT JOIN phone
        ON player.PlayerID = phone.PlayerID

    LEFT JOIN flag
        ON player.PlayerID = flag.PlayerID

    LEFT JOIN email
        ON player.PlayerID = email.PlayerID

    LEFT JOIN dnd
        ON player.PlayerID = dnd.PlayerID

    LEFT JOIN ENGAGEDB.dbo.UC_X_Nationality AS nationality WITH (NOLOCK)
        ON player.Nationality = nationality.NationalityID
),

gcb_with_duplicates AS (
    SELECT
        gcb_raw.*,

        CASE
            WHEN MobileClean IS NOT NULL
             AND Contactable = 1
             AND COUNT(
                    CASE
                        WHEN Contactable = 1 THEN 1
                    END
                 ) OVER (PARTITION BY MobileClean) > 1
            THEN 1
            ELSE 0
        END AS DuplicateMobile

    FROM gcb_raw
)

SELECT
    CASE
        WHEN g.DuplicateMobile = 1 THEN 0
        ELSE g.Contactable
    END AS Contactable,

    NULLIF(
        STUFF(
            CONCAT(
                CASE
                    WHEN g.DuplicateMobile = 1
                    THEN ', Duplicate Mobile'
                    ELSE ''
                END,

                CASE
                    WHEN g.PhoneBad = 1
                    THEN ', Bad Phone'
                    ELSE ''
                END,

                CASE
                    WHEN g.MobileSys IS NULL
                     AND g.EmailClean IS NULL
                    THEN ', No Phone and Email'
                    ELSE ''
                END,

                CASE
                    WHEN g.BannedTag = 1
                    THEN ', Banned Tag'
                    ELSE ''
                END,

                CASE
                    WHEN g.OptIn = 0
                    THEN ', DND / Opt-out'
                    ELSE ''
                END
            ),
            1,
            2,
            ''
        ),
        ''
    ) AS NonContactableReason

FROM gcb_with_duplicates AS g
WHERE g.UID = @UniversalPlayerID;
    """
    df = loader.load_data(sql)
    if df.empty:
        return pd.DataFrame(columns=["contactable", "non_contactable_reason"])
    return df


def filter_promotions(query: str | None, end_date=None) -> pd.DataFrame:
    from okada import SQL

    loader = SQL("hive").get_loader()
    conditions = []
    if query and query.strip():
        search_terms = [str(query).strip()]
        try:
            search_terms.extend(promo_group_search_aliases(query))
        except Exception:
            pass

        like_conditions = []
        seen_terms = set()
        for term in search_terms:
            promo = str(term or "").strip().replace("'", "''")
            if not promo:
                continue
            promo_key = promo.upper()
            if promo_key in seen_terms:
                continue
            seen_terms.add(promo_key)
            like_conditions.append(f"UPPER(promo_name) LIKE UPPER('%{promo}%')")

        if like_conditions:
            conditions.append(f"({' OR '.join(like_conditions)})")
    if end_date:
        end = pd.to_datetime(end_date).strftime("%Y-%m-%d")
        conditions.append(f"promo_end >= '{end}'")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT DISTINCT
            promo_name as PromoName,
            promo_start AS StartDate,
            promo_end AS EndDate
        FROM dwd.dwd_offer_whitelist_promotional_offers
        {where_clause}
        ORDER BY promo_start DESC, promo_name
    """
    df = loader.load_data(sql)

    if df.empty:
        return pd.DataFrame(columns=["PromoName", "FloorName", "StartDate", "EndDate"])

    return map_floor_names(df)


def load_placeholder_map(path: str | Path = DEFAULT_COMMS_CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def set_parameters(sms_message: str, data: dict, placeholder_map: dict) -> str:
    final_message = sms_message or ""
    for placeholder, field in placeholder_map.items():
        final_message = final_message.replace(placeholder, str(data.get(field, "")))
    return final_message


def get_edm_content(event_id, first_name: str = "", uid: str = "", edm_dir: str | Path = DEFAULT_EDM_DIR):
    html_path = Path(edm_dir) / f"{event_id}.html"
    try:
        html_content = html_path.read_text(encoding="utf-8")
        if first_name:
            html_content = html_content.replace("[first_name]", first_name)
        if uid:
            html_content = html_content.replace("[cc_memberid]", uid)

        return html.Iframe(srcDoc=html_content, style={"width": "100%", "height": "100%"})
    except FileNotFoundError:
        return html.Div("EDM content not available")


def normalize_promotion_name(value) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def clean_floorname_pattern(value) -> str:
    pattern = str(value or "").strip()
    if pattern.startswith("^"):
        pattern = pattern[1:]
    if pattern.endswith(".*"):
        pattern = pattern[:-2]
    if pattern.endswith("*"):
        pattern = pattern[:-1]
    return pattern


def promo_group_search_aliases(query: str | None, path: str | Path = DEFAULT_FLOORNAME_PATH) -> list[str]:
    query_value = str(query or "").strip()
    if not query_value:
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    promotions = data.get("promotions", []) if isinstance(data, dict) else data
    if not isinstance(promotions, list):
        return []

    query_key = query_value.upper()
    normalized_query_key = normalize_promotion_name(query_value)
    aliases = []
    for row in promotions:
        if not isinstance(row, dict):
            continue

        group_values = [row.get("promo_group"), row.get("PromoGroup"), row.get("promotion_group")]
        group_matches = False
        for group_value in group_values:
            group_key = str(group_value or "").strip().upper()
            normalized_group_key = normalize_promotion_name(group_value)
            name_matches = query_key and group_key and (query_key in group_key or group_key in query_key)
            normalized_matches = normalized_query_key and normalized_group_key and (
                normalized_query_key in normalized_group_key
                or normalized_group_key in normalized_query_key
            )
            if name_matches or normalized_matches:
                group_matches = True
                break

        if not group_matches:
            continue

        pattern_alias = clean_floorname_pattern(row.get("pattern"))
        row_aliases = [
            row.get("promo_name"),
            row.get("PromotionName"),
            row.get("promotion_name"),
            pattern_alias,
        ]
        if pattern_alias.endswith("_"):
            row_aliases.append(pattern_alias[:-1])

        for alias in row_aliases:
            alias = str(alias or "").strip()
            if alias and alias not in aliases:
                aliases.append(alias)

    return aliases


def load_floorname_map(path: str | Path = DEFAULT_FLOORNAME_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    def add_floor_aliases(floor_map: dict, row: dict) -> None:
        floor_name = row.get("floorname") or row.get("FloorName") or ""
        aliases = [
            row.get("promo_name"),
            row.get("PromotionName"),
            row.get("promotion_name"),
            row.get("promo_group"),
            row.get("PromoGroup"),
            row.get("promotion_group"),
            clean_floorname_pattern(row.get("pattern")),
            floor_name,
        ]

        pattern_alias = clean_floorname_pattern(row.get("pattern"))
        if pattern_alias.endswith("_"):
            aliases.append(pattern_alias[:-1])

        for alias in aliases:
            alias = str(alias or "").strip()
            if alias:
                floor_map[alias.upper()] = floor_name

    if isinstance(data, dict) and isinstance(data.get("promotions"), list):
        floor_map = {}
        for row in data["promotions"]:
            if isinstance(row, dict):
                add_floor_aliases(floor_map, row)
        return floor_map

    if isinstance(data, dict):
        return {str(k).strip().upper(): v for k, v in data.items() if str(k).strip()}

    if isinstance(data, list):
        floor_map = {}
        for row in data:
            if isinstance(row, dict):
                add_floor_aliases(floor_map, row)
        return floor_map

    return {}


def load_loading_floorname_rules(path: str | Path = DEFAULT_FLOORNAME_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    promotions = data.get("promotions", []) if isinstance(data, dict) else data
    if not isinstance(promotions, list):
        return []

    rules = []
    for row in promotions:
        if not isinstance(row, dict):
            continue

        raw_pattern = str(row.get("pattern") or "").strip()
        pattern = raw_pattern[1:] if raw_pattern.startswith("^") else raw_pattern
        display_pattern = pattern if pattern.endswith("*") else f"{pattern}*"
        regex_pattern = pattern[:-1] + ".*" if pattern.endswith("*") else f"{pattern}.*"
        floor_name = row.get("floorname") or row.get("FloorName") or ""

        if pattern:
            rules.append({"pattern": display_pattern, "regex_pattern": regex_pattern, "floor_name": floor_name})

    return rules


def map_loading_floor_names(df: pd.DataFrame, path: str | Path = DEFAULT_FLOORNAME_PATH) -> pd.DataFrame:
    if df is None or df.empty or "Trans Employee" not in df.columns:
        return df

    mapped = df.copy()
    try:
        rules = load_loading_floorname_rules(path)
    except Exception:
        rules = []

    def find_loading_match(trans_employee: str) -> pd.Series:
        value = str(trans_employee or "")
        for rule in rules:
            pattern = rule["regex_pattern"]
            try:
                matched = re.search(pattern, value, flags=re.IGNORECASE)
            except re.error:
                matched = pattern.lower() in value.lower()

            if matched:
                return rule["floor_name"]

        return ""

    mapped["FloorName"] = mapped["Trans Employee"].apply(find_loading_match)

    columns = list(mapped.columns)
    columns.remove("FloorName")
    trans_employee_index = columns.index("Trans Employee")
    columns.insert(trans_employee_index + 1, "FloorName")
    return mapped[columns]

def map_floor_names(df: pd.DataFrame, path: str | Path = DEFAULT_FLOORNAME_PATH) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    promotion_column = next((column for column in ("PromotionName", "PromoName", "promo_name") if column in df.columns), None)
    fallback_column = next((column for column in ("PromoGroup", "promo_group", "promotion_group") if column in df.columns), None)
    if promotion_column is None and fallback_column is None:
        return df

    try:
        floor_map = load_floorname_map(path)
        floor_rules = load_loading_floorname_rules(path)
    except Exception:
        df = df.copy()
        df["FloorName"] = ""
        return df

    mapped = df.copy()

    def find_floor_name(promotion_name: str) -> str:
        promotion_value = str(promotion_name or "")
        promotion_key = promotion_value.strip().upper()
        normalized_promotion_key = normalize_promotion_name(promotion_name)
        for map_promotion_name, floor_name in floor_map.items():
            normalized_map_key = normalize_promotion_name(map_promotion_name)
            name_matches = promotion_key and (
                map_promotion_name in promotion_key
                or promotion_key in map_promotion_name
            )
            normalized_matches = normalized_promotion_key and normalized_map_key and (
                normalized_map_key in normalized_promotion_key
                or normalized_promotion_key in normalized_map_key
            )
            if map_promotion_name and (name_matches or normalized_matches):
                return floor_name or ""

        for rule in floor_rules:
            pattern = rule["regex_pattern"]
            try:
                matched = re.search(pattern, promotion_value, flags=re.IGNORECASE)
            except re.error:
                matched = pattern.lower() in promotion_value.lower()

            if matched:
                return rule["floor_name"] or ""

        return ""

    if promotion_column is None:
        mapped["FloorName"] = mapped[fallback_column].apply(find_floor_name)
    elif fallback_column is None:
        mapped["FloorName"] = mapped[promotion_column].apply(find_floor_name)
    else:
        mapped["FloorName"] = mapped.apply(
            lambda row: find_floor_name(row.get(promotion_column)) or find_floor_name(row.get(fallback_column)),
            axis=1,
        )

    columns = list(mapped.columns)
    columns.remove("FloorName")
    insert_after_column = promotion_column or fallback_column
    promotion_index = columns.index(insert_after_column)
    columns.insert(promotion_index + 1, "FloorName")
    return mapped[columns]


def fetch_sms_records(om_number, promotion, start_date, end_date):
    if not om_number:
        return [], []

    om_number = format_om(om_number)
    start_date = pd.to_datetime(start_date) if start_date else None
    end_date = pd.to_datetime(end_date) if end_date else None

    from sms_etl.sms import SMS

    sms_processor = SMS()
    df = sms_processor.read_sms_blast(
        universalplayerid=om_number,
        eventname=promotion,
        startblastdate=start_date,
        endblastdate=end_date,
    )
    if df.empty:
        return [], []

    df = map_floor_names(df)
    records = df.to_dict("records")
    return records, records


def fetch_loadings_records(om_number, start_date, end_date) -> pd.DataFrame:
    if not om_number:
        return pd.DataFrame()

    start_date = pd.to_datetime(start_date) if start_date else None
    end_date = pd.to_datetime(end_date) if end_date else None
    if start_date is None or end_date is None:
        return pd.DataFrame()

    from okada import SQL

    uid = format_om(om_number).replace("'", "''")
    start = start_date.strftime("%Y-%m-%d")
    end = (end_date+timedelta(days=1)).strftime("%Y-%m-%d")

    loader = SQL("engage").get_loader()
    sql = f"""
        select adjustmentdate,
            adjustmentamount,
            adjustmentaction,
            transemployee
        from ENGAGEDB.dbo.UC_PL_BucketAdjustment ba
        left join ENGAGEDB.dbo.uc_pl_player p
            on p.PlayerID = ba.PlayerID
        where AdjustmentDate BETWEEN '{start}' and '{end}'
            and ba.createdby = 'HALoWebService'
            and universalplayerid = '{uid}'
        order by adjustmentdate desc
    """
    df = loader.load_data(sql)
    if not df.empty:
        df.columns = ["Adjustment Date", "Adjustment Amount", "Adjustment Action", "Trans Employee"]
        df = map_loading_floor_names(df)
    return df
