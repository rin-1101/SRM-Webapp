# import dash
# from dash import Dash, dcc, html, Input, Output, callback
# from urllib.parse import parse_qs
# import pandas as pd
# import math
# import re
# from datetime import datetime
# from utils.paths import LEADERBOARD
# # from utils.app_classes.patron import Patron
# from flask_login import current_user
# from utils.login_handler import require_login, has_access, restricted_page
# import sys
# ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
# sys.path.append(f"{ROOT}\\okada\\")
# sys.path.append(f"{ROOT}\\reports\\utils\\app_classes\\")
# # Helper class/ setup if needed
# from patron import Patron



# ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
# sys.path.append(ROOT)
# from okada import SQL, SQLService
# # loader = SQL("halo").get_loader()
# # hloader = SQL("hive").get_loader()
# from okada.utils.format import comma_format, human_format
# from okada import LogService
# logger = LogService("Leaderboard-dev").get_logger()
# filename = "Leaderboards_test.xlsx"
# dash.register_page(__name__, path=LEADERBOARD)

# def layout(**kwargs):
#     return _layout()
#     if current_user.is_authenticated and has_access(current_user, LEADERBOARD):
#         logger.info(f"{current_user.id} has accessed")
#         return _layout()
#     else:
#         return html.Div(["No Access!"])


# from dash import html, dcc

# def load_latest_file(selected_value, base_time):
#     for i in range(6):  # Try last 6 intervals (0 to 150 minutes ago)
#         attempt_time = base_time - timedelta(minutes=30 * i)
#         timestamp = attempt_time.strftime("%Y-%m-%d_%H-%M-%S")
#         path_data = fr"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\pages\ios_chase_etl\files\{selected_value}_Leaderboards.csv"
        
#         if os.path.exists(path_data):
#             try:
#                 print(f"Loading: {path_data}")
#                 df = pd.read_csv(path_data)
#                 return df, timestamp  # Return both data and timestamp
#             except Exception as e:
#                 print(f"Error reading {selected_value} file: {e}")
#     # print(f"No valid {selected_value} file found.")
#     return None, None



# def _layout(**kwargs):
#     #get patron dom

#     return html.Div(
#         children=[
#             # Stores
#             dcc.Store(id="leader-store-uid", data="OM"),
#             dcc.Location(id='leader-url', refresh=True),
#             dcc.Dropdown(
#                 id='leader-dropdown',
#                 options=[
#                     {'label': 'TG', 'value': 'TG'},
#                     {'label': 'EG', 'value': 'EG'},
#                 ],
#                 value=f'TG',
#                 clearable=False,
#                 className='leader-dropdown'
#             ),



#             html.Button(
#                     "Back", 
#                     id="leader-back-button",
#                     className="button is-white leg-box-transparent-button"
#                 ),
#             # Main Container
#             html.Div(
#                 id="leader-main-container",
#                 className="section has-text-centered",
#                 children=[
                    
                    
#                     # Footer Section
#                     html.Div(
#                         id="leader-footer",
#                         className="app-footer",
#                         children=[
#                             html.Img(
#                                 id="pagcor-main",
#                                 src='/assets/DEFAULT/pagcor.png'
#                             ),
#                             html.Img(
#                                 id="okada-long-main",
#                                 src='/assets/DEFAULT/okada-long.png'
#                             ),
#                         ]
#                     ),
#                     # Logo Section
#                     html.Div(
#                         id="leader-logo-container",
#                         children=[
#                             html.Div(
#                                 id="leader-Logo",
#                                 className="box is-flex is-justify-content-center is-align-items-center",
#                                 children=[
#                                     html.Img(

#                                         id="leader-logo-main",
#                                         src='/assets/tracker/LOGO.png'
#                                     ),
#                                 ]
#                             )
#                         ]
#                     ),

#                     # Leaderboard Container
#                     html.Div(
#                         id="leader-leaderboard-container",
#                         className="container",
#                         children=[

#                             # Patron Data Box
#                             html.Div(
#                                 id="leader-main-patron",
#                                 className="box mb-5",
#                                 children=[
#                                     html.Div(id='leader-output-value', className="title is-4"),
#                                     html.Div("Rank X | X TP",id='leader-details-value'),
#                                     html.Div("Date as of",id='leader-asof')
#                                 ]
#                             ),

#                             # Ranking List
                            
                            
#                             # Ranking List (Top 17)
#                             html.Div(
#                                 id="leader-ranking-container",
#                                 className="box",
#                                 children=[
#                                     html.Div(
#                                             id=f"leader-rank-header",
#                                             className="leader-ranking",
#                                             children=[
#                                                 html.Div("Rank", className="leader-rank-col rank-left"),
#                                                 html.Div("OM Number", className="leader-rank-col rank-center"),
#                                                 html.Div("TP", className="leader-rank-col rank-right"),
#                                             ]
#                                         ),
#                                     html.Div(id="leader-ranking-container-result",children = [
#                                         html.Div(
#                                             id=f"leader-rank{i}",
#                                             className="leader-ranking",
#                                             children=[
#                                                 html.Div(str(i), className="leader-rank-col rank-left"),
#                                                 html.Div("OMXXXXXXXXX", className="leader-rank-col rank-center"),
#                                                 html.Div("0", className="leader-rank-col rank-right"),
#                                             ]
#                                         ) for i in range(1, 18)  # from 1 to 17
#                                     ])
                                    
#                                 ]
#                             )


#                         ]
#                     ),
                    
#                 ]
#             )
#         ]
#     )


# @callback(
#     Output('leader-output-value', 'children'),
#     Input('leader-url', 'search')  # Get query string
# )
# def display_value_from_url(search):
#     if search:
#         parsed = parse_qs(search.lstrip('?'))
#         patron = Patron(parsed)
#         return f"{patron.get_om()}"
#     return "No input_value provided"
# from datetime import datetime, timedelta
# from datetime import datetime, timedelta
# import pandas as pd
# import os



# # Round to nearest lower 10-minute mark
# def round_to_nearest_30_minutes(dt=None):
#     if dt is None:
#         dt = datetime.now()
#     dt = dt.replace(second=0, microsecond=0)
#     minute = (dt.minute // 30) * 30
#     return dt.replace(minute=minute)


# @callback(
#     [Output('leader-details-value', 'children'),    # Update leader details
#      Output('leader-ranking-container-result', 'children'),
#      Output('leader-asof','children')],  # Update the ranking list
#     #  Output('leader-drpdwn','children')],  # Update the ranking list
#     [Input('leader-dropdown', 'value'),  # Dropdown value (TG or EG)
#      Input('leader-url', 'search')]  # Get query string from URL
# )
# def set_data(selected_value, search):

#     # Initialize current time rounded down
#     base_time = round_to_nearest_30_minutes()

#     # Try loading the CSV file with fallback up to 6 times (1 hour back)
#     data_main = None
#     error_msg = ""

#     # Round current time to previous 30 minutes
#     now = datetime.now()
#     minute = (now.minute // 30) * 30
#     base_time = now.replace(minute=minute, second=0, microsecond=0)
    
    
#     try:
#         timestamp = base_time.strftime("%Y-%m-%d_%H-%M-%S")
#         path_data = fr"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\pages\ios_chase_etl\files\{selected_value}_Leaderboards.csv"
#         data_main = pd.read_csv(path_data)
#     except:
#         for i in range(6):  # 0, 1, 2, ..., 5 = 0 to 50 minutes ago
#             delta = i * 30
#             attempt_time = base_time - timedelta(minutes = delta)
#             timestamp = attempt_time.strftime("%Y-%m-%d_%H-%M-%S")
#             path_data = fr"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\pages\ios_chase_etl\files\{selected_value}_Leaderboards.csv"
            
#             if os.path.exists(path_data):
#                 try:
#                     data_main = pd.read_csv(path_data)
#                     break
#                 except Exception as e_inner:
#                     print(f"Error reading fallback file {path_data}: {e_inner}")
#             else:
#                 print(f"File not found: {path_data}")



#     if 'rank' not in data_main.columns or 'UniversalPlayerID' not in data_main.columns or 'TP_Earning' not in data_main.columns:
#         return "Invalid data format. Columns 'rank', 'UniversalPlayerID', and 'TP_Earning' are required.", []

#     top_17 = data_main.head(17)
#     # top_17['UniversalPlayerID'] = top_17['UniversalPlayerID'].apply(lambda x: f"{x[:2]}{'*' * (len(x) - 5)}{x[-3:]}")
    

#     patron_id = None
#     if search:
#         parsed = parse_qs(search.lstrip('?'))
#         patron_id = Patron(parsed).get_om()

#     if patron_id:
#         patron_data = top_17[top_17['UniversalPlayerID'].str.strip() == patron_id.strip()]
#         if not patron_data.empty:
#             # Patron found in the data
#             rank = patron_data['rank'].values[0]
#             tp_earned = math.ceil(patron_data['TP_Earning'].values[0])
#         else:
#             rank = 'N/A'
#             tp_earned = 'N/A'
#     else:
#         rank = 'N/A'
#         tp_earned = 'N/A'

#     leader_details_value = f"Rank {rank} | {tp_earned} TP"
#     top_17['UniversalPlayerID'] = top_17['UniversalPlayerID'].apply(lambda x: f"{x[:2]}{'*' * (len(x) - 5)}{x[-3:]}")
    
    
#     date = ''
#     date_match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})', path_data)
#     if date_match:
#         date_part = date_match.group(1)
#         time_part = date_match.group(2).replace('-', ':')
#         date_str = f"{date_part} {time_part}"
#         date = datetime.strptime(date_str, '%Y-%m-%d %H:%M').strftime('%m-%d-%Y %H:%M')
#     else:
#         date = "Unknown Date"  # In case no date is found in the filename
    
#     date_str = f'date as of {date}'
    
#     ranking_items = [
#         html.Div(
#             id=f"leader-rank{i}",
#             className="leader-ranking",
#             children=[
#                 html.Div(str(row['rank']), className="leader-rank-col rank-left"),
#                 html.Div(str(row['UniversalPlayerID']), className="leader-rank-col rank-center"),
#                 html.Div(str(math.ceil(row['TP_Earning'])), className="leader-rank-col rank-right"),
#             ]
#         ) for i, row in top_17.iterrows()  
#     ]
    
#     return leader_details_value, ranking_items, date_str
# from dash import Output, Input, callback_context

# @callback(
#     Output('leader-dropdown', 'value'),
#     Input('leader-url', 'search')  # Use the URL to get PatronID
# )
# def determine_default_segment(search):
#     patron_id = None
#     if search:
#         parsed = parse_qs(search.lstrip('?'))
#         patron_id = Patron(parsed).get_om()  # Your PatronID extraction logic

#     if not patron_id:
#         return 'TG'  # Default fallback if no patron_id

#     now = datetime.now()
#     minute = (now.minute // 30) * 30
#     base_time = now.replace(minute=minute, second=0, microsecond=0)

#     def load_rank(segment):
#         for i in range(6):
#             attempt_time = base_time - timedelta(minutes=i*30)
#             timestamp = attempt_time.strftime("%Y-%m-%d_%H-%M-%S")
#             path = fr"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\pages\ios_chase_etl\files\{segment}_Leaderboards.csv"
#             if os.path.exists(path):
#                 try:
#                     df = pd.read_csv(path)
#                     # Find patron rank
#                     df_filtered = df[df['UniversalPlayerID'].str.strip() == patron_id.strip()]
#                     if not df_filtered.empty and 'rank' in df.columns:
#                         return int(df_filtered.iloc[0]['rank'])
#                 except Exception as e:
#                     print(f"Error reading file {path}: {e}")
#         return None

#     rank_eg = load_rank('EG')
#     rank_tg = load_rank('TG')

#     # Determine which has better rank (lower rank number is better)
#     if rank_eg is None and rank_tg is None:
#         return 'TG'  # default fallback
#     elif rank_eg is None:
#         return 'TG'
#     elif rank_tg is None:
#         return 'EG'
#     else:
#         return 'EG' if rank_eg < rank_tg else 'TG'

# @callback(
#     Output('leader-url', 'href'),
#     Input('leader-back-button', 'n_clicks')
# )
# def navigate_to_prev_page(n_clicks):
#     if not n_clicks:
#         return dash.no_update
#     return f'/top17tracker'
