import os
import dash
from dash import Dash, dcc, html, Input, Output, State, ctx, callback
import dash_table
import pandas as pd
import sys
import io
import base64
from datetime import datetime
import os
from utils.paths import TRANSACTIONS

# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page


ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService
loader = SQL("halo").get_loader()

from okada.utils.format import comma_format, human_format
from okada import LogService

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\utils\\app_classes\\")

# Page registration
dash.register_page(__name__, path=TRANSACTIONS)
require_login(
    __name__, access_level=restricted_page[TRANSACTIONS]["access_level"])

#logger is always needed
logger = LogService("transactions").get_logger()
from shop import ShopTransaction 
from inventory import Inventory

DB_FOLDER = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\shop"
INV_FOLDER = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory"

TABLE_NAME = "orders"
USER = "dash_user"

def get_db_files():
    files = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db")]
    return files

dash.register_page(__name__, path=TRANSACTIONS)
def get_halo_bulk(uids, prizes):
    # make sure inputs are iterable
    uids = [str(u) for u in uids if pd.notna(u)]
    prizes = [str(p) for p in prizes if pd.notna(p)]

    if not uids or not prizes:
        return pd.DataFrame(columns=["UniversalPlayerID", "PrizeName", "redeemed_count"])

    # SQL IN clause
    uids_in = ",".join([f"'{u}'" for u in uids])
    prizes_in = ",".join([f"'%{p}%'" for p in prizes])  # LIKE patterns

    sql = f"""
        WITH subq AS (
            SELECT 
                pr.PlayerID,
                ed.Name as EventName,
                pi.Value,
                pi.Name as PrizeName
            FROM HALOCOREDB.AWA.UC_PL_PrizeRedemption pr
            LEFT JOIN HALOCOREDB.AWA.UC_X_EventDefinition ed 
                ON pr.EventDefinitionID = ed.ID
            LEFT JOIN HALOCOREDB.AWA.UC_PL_PrizeRedemptionDetail prd 
                ON pr.ID = prd.PrizeRedemptionID
            LEFT JOIN HALOCOREDB.AWA.UC_X_PrizeInventory pi 
                ON prd.PrizeID = pi.ID
        )
        SELECT 
            p.UniversalPlayerID,
            pr.PrizeName,
            COUNT(pr.PrizeName) as redeemed_count
        FROM subq pr 
        LEFT JOIN HALOCOREDB.dbo.UC_PL_Player p
            ON p.PlayerID = pr.PlayerID
        WHERE p.UniversalPlayerID IN ({uids_in})
          AND EventName LIKE '%SR%'
          AND ({' OR '.join([f"PrizeName LIKE {p}" for p in prizes_in])})
        GROUP BY p.UniversalPlayerID, pr.PrizeName
    """
    try:
        df = loader.load_data(sql)
        if df.empty:
            return pd.DataFrame(columns=["UniversalPlayerID", "PrizeName", "redeemed_count"])
        return df
    except Exception as e:
        print(f"⚠️ get_halo_bulk error: {e}")
        return pd.DataFrame(columns=["UniversalPlayerID", "PrizeName", "redeemed_count"])



def layout():
    return _layout()
    if current_user.is_authenticated and has_access(current_user, TRANSACTIONS):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])

def _layout():
    return html.Div(className="container", id='shop-transactions-manager', children=[

        html.H2("Shop Transactions Manager", className="title is-2"),
        html.Link(rel='stylesheet', href='/assets/inventory/inv-style.css'),

        html.Label("Select Database:", className="label"),
        dcc.Dropdown(
            id="db-dropdown-shop",
            options=[{"label": f, "value": f} for f in get_db_files()],
            value=get_db_files()[0] if get_db_files() else None,
            clearable=False,
            className="input"
        ),

        html.Hr(),

        html.Div(className="table-wrapper", children=[
            dash_table.DataTable(
                id="shop-transactions-table",
                columns=[
                    {"name": "ID", "id": "id"},
                    {"name": "User ID", "id": "uid"},
                    {"name": "Item ID", "id": "item_id"},
                    {"name": "Item", "id": "item"},
                    {"name": "Quantity", "id": "quantity"},
                    {"name": "Cost", "id": "cost"},
                    {"name": "Total Cost", "id": "total_cost"},
                    {"name": "Credits Used", "id": "credits_used"},
                    {"name": "CP Used", "id": "cp_used"},
                    {"name": "Created", "id": "createddate"},
                    {"name": "Updated", "id": "updateddate"},
                    {"name": "Status", "id": "status"},
                    {"name":"HALO",'id':'HALO'}
                ],
                data=[],
                row_selectable="single",
                selected_rows=[],
                filter_action="native",
                sort_action="native",
                page_size=10
            )
        ]),


        html.Hr(),

        html.Div(className="columns", children=[
            html.Div(className="column", children=[
                html.Button("Delete Transaction", id="btn-delete-txn", n_clicks=0, className="button is-danger"),
                html.Button("Claimed", id="btn-claim-txn", n_clicks=0, className="button"),
            ])
        ]),

        html.Div(id="txn-action-output", style={"marginTop": "20px", "color": "blue"})
    ])

import os
@callback(
    Output("shop-transactions-table", "data"),
    Output("txn-action-output", "children"),
    Input("db-dropdown-shop", "value"),
    Input("btn-delete-txn", "n_clicks"),
    Input("btn-claim-txn", "n_clicks"),
    State("shop-transactions-table", "data"),
    State("shop-transactions-table", "selected_rows"),
)
def manage_transactions(selected_db, btn_delete, btn_claim, table_data, selected_rows):
    if not selected_db:
        return [], "❌ No database selected."
    
    db_name = os.path.splitext(selected_db)[0]
    txn = ShopTransaction(DB_FOLDER, selected_db, TABLE_NAME, USER)
    inv = Inventory(INV_FOLDER, selected_db, "prize_pool", USER) 
    triggered_id = ctx.triggered_id

    try:
        if triggered_id == "btn-delete-txn":
            if not selected_rows or not table_data:
                return dash.no_update, "⚠️ Please select a transaction to delete."
            
            row_idx = selected_rows[0]
            row = table_data[row_idx]
            txn_id = row.get("id") or row.get("txn_id") 
            
            if not txn_id:
                return dash.no_update, "❌ Could not find transaction ID in table row."
            
            item_id = row.get("item_id")
            quantity = row.get("quantity")
            
            if not item_id or not quantity:
                return dash.no_update, "❌ Missing item ID or quantity in the transaction."

            result = txn.delete_transaction(txn_id)
            if result is True:
                inventory_update_result = inv.add_quantity(item_id, quantity)
                if isinstance(inventory_update_result, str): 
                    return dash.no_update, f"❌ Error updating inventory: {inventory_update_result}"
                df = txn.show_transactions()
                halo_df = get_halo_bulk(df["uid"].unique(), df["item"].unique())

                # normalize prize names for join
                df["item_lower"] = df["item"].str.lower()
                halo_df["PrizeName_lower"] = halo_df["PrizeName"].str.lower()

                # merge
                df = df.merge(
                    halo_df,
                    left_on=["uid", "item_lower"],
                    right_on=["UniversalPlayerID", "PrizeName_lower"],
                    how="left"
                )

                # fill missing as 0
                df["HALO"] = df["redeemed_count"].fillna(0).astype(int)

                # drop helper cols
                df = df.drop(columns=["item_lower", "PrizeName_lower", "UniversalPlayerID", "PrizeName", "redeemed_count"])


                return df.to_dict("records"), f"✅ Transaction {txn_id} deleted and Item {item_id} returned to inventory."
            else:
                return dash.no_update, f"❌ Error deleting transaction: {result}"

        if triggered_id == "btn-claim-txn":
            if not selected_rows or not table_data:
                return dash.no_update, "⚠️ Please select a transaction to claim."

            row_idx = selected_rows[0]
            row = table_data[row_idx]
            txn_id = row.get("id") or row.get("txn_id")  
            
            if not txn_id:
                return dash.no_update, "❌ Could not find transaction ID in table row."

            current_status = row.get("status")
            
            new_status = "pending" if current_status == "redeemed" else "redeemed"

            result = txn.update_transaction(txn_id, status = new_status)
            if result is True:
                df = txn.show_transactions()
                halo_df = get_halo_bulk(df["uid"].unique(), df["item"].unique())

                # normalize prize names for join
                df["item_lower"] = df["item"].str.lower()
                halo_df["PrizeName_lower"] = halo_df["PrizeName"].str.lower()

                # merge
                df = df.merge(
                    halo_df,
                    left_on=["uid", "item_lower"],
                    right_on=["UniversalPlayerID", "PrizeName_lower"],
                    how="left"
                )

                # fill missing as 0
                df["HALO"] = df["redeemed_count"].fillna(0).astype(int)

                # drop helper cols
                df = df.drop(columns=["item_lower", "PrizeName_lower", "UniversalPlayerID", "PrizeName", "redeemed_count"])
                return df.to_dict("records"), f"✅ Transaction {txn_id} status updated to {new_status}."
            else:
                return dash.no_update, f"❌ Error updating transaction status: {result}"

        else:
            df = txn.show_transactions()
            halo_df = get_halo_bulk(df["uid"].unique(), df["item"].unique())

            # normalize prize names for join
            df["item_lower"] = df["item"].str.lower()
            halo_df["PrizeName_lower"] = halo_df["PrizeName"].str.lower()

            # merge
            df = df.merge(
                halo_df,
                left_on=["uid", "item_lower"],
                right_on=["UniversalPlayerID", "PrizeName_lower"],
                how="left"
            )

            # fill missing as 0
            df["HALO"] = df["redeemed_count"].fillna(0).astype(int)

            # drop helper cols
            df = df.drop(columns=["item_lower", "PrizeName_lower", "UniversalPlayerID", "PrizeName", "redeemed_count"])
            return df.to_dict("records"), f"📂 Loaded {len(df)} transactions from {db_name}."

    except Exception as e:
        import traceback
        traceback.print_exc()
        return [], f"❌ Unexpected error: {e}"
