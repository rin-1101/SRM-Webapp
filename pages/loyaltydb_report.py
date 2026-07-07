import dash
import pandas as pd

from dash import html, dcc, callback, Output, Input
from utils.paths import LOYALTYDB

# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page

import sys
from datetime import datetime
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")

from loyaltydb_etl.loyalty.utils import pct_format
from loyaltydb_etl.loyalty.data import Data, get_last_update
from loyaltydb_etl.loyalty.element import Checklist, DataTable

from okada.utils.format import comma_format, human_format
from okada import LogService

logger = LogService("loyaltydb").get_logger()


dash.register_page(__name__, path=LOYALTYDB)
require_login(
    __name__, access_level=restricted_page[LOYALTYDB]["access_level"])

all_filter_list = [
    Input("loygrp-filter", "value"),
    Input("gender-filter", "value"),
    Input("age-filter", "value"),
    Input("contactable-filter", "value"),
    Input("suyear-filter", "value"),
    Input("natgrp-filter", "value"),
    Input("dom-filter", "value"),
    Input("adtgrp-filter", "value"),
    Input("vfreqgrp-filter", "value"),
    Input("vlengrp-filter", "value"),
    Input("language-filter", "value"),
]

data_class = None
data = None

def _page_layout_init():
    return html.Div([
        html.Div(id="data-output", children=[]) 
    ])
def _page_layout():
    global data_class, data
    data_class = Data() 
    data = data_class.load()
    columns_to_fill = ['Gender', 'NatGrp', 'LoyGrp', 'Age','Language','Contactable','12moActive','Dom','ADTGrp','VFreqGrp','VLenGrp']

    data[columns_to_fill] = data[columns_to_fill].fillna('N/A')

    last_update = get_last_update()
    
    main_table_cols = [
        "PID",
        "% HC Mix",
        "Theo",
        "% Theo Mix",
        "Visits",
        "% Visits Mix",
        "ADT",
        "Visits pa",
        "Hours PV",
        "Theo_TG",
        "Theo_EG",
    ]
    cols_to_agg = [
        "12moActive",
        "LoyGrp",
        "NatGrp",
        "Contactable",
        "Age",
        "Gender",
        "SU_year",
        "Dom",
        "ADTGrp",
        "VFreqGrp",
        "VLenGrp",
        "Language",
    ]
    # Apply custom sorting based on the column
    # Custom orders for specific columns
    custom_orders = {
        "LoyGrp": ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP", "Okada Club"],
        "NatGrp": ["Filipino", "Chinese", "NEA", "SEA", "Others"],
        "ADTGrp": ["30k", "20k", "10k", "5k", "1k", "Z"],
        "VFreqGrp": ["Low", "3x pw", "2x pw", "Weekly", "Fortnightly", "Monthly", "Quarterly"],
    }

    def sort_by_custom_order(values, custom_order):
        return sorted(values, key=lambda x: custom_order.index(x) if x in custom_order else float('inf'))

    values_per_col = {
        col: sort_by_custom_order(data[col].sort_values().unique().tolist(), custom_orders.get(col, []))
        for col in cols_to_agg
    }


    return html.Div(
        [
            dcc.Dropdown(id="dropdown", style={"display": "none"}),
            dcc.Store(id="data"),
            html.Div(
                [
                    html.H1(children="Loyalty Report"),
                    html.Div(
                        children="Data updated as of",
                        style={"display": "inline-block", "vertical-align": "top"},
                    ),
                    html.Label(
                        last_update,
                        style={
                            "display": "inline-block",
                            "vertical-align": "top",
                            "margin-left": "5px",
                        },
                    ),
                    html.Div(
                        [
                            dcc.Download(id="download-data-loyalty"),
                            html.Button("Export Raw", id="export-button-loyalty", className="button is-primary", n_clicks=0),
                        ]
                    ),
                ],
                style={
                    "margin-left": 30,
                    "margin-top": 30,
                    "font-family": "Helvetica",
                    "border-bottom": "2px solid light-blue",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(["Loyalty Group % active"]),
                            Checklist(
                                id="left_12moActive-loygrp-filter",
                                col="12moActive",
                                data=data,
                                default=values_per_col["12moActive"],
                                values=values_per_col["12moActive"],
                                horizontal=True,
                            ).elem,
                            html.Div(
                                [   
                                    dcc.Loading(type = 'circle',children = [html.Div(
                                        [
                                            
                                            DataTable(
                                            id="left_12mo_loygrp_pid",
                                            cols=["LoyGrp", "PID", "% mix"],
                                            ).elem,                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            DataTable(
                                                id="left_12mo_loygrp_active",
                                                cols=["% active"],
                                            ).elem,   
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    ]),
                                    
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            html.Br(),
                            html.Br(),
                            html.Label(["Nationality Group  % active"]),
                            Checklist(
                                id="left_12moActive-natgrp-filter",
                                col="12moActive",
                                data=data,
                                default=values_per_col["12moActive"],
                                values=values_per_col["12moActive"],
                                horizontal=True,
                            ).elem,
                            html.Div(
                                [
                                    dcc.Loading(type = 'circle',children = [
                                        html.Div(
                                        [
                                            
                                            DataTable(
                                            id="left_12mo_natgrp_pid",
                                            cols=["NatGrp", "PID", "% mix"],
                                            ).elem,
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            DataTable(
                                            id="left_12mo_natgrp_active",
                                            cols=["% active"],
                                            ).elem,                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    ]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            html.Br(),
                            html.Br(),
                            html.Label(["Contactable  % active"]),
                            Checklist(
                                id="left_12moActive-contactable-filter",
                                col="12moActive",
                                data=data,
                                default=values_per_col["12moActive"],
                                values=values_per_col["12moActive"],
                                horizontal=True,
                            ).elem,
                            html.Div(
                                [   dcc.Loading(type = 'circle',children = [
                                    html.Div(
                                        [
                                            
                                                DataTable(
                                                id="left_12mo_contactable_pid",
                                                cols=["Contactable", "PID", "% mix"],
                                            ).elem, 
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    html.Div(
                                        [
                                                DataTable(
                                                id="left_12mo_contactable_active",
                                                cols=["% active"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),] ),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            html.Br(),
                            html.Br(),
                            html.Label(["Age % active"]),
                            Checklist(
                                id="left_12moActive-age-filter",
                                col="12moActive",
                                data=data,
                                default=values_per_col["12moActive"],
                                values=values_per_col["12moActive"],
                                horizontal=True,
                            ).elem,
                            html.Div(
                                [dcc.Loading(type = 'circle',children = [
                                    html.Div(
                                        [
                                            
                                                DataTable(
                                                id="left_12mo_age_pid",
                                                cols=["Age", "PID", "% mix"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            
                                                DataTable(
                                                id="left_12mo_age_active",
                                                cols=["% active"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),] ),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            html.Br(),
                            html.Br(),
                            html.Label(["Gender % active"]),
                            Checklist(
                                id="left_12moActive-gender-filter",
                                col="12moActive",
                                data=data,
                                default=values_per_col["12moActive"],
                                values=values_per_col["12moActive"],
                                horizontal=True,
                            ).elem,
                            html.Div(
                                [dcc.Loading(type = 'circle',children = [
                                    html.Div(
                                        [
                                            
                                                DataTable(
                                                id="left_12mo_gender_pid",
                                                cols=["Gender", "PID", "% mix"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    html.Div(
                                        [
                                                DataTable(
                                                id="left_12mo_gender_active",
                                                cols=["% active"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),] ),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            html.Br(),
                            html.Br(),
                            html.Label(["Sign Up Year % active"]),
                            Checklist(
                                id="left_12moActive-suyear-filter",
                                col="12moActive",
                                data=data,
                                default=values_per_col["12moActive"],
                                values=values_per_col["12moActive"],
                                horizontal=True,
                            ).elem,
                            html.Div(
                                [   dcc.Loading(type = 'circle',children = [
                                    html.Div(
                                        [
                                                DataTable(
                                                id="left_12mo_suyear_pid",
                                                cols=["SU_year", "PID", "% mix"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            
                                                DataTable(
                                                id="left_12mo_suyear_active",
                                                cols=["% active"],
                                            ).elem,
                                            
                                        ],
                                        style={
                                            "display": "inline-block",
                                            "vertical-align": "top",
                                        },
                                    )]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            html.Br(),
                            html.Br(),
                        ],
                        style={
                            "display": "inline-block",
                            "vertical-align": "top",
                            "margin-top": 30,
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                children=[
                                    html.Label(["Loyalty Group KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_loygrp_active",
                                    cols=["LoyGrp"] + main_table_cols,
                                ).elem] ),
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Nationality Group KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_natgrp_active",
                                    cols=["NatGrp"] + main_table_cols,
                                ).elem]),                            
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Contactable KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_contactable_active",
                                    cols=["Contactable"] + main_table_cols,
                                ).elem] ),                            
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Age KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_age_active", cols=["Age"] + main_table_cols
                                ).elem] ),                                
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Gender KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                     DataTable(
                                    id="right_gender_active",
                                    cols=["Gender"] + main_table_cols,
                                ).elem] ),
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Sign Up Year KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_suyear_active",
                                    cols=["SU_year"] + main_table_cols,
                                ).elem] ),                            
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Dom KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_dom_active", cols=["Dom"] + main_table_cols
                                ).elem] ), 
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["ADT Group KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_adtgrp_active",
                                    cols=["ADTGrp"] + main_table_cols,
                                ).elem] ), 
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Frequency Group KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_vfreqgrp_active",
                                    cols=["VFreqGrp"] + main_table_cols,
                                ).elem]),
                            html.Br(),
                            html.Div(
                                children=[
                                    html.Label(["Visit Length Group KPI"]),
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    # "visibility" : "hidden",
                                },
                            ),
                            dcc.Loading(type = 'circle',children = [
                                    DataTable(
                                    id="right_vlengrp_active",
                                    cols=["VLenGrp"] + main_table_cols,
                                ).elem] ), 
                        ],
                        style={
                            "display": "inline-block",
                            "vertical-align": "top",
                            "margin-left": 50,
                            "margin-top": 30,
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                children=[
                                    html.Label("NatGrp"),
                                    Checklist(
                                        id="natgrp-filter",
                                        col="NatGrp",
                                        data=data,
                                        default=values_per_col["NatGrp"],
                                        values=values_per_col["NatGrp"],
                                    ).elem,
                                    html.Label("Contactable"),
                                    Checklist(
                                        id="contactable-filter",
                                        col="Contactable",
                                        data=data,
                                        default=values_per_col["Contactable"],
                                        values=values_per_col["Contactable"],
                                    ).elem,
                                    html.Label("Age"),
                                    Checklist(
                                        id="age-filter",
                                        col="Age",
                                        data=data,
                                        default=values_per_col["Age"],
                                        values=values_per_col["Age"],
                                    ).elem,
                                    html.Label("Dom"),
                                    Checklist(
                                        id="dom-filter",
                                        col="Dom",
                                        data=data,
                                        default=values_per_col["Dom"],
                                        values=values_per_col["Dom"],
                                    ).elem,
                                    html.Label("ADTGrp"),
                                    Checklist(
                                        id="adtgrp-filter",
                                        col="ADTGrp",
                                        data=data,
                                        default=values_per_col["ADTGrp"],
                                        values=values_per_col["ADTGrp"],
                                    ).elem,
                                    html.Label("Gender"),
                                    Checklist(
                                        id="gender-filter",
                                        col="Gender",
                                        data=data,
                                        default=values_per_col["Gender"],
                                        values=values_per_col["Gender"],
                                    ).elem,
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    "width": "50%",
                                },
                            ),
                            html.Div(
                                children=[
                                    html.Label("LoyGrp"),
                                    Checklist(
                                        id="loygrp-filter",
                                        col="LoyGrp",
                                        data=data,
                                        default=values_per_col["LoyGrp"],
                                        values=values_per_col["LoyGrp"],
                                    ).elem,
                                    html.Label("SU_year"),
                                    Checklist(
                                        id="suyear-filter",
                                        col="SU_year",
                                        data=data,
                                        default=values_per_col["SU_year"],
                                        values=values_per_col["SU_year"],
                                    ).elem,
                                    html.Label("VFreqGrp"),
                                    Checklist(
                                        id="vfreqgrp-filter",
                                        col="VFreqGrp",
                                        data=data,
                                        default=values_per_col["VFreqGrp"],
                                        values=sorted(values_per_col["VFreqGrp"]),
                                    ).elem,
                                    html.Label("VLenGrp"),
                                    Checklist(
                                        id="vlengrp-filter",
                                        col="VLenGrp",
                                        data=data,
                                        default=values_per_col["VLenGrp"],
                                        values=values_per_col["VLenGrp"],
                                    ).elem,
                                    html.Label("Language"),
                                    Checklist(
                                        id="language-filter",
                                        col="Language",
                                        data=data,
                                        default=values_per_col["Language"],
                                        values=values_per_col["Language"],
                                    ).elem,
                                ],
                                style={
                                    "display": "inline-block",
                                    "vertical-align": "top",
                                    "width": "50%",
                                },
                            ),
                        ],
                        style={
                            "display": "inline-block",
                            "vertical-align": "top",
                            "width": "20%",
                            "margin-left": 50,
                            "margin-top": 100,
                            "position": "sticky",
                            "top": "0",
                            "border": "1px solid g",
                        },
                    ),
                ],
                style={"margin-left": 30, "font-family": "Helvetica"},
            ),
        # html.Div(id="data-output")
        ]
    )
def layout():
    """
    Important: Always include this in the page code.
    layout function will always be used by default as where the page layout will be taken from
    This is a workaround to prevent unwanted users from accessing the report when pressing BACK.
    """
    return html.Div([
                html.Div(id="page1-output"),
                _page_layout_init(),
                # dcc.Loading(type = 'circle',children = [html.Div(_page_layout_init())]),
            ])
    if current_user.is_authenticated and has_access(current_user, LOYALTYDB):
        logger.info(f"{current_user.id} has accessed")
        return html.Div([
            html.Div(id="page1-output"),
            _page_layout_init(),
            # dcc.Loading(type = 'circle',children = [html.Div(_page_layout_init())]),
        ])
        # return html.Div(children=[_page_layout()])
    else:
        return html.Div(["No Access!"])
    # return _page_layout()


def add_mix_pct(output, grand_total=False):
    output = output.copy()
    
    if grand_total:
        output.loc["Grand Total", :] = output.sum()
        output[output.columns[0]].loc["Grand Total"] = "Grand Total"
        
    
    output["ADT"] = output["Theo"] / output["Visits"]
    output["Visits pa"] = output["Visits"] / output["PID"]
    output["Hours PV"] = output["Hours"] / output["Visits"]

    if grand_total:
        output["% HC Mix"] = output["PID"] / output.iloc[:-1]["PID"].sum()
        output["% Theo Mix"] = output["Theo"] / output.iloc[:-1]["Theo"].sum()
        output["% Visits Mix"] = output["Visits"] / output.iloc[:-1]["Visits"].sum()
    else:
        output["% HC Mix"] = output["PID"] / output["PID"].sum()
        output["% Theo Mix"] = output["Theo"] / output["Theo"].sum()
        output["% Visits Mix"] = output["Visits"] / output["Visits"].sum()

    output["% HC Mix"] = output["% HC Mix"].apply(pct_format)
    output["% Theo Mix"] = output["% Theo Mix"].apply(pct_format)
    output["% Visits Mix"] = output["% Visits Mix"].apply(pct_format)

    output["PID"] = output["PID"].apply(comma_format)
    output["ADT"] = output["ADT"].apply(comma_format)
    output["Visits pa"] = output["Visits pa"].apply(comma_format)
    output["Theo"] = output["Theo"].apply(human_format)
    output["Visits"] = output["Visits"].apply(comma_format)
    output["Hours PV"] = output["Hours PV"].round(decimals=1)
    output["Theo_TG"] = output["Theo_TG"].apply(human_format)
    output["Theo_EG"] = output["Theo_EG"].apply(human_format)

    return output
def sort_by_custom_order(df, col, desired_order):
    # Convert the specified column to a categorical type with the desired order
    df[col] = pd.Categorical(df[col], categories=desired_order, ordered=True)
    
    # Sort the DataFrame based on this order
    sorted_df = df.sort_values(col).reset_index(drop=True)
    
    # Convert the column back to string type
    sorted_df[col] = sorted_df[col].astype(str)
    
    return sorted_df


def filtered_table_agg(data, col):
    # Perform grouping and aggregation first without any modification to the column type
    output = data.groupby([col]).agg(
        {
            "PID": "sum",
            "Theo": "sum",
            "Visits": "sum",
            "Hours": "sum",
            "Theo_TG": "sum",
            "Theo_EG": "sum",
        }
    ).reset_index()  # Reset index to make 'col' a column in the output DataFrame
    
    # Apply custom sorting based on the column
    if col == "LoyGrp":
        desired_order = ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP", "Okada Club", "Grand Total"]
        output = sort_by_custom_order(output, col, desired_order)
    
    elif col == "NatGrp":
        desired_order = ["Filipino", "Chinese", "NEA", "SEA", "Others", "Grand Total"]
        output = sort_by_custom_order(output, col, desired_order)
    
    elif col == "ADTGrp":
        desired_order = ["30k", "20k", "10k", "5k", "1k", "Z", "Grand Total"]
        output = sort_by_custom_order(output, col, desired_order)
        
    elif col == "VFreqGrp":
        desired_order = ["Low","3x pw", "2x pw", "Weekly", "Fortnightly", "Monthly", "Quarterly", "Grand Total"]
        output = sort_by_custom_order(output, col, desired_order)

    return output

def filtered_table(data, col):
    # Apply custom sorting based on the column
    output = data
    if col == "LoyGrp":
        desired_order = ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP", "Okada Club", "Grand Total"]
        output = sort_by_custom_order(data, col, desired_order)
    
    elif col == "NatGrp":
        desired_order = ["Filipino", "Chinese", "NEA", "SEA", "Others", "Grand Total"]
        output = sort_by_custom_order(data, col, desired_order)
    
    elif col == "ADTGrp":
        desired_order = ["30k", "20k", "10k", "5k", "1k", "Z", "Grand Total"]
        output = sort_by_custom_order(data, col, desired_order)
        
    elif col == "VFreqGrp":
        desired_order = ["Low","3x pw", "2x pw", "Weekly", "Fortnightly", "Monthly", "Quarterly", "Grand Total"]
        output = sort_by_custom_order(data, col, desired_order)

    return output



def filtered_pid_agg(data, col, grand_total=False):
    output = data.groupby([col]).agg(
        {
            "PID": "sum",
        }
    ).reset_index()
    if grand_total:
        output.loc["Grand Total", "PID"] = output["PID"].sum()
        output["% mix"] = output["PID"] / output.iloc[:-1]["PID"].sum()
        output[output.columns[0]].loc["Grand Total"] = "Grand Total"
    else:
        output["% mix"] = output["PID"] / output["PID"].sum()
    # Apply custom sorting based on the column
    if col == "LoyGrp":
        desired_order = ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP", "Okada Club", "Grand Total"]
        output = sort_by_custom_order(output, col, desired_order)
    elif col == "NatGrp":
        desired_order = ["Filipino", "Chinese", "NEA", "SEA", "Others", "Grand Total"]
        output = sort_by_custom_order(output, col, desired_order)
    #  Apply formatting
    output["PID"] = output["PID"].apply(comma_format)
    output["% mix"] = output["% mix"].apply(pct_format)
    
    
        
    return output


import pandas as pd
import numpy as np
def get_pct_active_mix(left_data_data, col, left_filter, grand_total=False):


    left_data = left_data_data.copy()
    
    left_is_active = 'Active' in left_filter if left_filter else False
    left_is_inactive = 'Inactive' in left_filter if left_filter else False
    
    if not left_is_active and not left_is_inactive:
        return pd.DataFrame({col: [], "% active": []})

    right_data = left_data.copy() 
    
    left_data = left_data[left_data["12moActive"] == "Active"]
    
    if left_data.empty:
        left_output = pd.DataFrame(columns=["PID"])
    else:
        left_output = left_data.groupby([col]).agg({"PID": "sum"})
    right_output = right_data.groupby([col]).agg({"PID": "sum"})
    
    if grand_total:
        right_output.loc["Grand Total", "PID"] = right_output["PID"].sum()
        left_output.loc["Grand Total", "PID"] = left_output["PID"].sum()
    # Merge as before, filling inactive rows with 0 for `PID_left`
    merged = right_output.merge(
        left_output, left_index=True, right_index=True, how="left", suffixes=["_right", "_left"]
    )
    merged["PID_left"].fillna(0, inplace=True)

    # Calculate % active based on the filter selection
    if left_is_active and left_is_inactive:
        merged["% active"] = np.where(
            merged["PID_right"] != 0,
            merged["PID_left"] / merged["PID_right"],  # Active / Total
            0
        )
    elif left_is_active:
        merged = left_output
        merged["% active"] = 1  # 100%
    elif left_is_inactive:
        merged = right_output
        merged["% active"] = 0  # 0%

    # Reset index as before and apply formatting if needed
    merged = merged.reset_index()
    if pct_format:
        merged["% active"] = merged["% active"].apply(pct_format)

    return merged



def apply_month_active_filter(df, month_active_filter):
    if month_active_filter:
        return df[df["12moActive"].isin(month_active_filter)]
    return df

# @callback(Output("data", "value"), Input("dropdown", "value"))
# def read_data(value):
#     """
#     This stores the data the the browser session.
#     Benefit is that when using the checklis filter, it won't requery the data again.
#     Which can take time and increase traffic.
#     """
#     # data = data_class.load()

#     return data.to_json(date_format="iso", orient="split")

@callback(
    Output("data-output", "children"),
    Input("page1-output", "children")  # Triggered on page load
)
def load_data(_):
    return _page_layout()  # Dynamically load and return the layout

@callback(
    Output("right_loygrp_active", "data"),
    Output("right_natgrp_active", "data"),
    Output("right_contactable_active", "data"),
    Output("right_age_active", "data"),
    Output("right_gender_active", "data"),
    Output("right_suyear_active", "data"),
    Output("right_dom_active", "data"),
    Output("right_adtgrp_active", "data"),
    Output("right_vfreqgrp_active", "data"),
    Output("right_vlengrp_active", "data"),
    Output("left_12mo_loygrp_pid", "data"),
    Output("left_12mo_natgrp_pid", "data"),
    Output("left_12mo_contactable_pid", "data"),
    Output("left_12mo_age_pid", "data"),
    Output("left_12mo_gender_pid", "data"),
    Output("left_12mo_suyear_pid", "data"),
    Output("left_12mo_loygrp_active", "data"),
    Output("left_12mo_natgrp_active", "data"),
    Output("left_12mo_contactable_active", "data"),
    Output("left_12mo_age_active", "data"),
    Output("left_12mo_gender_active", "data"),
    Output("left_12mo_suyear_active", "data"),
    [
        Input("data", "value"),
        Input("left_12moActive-loygrp-filter", "value"),
        Input("left_12moActive-natgrp-filter", "value"),
        Input("left_12moActive-contactable-filter", "value"),
        Input("left_12moActive-age-filter", "value"),
        Input("left_12moActive-gender-filter", "value"),
        Input("left_12moActive-suyear-filter", "value"),
    ]
    + all_filter_list,
)
def update_right_loygrp_active(
    json_data,
    loygrp_left_12mo_active_filter,
    natgrp_left_12mo_active_filter,
    contactable_left_12mo_active_filter,
    age_left_12mo_active_filter,
    gender_left_12mo_active_filter,
    suyear_left_12mo_active_filter,
    loygrp_filter,
    gender_filter,
    age_filter,
    cont_filter,
    su_year_filter,
    natgrp_filter,
    dom_filter,
    adtgrp_filter,
    vfreqgrp_filter,
    vlengrp_filter,
    language_filter,
):

    # data = data_class.load()
    filtered_data = data[
        (data["LoyGrp"].isin(loygrp_filter) if loygrp_filter else True)
        & (data["Gender"].isin(gender_filter) if gender_filter else True)
        & (data["Age"].isin(age_filter) if age_filter else True)
        & (data["Contactable"].isin(cont_filter) if cont_filter else True)
        & (data["SU_year"].isin(su_year_filter) if su_year_filter else True)
        & (data["NatGrp"].isin(natgrp_filter) if natgrp_filter else True)
        & (data["Dom"].isin(dom_filter) if dom_filter else True)
        & (data["ADTGrp"].isin(adtgrp_filter) if adtgrp_filter else True)
        & (data["VFreqGrp"].isin(vfreqgrp_filter) if vfreqgrp_filter else True)
        & (data["VLenGrp"].isin(vlengrp_filter) if vlengrp_filter else True)
        & (data["Language"].isin(language_filter) if language_filter else True)
    ]
    filtered_active_data = filtered_data[filtered_data["12moActive"] == "Active"]

    loygrp_output = filtered_table_agg(filtered_active_data, "LoyGrp")
    loygrp_output = add_mix_pct(loygrp_output, grand_total=True).reset_index()
    
    natgrp_output = filtered_table_agg(filtered_active_data, "NatGrp")
    natgrp_output = add_mix_pct(natgrp_output, grand_total=True).reset_index()

    contactable_output = filtered_table_agg(filtered_active_data, "Contactable")
    contactable_output = add_mix_pct(contactable_output, grand_total=True).reset_index()

    age_output = filtered_table_agg(filtered_active_data, "Age")
    age_output = add_mix_pct(age_output, grand_total=True).reset_index()

    gender_output = filtered_table_agg(filtered_active_data, "Gender")
    gender_output = add_mix_pct(gender_output, grand_total=True).reset_index()

    suyear_output = filtered_table_agg(filtered_active_data, "SU_year")
    suyear_output = add_mix_pct(suyear_output, grand_total=True).reset_index()

    dom_output = filtered_table_agg(filtered_active_data, "Dom")
    dom_output = add_mix_pct(dom_output, grand_total=True).reset_index()

    adtgrp_output = filtered_table_agg(filtered_active_data, "ADTGrp")
    adtgrp_output = add_mix_pct(adtgrp_output, grand_total=True).reset_index()

    vfreqgrp_output = filtered_table_agg(filtered_active_data, "VFreqGrp")
    vfreqgrp_output = add_mix_pct(vfreqgrp_output, grand_total=True).reset_index()

    vlen_output = filtered_table_agg(filtered_active_data, "VLenGrp")
    vlen_output = add_mix_pct(vlen_output, grand_total=True).reset_index()



    loygrp_filtered_pid_agg = filtered_data[
        (
            filtered_data["12moActive"].isin(loygrp_left_12mo_active_filter)
            if loygrp_left_12mo_active_filter
            else True
        )
    ]
    loygrp_filtered_pid_agg = filtered_pid_agg(
        loygrp_filtered_pid_agg, "LoyGrp", grand_total=True
    ).reset_index()

    natgrp_filtered_pid_agg = filtered_data[
        (
            filtered_data["12moActive"].isin(natgrp_left_12mo_active_filter)
            if natgrp_left_12mo_active_filter
            else True
        )
    ]
    natgrp_filtered_pid_agg = filtered_pid_agg(
        natgrp_filtered_pid_agg, "NatGrp", grand_total=True
    ).reset_index()

    contactable_filtered_pid_agg = filtered_data[
        (
            filtered_data["12moActive"].isin(contactable_left_12mo_active_filter)
            if contactable_left_12mo_active_filter
            else True
        )
    ]
    contactable_filtered_pid_agg = filtered_pid_agg(
        contactable_filtered_pid_agg, "Contactable", grand_total=True
    ).reset_index()

    age_filtered_pid_agg = filtered_data[
        (
            filtered_data["12moActive"].isin(age_left_12mo_active_filter)
            if age_left_12mo_active_filter
            else True
        )
    ]
    age_filtered_pid_agg = filtered_pid_agg(age_filtered_pid_agg, "Age", grand_total=True).reset_index()

    gender_filtered_pid_agg = filtered_data[
        (
            filtered_data["12moActive"].isin(gender_left_12mo_active_filter)
            if gender_left_12mo_active_filter
            else True
        )
    ]
    gender_filtered_pid_agg = filtered_pid_agg(
        gender_filtered_pid_agg, "Gender", grand_total=True
    ).reset_index()

    suyear_filtered_pid_agg = filtered_data[
        (
            filtered_data["12moActive"].isin(suyear_left_12mo_active_filter)
            if suyear_left_12mo_active_filter
            else True
        )
    ]
    suyear_filtered_pid_agg = filtered_pid_agg(
        suyear_filtered_pid_agg, "SU_year", grand_total=True
    ).reset_index()


    loygrp_merged = get_pct_active_mix(
        filtered_data,
        "LoyGrp",
        loygrp_left_12mo_active_filter,
        grand_total=True
    )
    desired_order = ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP", "Okada Club", "Grand Total"]
    loygrp_merged = sort_by_custom_order(loygrp_merged, "LoyGrp", desired_order)
    loygrp_merged = loygrp_merged[["% active"]]

    natgrp_merged = get_pct_active_mix(
        filtered_data,
        "NatGrp",
        natgrp_left_12mo_active_filter,
        grand_total=True
    )    
    desired_order = ["Filipino", "Chinese", "NEA", "SEA", "Others", "Grand Total"]
    # desired_order = ["Prime", "Elite", "Premium", "Supreme", "Maharlika", "Okada VIP", "Grand Total"]
    natgrp_merged = sort_by_custom_order(natgrp_merged, "NatGrp", desired_order)
    natgrp_merged = natgrp_merged[["% active"]]
    
    contactable_merged = get_pct_active_mix(
        filtered_data,
        "Contactable",
        contactable_left_12mo_active_filter,
        grand_total=True
    )[["% active"]]
    age_merged = get_pct_active_mix(
        filtered_data,
        "Age",
        age_left_12mo_active_filter,
        grand_total=True
    )[["% active"]]
    gender_merged = get_pct_active_mix(
        filtered_data,
        "Gender",
        gender_left_12mo_active_filter,
        grand_total=True
    )[["% active"]]
    suyear_merged = get_pct_active_mix(
        filtered_data,
        "SU_year",
        suyear_left_12mo_active_filter,
        grand_total=True
    )[["% active"]]


    return (
        loygrp_output.to_dict("records"),
        natgrp_output.to_dict("records"),
        contactable_output.to_dict("records"),
        age_output.to_dict("records"),
        gender_output.to_dict("records"),
        suyear_output.to_dict("records"),
        dom_output.to_dict("records"),
        adtgrp_output.to_dict("records"),
        vfreqgrp_output.to_dict("records"),
        vlen_output.to_dict("records"),
        loygrp_filtered_pid_agg.to_dict("records"),
        natgrp_filtered_pid_agg.to_dict("records"),
        contactable_filtered_pid_agg.to_dict("records"),
        age_filtered_pid_agg.to_dict("records"),
        gender_filtered_pid_agg.to_dict("records"),
        suyear_filtered_pid_agg.to_dict("records"),
        loygrp_merged.to_dict("records"),
        natgrp_merged.to_dict("records"),
        contactable_merged.to_dict("records"),
        age_merged.to_dict("records"),
        gender_merged.to_dict("records"),
        suyear_merged.to_dict("records"),
    )


@callback(
    Output("download-data-loyalty", "data"),
    Input("export-button-loyalty", "n_clicks"),
    prevent_initial_call=True,
)
def export_filtered_data(n_clicks):
    data_class = Data() 
    data = data_class.load()
    return dcc.send_data_frame(data.to_csv, filename="loyalty_raw.csv", index=False)
