"""On-demand duplicate lookup using reference/Duplicate.py's full-scan rules."""

import logging
import re
import sys

import dash
import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html
from dash.exceptions import PreventUpdate
from flask_login import current_user

from utils.login_handler import has_access, require_login, restricted_page
from utils.paths import DUPLICATE_CHECKER

ROOT = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\okada"
sys.path.append(ROOT)
from okada import SQL

logger = logging.getLogger("duplicate-checker")
COLUMNS = [
    "PlayerID", "UniversalPlayerID", "FirstName", "MiddleName", "LastName",
    "Gender", "BirthDate", "CreatedDate", "CreatedBy", "Flag",
]

dash.register_page(__name__, path=DUPLICATE_CHECKER, name="Duplicate Checker")
require_login(__name__, access_level=restricted_page[DUPLICATE_CHECKER]["access_level"])


def normalize_uid(value):
    uid = str(value or "").strip().upper()
    if not uid:
        raise ValueError("Please enter a UniversalPlayerID.")
    if not re.fullmatch(r"[A-Z0-9]+", uid):
        raise ValueError("UniversalPlayerID may contain letters and numbers only.")
    return uid


def normalize_search(uid=None, first_name=None, last_name=None):
    filters = {}
    if str(uid or "").strip():
        filters["UniversalPlayerID"] = normalize_uid(uid)
    for column, value in (("FirstName", first_name), ("LastName", last_name)):
        value = str(value or "").strip().upper()
        if value:
            filters[column] = value
    if not filters:
        raise ValueError("Enter at least one: UniversalPlayerID, Firstname, or Lastname.")
    return filters


def build_query(uid=None, first_name=None, last_name=None):
    filters = normalize_search(uid, first_name, last_name)
    # Column names come from the fixed allowlist above; quote SQL string literals.
    conditions = []
    for column, value in filters.items():
        escaped = value.replace("'", "''")
        if column == "UniversalPlayerID":
            conditions.append(f"UPPER(LTRIM(RTRIM({column}))) = N'{escaped}'")
        else:
            # Treat SQL LIKE metacharacters as literal name characters.
            escaped = (escaped.replace("~", "~~").replace("%", "~%")
                       .replace("_", "~_").replace("[", "~["))
            conditions.append(
                f"UPPER(LTRIM(RTRIM({column}))) LIKE N'%{escaped}%' ESCAPE N'~'"
            )
    predicate = " AND ".join(conditions)
    # All connected matches share first name and birth date, so only this
    # subset is needed to reproduce the reference's full-scan grouping.
    return f"""
WITH target AS (
    SELECT PlayerID, FirstName, BirthDate
    FROM ENGAGEDB.dbo.UC_PL_Player
    WHERE {predicate}
), candidates AS (
    SELECT p.*
    FROM ENGAGEDB.dbo.UC_PL_Player p
    WHERE EXISTS (SELECT 1 FROM target t WHERE t.PlayerID = p.PlayerID)
       OR EXISTS (
           SELECT 1 FROM target t
           WHERE UPPER(LTRIM(RTRIM(p.FirstName))) = UPPER(LTRIM(RTRIM(t.FirstName)))
             AND p.BirthDate = t.BirthDate
       )
), gender AS (
    SELECT i.PlayerID, MAX(i.Gender) AS Gender
    FROM ENGAGEDB.dbo.UC_PL_Identification i
    INNER JOIN candidates c ON c.PlayerID = i.PlayerID
    GROUP BY i.PlayerID
), flag AS (
    SELECT pf.PlayerID,
           STRING_AGG(NULLIF(LTRIM(RTRIM(xf.FlagShortName)), ''), ' | ') AS Flag
    FROM ENGAGEDB.FLG.UC_PL_Flag pf
    INNER JOIN ENGAGEDB.FLG.UC_X_Flag xf ON pf.FlagTypeID = xf.FlagID
    INNER JOIN candidates c ON c.PlayerID = pf.PlayerID
    WHERE pf.Active = 1
    GROUP BY pf.PlayerID
)
SELECT p.PlayerID,
       UPPER(LTRIM(RTRIM(p.UniversalPlayerID))) AS UniversalPlayerID,
       UPPER(LTRIM(RTRIM(p.FirstName))) AS FirstName,
       UPPER(LTRIM(RTRIM(p.MiddleName))) AS MiddleName,
       UPPER(LTRIM(RTRIM(p.LastName))) AS LastName,
       g.Gender, p.BirthDate, p.CreatedDate, p.CreatedBy, f.Flag,
       CASE WHEN EXISTS (SELECT 1 FROM target t WHERE t.PlayerID = p.PlayerID)
            THEN 1 ELSE 0 END AS IsSearchMatch
FROM candidates p
LEFT JOIN gender g ON p.PlayerID = g.PlayerID
LEFT JOIN flag f ON p.PlayerID = f.PlayerID
""".strip()


def find_duplicates(dataframe, uid=None):
    """Return the target, other linked UIDs, and a user-facing status."""
    if uid is not None:
        uid = normalize_uid(uid)
    data = dataframe.reindex(columns=COLUMNS).copy()
    for column in ("FirstName", "MiddleName", "LastName"):
        data[column] = data[column].astype("string").str.strip().str.title()
    data["UniversalPlayerID"] = data["UniversalPlayerID"].astype("string").str.strip().str.upper()
    data["Flag"] = data["Flag"].fillna("")
    # The SQL marker preserves the database's name/collation matching behavior.
    matched = (data["UniversalPlayerID"].eq(uid) if uid is not None
               else dataframe.reindex(data.index)["IsSearchMatch"].eq(1)
               if "IsSearchMatch" in dataframe else pd.Series(False, index=data.index))
    target = data.loc[matched].copy()
    target_uids = set(target["UniversalPlayerID"].dropna())
    empty = data.iloc[:0].copy()
    if target.empty:
        return target, empty, "No accounts found matching the supplied search fields."

    eligible = data["BirthDate"].notna() & ~data["Flag"].str.upper().str.contains("ZZ|TA|RE", regex=True)
    data = data.loc[eligible].reset_index(drop=True)
    target_indexes = data.index[data["UniversalPlayerID"].isin(target_uids)].tolist()
    if not target_indexes:
        return target, empty, "Matched accounts are excluded from duplicate checking: missing birth date or an active flag containing ZZ, TA, or RE."

    parents = list(range(len(data)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def join(left, right):
        parents[root(right)] = root(left)

    for _, group in data.groupby(["FirstName", "BirthDate"], sort=False):
        surnames = {}
        for index, row in group.iterrows():
            surname = row["LastName"]
            if pd.notna(surname):
                if surname in surnames:
                    join(index, surnames[surname])
                else:
                    surnames[surname] = index
        for index, row in group.iterrows():
            middle = row["MiddleName"]
            if pd.notna(row["Gender"]) and row["Gender"] == "F" and pd.notna(middle) and middle and middle in surnames:
                join(index, surnames[middle])

    grouped = {}
    for index in data.index:
        grouped.setdefault(root(index), []).append(index)
    duplicate_results = []
    checked_uids = set()
    for index in target_indexes:
        searched_uid = data.at[index, "UniversalPlayerID"]
        if searched_uid in checked_uids:
            continue
        checked_uids.add(searched_uid)
        linked = data.loc[grouped[root(index)]]
        linked = linked.loc[linked["UniversalPlayerID"].ne(searched_uid)].copy()
        if not linked.empty:
            linked.insert(0, "SearchedUniversalPlayerID", searched_uid)
            duplicate_results.append(linked)
    duplicates = (pd.concat(duplicate_results, ignore_index=True).drop_duplicates()
                  if duplicate_results else pd.DataFrame(columns=["SearchedUniversalPlayerID"] + COLUMNS))
    duplicates = duplicates.sort_values("CreatedDate", na_position="last")
    count = duplicates["UniversalPlayerID"].nunique()
    excluded = len(target_uids - checked_uids)
    message = f"Found {len(target_uids):,} matching account(s). Checked {len(checked_uids):,}; excluded {excluded:,} for missing birth date or ZZ/TA/RE flags. "
    message += f"Found {count:,} potential duplicate account(s)." if count else "No duplicates found under the reference matching rules."
    return target, duplicates, message


def make_table(dataframe):
    display = dataframe.copy()
    for column in ("BirthDate", "CreatedDate"):
        display[column] = display[column].map(lambda value: str(value) if pd.notna(value) else "")
    display = display.astype(object).where(pd.notna(display), None)
    return dash_table.DataTable(
        data=display.to_dict("records"),
        columns=[{"name": column, "id": column} for column in display.columns],
        page_size=15, sort_action="native", filter_action="native",
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#2c3e50", "color": "white", "fontWeight": "bold"},
        style_cell={"padding": "8px", "textAlign": "left", "whiteSpace": "normal", "height": "auto"},
    )


def layout():
    if not current_user.is_authenticated or not has_access(current_user, DUPLICATE_CHECKER):
        return html.Div("No Access!")
    return html.Div(className="container", children=[
        html.H1("Duplicate Checker", className="title has-text-centered"),
        html.Div(className="box", children=[
            html.Label("UniversalPlayerID", htmlFor="duplicate-uid", className="label"),
            dcc.Input(id="duplicate-uid", type="text", placeholder="Enter UniversalPlayerID", className="input"),
            html.Label("Firstname", htmlFor="duplicate-firstname", className="label mt-3"),
            dcc.Input(id="duplicate-firstname", type="text", placeholder="Enter first name", className="input"),
            html.Label("Lastname", htmlFor="duplicate-lastname", className="label mt-3"),
            dcc.Input(id="duplicate-lastname", type="text", placeholder="Enter last name", className="input"),
            html.P("Enter at least one field. Names use case-insensitive contains matching. UniversalPlayerID uses an exact match. When multiple fields are entered, all must match.", className="help"),
            html.Button("Check duplicates", id="duplicate-check", n_clicks=0, className="button is-info mt-3"),
            html.P("Matches first name and birth date, then surname or female middle-name/surname links, including connected accounts. Active flags containing ZZ, TA, or RE are excluded.", className="help"),
        ]),
        dcc.Loading(html.Div(id="duplicate-result")),
    ])


@callback(
    Output("duplicate-result", "children"),
    Input("duplicate-check", "n_clicks"),
    State("duplicate-uid", "value"),
    State("duplicate-firstname", "value"),
    State("duplicate-lastname", "value"),
    prevent_initial_call=True,
)
def check_duplicates(n_clicks, uid_value, first_name=None, last_name=None):
    if not n_clicks:
        raise PreventUpdate
    if not current_user.is_authenticated or not has_access(current_user, DUPLICATE_CHECKER):
        return html.P("No Access!", className="has-text-danger")
    try:
        query = build_query(uid_value, first_name, last_name)
    except ValueError as exc:
        return html.P(str(exc), className="has-text-warning")
    try:
        result = SQL("engage").get_loader().load_data(query)
        target, duplicates, message = find_duplicates(result)
    except Exception:
        logger.exception("Duplicate lookup failed")
        return html.P("Unable to check duplicates. Please try again.", className="has-text-danger")
    return html.Div([
        html.P(message, className="notification is-info"),
        html.H2("Matching accounts", className="subtitle"),
        make_table(target),
        html.H2("Potential duplicate accounts", className="subtitle mt-5"),
        make_table(duplicates),
    ])
