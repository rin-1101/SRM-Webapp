import os
import dash
from dash import Dash, dcc, html, Input, Output, callback
from dash import dcc, html, Input, Output, State, ctx
import dash_table
import pandas as pd


import sys
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\utils\\app_classes\\")
from inventory import Inventory  
from datetime import datetime

DB_FOLDER = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory"
ASSETS_FOLDER = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\assets\inventory"
TABLE_NAME = "prize_pool"
USER = "dash_user"

def get_db_files():
    files = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db")]
    return files

dash.register_page(__name__, path="/inventory")


def layout():
    return _layout()
def _layout():
    return html.Div(className="container", id='inventory-db-manager', children=[
        html.H2("Inventory DB new Manager", className="title is-2"),
        #
        # Link to specific CSS file for this layout
        html.Link(rel='stylesheet', href='/assets/inventory/inv-style.css'),

        # Database Selection
        html.Label("Select Database:", className="label"),
        dcc.Dropdown(
            id="db-dropdown",
            options=[{"label": f, "value": f} for f in get_db_files()],
            value=get_db_files()[0] if get_db_files() else None,
            clearable=False,
            className="input"
        ),

        html.Hr(),

        # Create New DB Section
        html.Div(className="columns", children=[
            html.Div(className="column", children=[
                dcc.Input(id="new-db-name", type="text", placeholder="New DB filename (with .db)", className="input"),
                html.Button("Create New DB", id="btn-create-db", n_clicks=0, className="button is-primary")
            ]),
            html.Div(id="create-db-output", style={"marginTop": "10px", "color": "green"})
        ]),

        html.Hr(),

        # Upload Section
        html.Div(className="columns", children=[
            html.Div(className="column", children=[
                html.Label("Upload CSV:", className="label"),
                dcc.Upload(id="upload-data", children=html.Button("Upload CSV", className="button is-link"), multiple=False),
                html.Div(id="upload-status", style={"marginTop": "10px", "color": "green"})
            ])
        ]),

        html.Hr(),

        # Search Section
        html.Div(className="columns", children=[
            html.Div(className="column", children=[
                html.Label("Search by Name:", className="label"),
                dcc.Input(id="search-name", type="text", placeholder="Partial name", className="input")
            ]),
            html.Div(className="column", children=[
                html.Label("Category:", className="label"),
                dcc.Input(id="search-category", type="text", placeholder="Partial category", className="input")
            ]),
            html.Div(className="column", children=[
                html.Label("Min Cost:", className="label"),
                dcc.Input(id="search-min-cost", type="number", min=0, className="input")
            ]),
            html.Div(className="column", children=[
                html.Label("Max Cost:", className="label"),
                dcc.Input(id="search-max-cost", type="number", min=0, className="input")
            ])
        ]),
        html.Button("Search", id="btn-search", n_clicks=0, className="button is-info"),

        html.Hr(),

        # Table Section
        html.Div(className="table-wrapper", children=[
            dash_table.DataTable(
                id="inventory-table",
                columns=[
                    {"name": "ID", "id": "ID"},
                    {"name": "Name", "id": "name"},
                    {"name": "Cost", "id": "cost"},
                    {"name": "Category", "id": "category"},
                    {"name": "Inventory", "id": "inventory"},
                ],
                data=[],
                row_selectable="single",
                selected_rows=[],
                page_size=10
            )
        ]),

        html.Hr(),

        # Add / Update Section
        html.Div(className="columns", children=[
            html.Div(className="column", children=[
                html.Label("ID:", className="label"),
                dcc.Input(id="input-id", type="text", className="input"),

                html.Label("Name:", className="label"),
                dcc.Input(id="input-name", type="text", className="input"),

                html.Label("Cost:", className="label"),
                dcc.Input(id="input-cost", type="number", min=0, className="input"),

                html.Label("Category:", className="label"),
                dcc.Input(id="input-category", type="text", className="input"),

                html.Label("Inventory:", className="label"),
                dcc.Input(id="input-inventory", type="number", min=0, className="input"),
            ])
        ]),
        html.Div(className="columns", children=[
            html.Div(className="column", children=[

                html.Button("Add Item", id="btn-add", n_clicks=0, className="button is-primary"),
                html.Button("Update Item", id="btn-update", n_clicks=0, className="button is-warning"),
                html.Button("Delete Selected Item", id="btn-delete", n_clicks=0, className="button is-danger")
            ])
        ]),
        html.Div(id="action-output", style={"marginTop": "20px", "color": "blue"})
    ])


@callback(
    Output("create-db-output", "children"),
    Output("db-dropdown", "options"),
    Input("btn-create-db", "n_clicks"),
    State("new-db-name", "value"),
    prevent_initial_call=True,
)
def create_database(n_clicks, new_db_name):
    if not new_db_name:
        return "Please enter a database filename.", dash.no_update

    result = Inventory.create_new_db(DB_FOLDER, new_db_name, TABLE_NAME)

    if result is True:
        options = [{"label": f, "value": f} for f in get_db_files()]
        return f"Database '{new_db_name}' created successfully.", options
    else:
        return f"Error creating database: {result}", dash.no_update
import io
import base64

@callback(
    Output("inventory-table", "data"),
    Output("action-output", "children"),
    Output("upload-status", "children"),
    Input("db-dropdown", "value"),
    Input("btn-search", "n_clicks"),
    Input("btn-add", "n_clicks"),
    Input("btn-update", "n_clicks"),
    Input("btn-delete", "n_clicks"),
    Input("upload-data", "contents"),
    State("search-name", "value"),
    State("search-category", "value"),
    State("search-min-cost", "value"),
    State("search-max-cost", "value"),
    State("input-id", "value"),
    State("input-name", "value"),
    State("input-cost", "value"),
    State("input-category", "value"),
    State("input-inventory", "value"),
    State("inventory-table", "data"),
    State("inventory-table", "selected_rows")
)
def manage_inventory_and_upload(
        selected_db, btn_search, btn_add, btn_update, btn_delete, upload_contents,
        search_name, search_category, search_min_cost, search_max_cost,
        input_id, input_name, input_cost, input_category, input_inventory,
        table_data, selected_rows
):
    # If no database is 
    # update
    if not selected_db:
        return [], "No database selected.", dash.no_update

    # Initialize the Inventory class
    inv = Inventory(DB_FOLDER, selected_db, TABLE_NAME, USER)

    triggered_id = ctx.triggered_id
    try:
        # Handle CSV Upload
        if triggered_id == "upload-data" and upload_contents:
            content_type, content_string = upload_contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

                # Try to add the rows to the database
                for index, row in df.iterrows():
                    item_id = int(row.get("id", 0))
                    name = row.get("name", "")
                    cost = int(row.get("cost", 0))
                    category = row.get("category", "")
                    inventory = int(row.get("inventory", 0))

                    result = inv.add_item(item_id, name, cost, category, inventory)
                    if result != True:
                        return dash.no_update, f"Error adding item from CSV: {result}", dash.no_update

                # After uploading, show the updated inventory
                df_inventory = inv.show_inventory()
                return df_inventory.to_dict('records'), "CSV file uploaded and data added successfully.", "File processed."
            except Exception as e:
                return dash.no_update, f"Error processing CSV file: {str(e)}", dash.no_update

        # Handle Search
        elif triggered_id == "btn-search":
            df = inv.search_items(name=search_name, category=search_category, 
                                  min_cost=search_min_cost, max_cost=search_max_cost)
            if isinstance(df, str):
                return [], f"Error: {df}", dash.no_update
            else:
                return df.to_dict('records'), f"Loaded {len(df)} records from {selected_db}.", dash.no_update

        # Handle Add Item
        elif triggered_id == "btn-add":
            if None in [input_id, input_name, input_cost, input_category, input_inventory]:
                return dash.no_update, "All fields are required to add an item.", dash.no_update
            result = inv.add_item(int(input_id), input_name, int(input_cost), input_category, int(input_inventory))
            if result is True:
                df = inv.show_inventory()
                return df.to_dict('records'), f"Item '{input_name}' added successfully.", dash.no_update
            else:
                return dash.no_update, f"Error adding item: {result}", dash.no_update

        # Handle Update Item
        elif triggered_id == "btn-update":
            if not input_id:
                return dash.no_update, "❌ ID is required to update an item.", dash.no_update

            # Convert empty values to None → so update_item keeps old values
            safe_name = input_name if input_name not in [None, ""] else None
            safe_cost = int(input_cost) if input_cost not in [None, ""] else None
            safe_category = input_category if input_category not in [None, ""] else None
            safe_inventory = int(input_inventory) if input_inventory not in [None, ""] else None

            result = inv.update_item(int(input_id), safe_name, safe_cost, safe_category, safe_inventory)

            if result is True:
                df = inv.show_inventory()
                return df.to_dict("records"), f"✅ Item ID {input_id} updated successfully.", dash.no_update
            else:
                return dash.no_update, f"❌ Error updating item: {result}", dash.no_update



        # Handle Delete Item
        elif triggered_id == "btn-delete":
            if not selected_rows or not table_data:
                return dash.no_update, "Please select an item to delete.", dash.no_update
            row_idx = selected_rows[0]
            row = table_data[row_idx]
            item_id = row.get("ID")
            if item_id is None:
                return dash.no_update, "Selected item has no ID.", dash.no_update
            result = inv.delete_item(item_id)
            if result is True:
                df = inv.show_inventory()
                return df.to_dict('records'), f"Item with ID {item_id} deleted successfully.", dash.no_update
            else:
                return dash.no_update, f"Error deleting item: {result}", dash.no_update

        else:
            # Default action when no button is clicked
            df = inv.show_inventory()
            return df.to_dict('records'), f"Loaded {len(df)} records from {selected_db}.", dash.no_update

    except Exception as e:
        return [], f"Unexpected error: {e}", dash.no_update
