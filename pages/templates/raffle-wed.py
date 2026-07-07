# import dash
# import random
# import pandas as pd
# import sys
# from dash import Dash, dcc, html, dash_table, Input, Output, State, callback, ctx


# from utils.paths import WED_RAFFLE
# # Authentication Imports
# from flask_login import current_user
# from utils.login_handler import require_login, has_access, restricted_page


# ## Raflfe import
# ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
# sys.path.append(f"{ROOT}\\okada\\")
# sys.path.append(f"{ROOT}\\reports\\pages\\")
# from raffle_etl.raffle import Raffle_app
# from raffle_etl.shareddata import get_data

# raffle = Raffle_app()


# ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
# sys.path.append(f"{ROOT}\\okada\\")
# from okada import SQL
# from okada import LogServiceDaily

# logger = LogServiceDaily("win-wed").get_logger()



# # ----------------------------------------------------------------
# # Page registration
# # ----------------------------------------------------------------
# dash.register_page(__name__, path=WED_RAFFLE)
# require_login(__name__, access_level=restricted_page[WED_RAFFLE]["access_level"])

# # ----------------------------------------------------------------
# # Layout
# # ----------------------------------------------------------------

# def layout():
#     return html.Div([
#         html.Link(rel='stylesheet', href='/assets/raffle/raffle.css'),
        
#         dcc.Interval(
#             id='interval-component',
#             interval=1000, 
#             n_intervals=0
#         ),
#         dcc.Location(id='url-wed', refresh=False),  # to track URL changes or page load
#         dcc.Store(id='animation-store', data={'animating': False, 'timestamp': 0}),
        
#         dcc.Interval(
#             id='animation-interval',
#             interval=100,  
#             n_intervals=0,
#             disabled=True
#         ),
        
#         html.Div(  
#             id="container-div-wed",
#             className="columns is-centered is-vcentered is-flex-direction-column", 
#             children=[
                
#                 # Logo
#                 html.Div(
#                     style={"text-align": "center"},
#                     children=[
#                         html.Img(
#                             id="logo-main-ctc",
#                             src="/assets/raffle/wed-raffle-logo.png",
#                             style={
#                                 "height": "300px",
#                                 "width": "auto",
#                                 "max-width": "100%",
#                                 "object-fit": "contain",
#                             }
#                         )
#                     ]
#                 ),
                
#                 html.Div(  
#                     id="details-wed",
#                     className="column is-12 has-text-centered",  
#                     children=[
#                         html.Div(id="date-display"),
#                         html.Div(id="time-display"),
#                     ]
#                 ),
#                 html.Div(
#                     id="subdetails-wed",
#                     className = "raffle-font",
#                     children = [
#                         html.Div(
#                             id="prize-container-wed",
#                             className="columns is-gapless",  # This removes the gap between the columns
#                             children=[
#                                 html.Div(  
#                                     id="prize-php-wed",
#                                     className="column is-4 has-text-right",  # Column size stays the same
#                                     children=[
#                                         html.Img(
#                                             id="logo-main-ctc",
#                                             src=f"/assets/raffle/wed-raffle/Prizes/PHP.png",
#                                             style={
#                                                 "height": "150px",
#                                                 "width": "auto",
#                                                 "max-width": "100%",
#                                                 "object-fit": "contain",
#                                             }
#                                         ),
#                                     ]
#                                 ),
#                                 html.Div(  
#                                     id="prize-wed",
#                                     className="column is-4 has-text-centered",  # Column size stays the same
#                                     children=[
#                                         html.P(id="prize-display", className="subtitle is-5") 
#                                     ]
#                                 ),
#                                 html.Div(  
#                                     id="prize-worth-wed",
#                                     className="column is-4 has-text-left",  # Column size stays the same
#                                     children=[
#                                         html.Img(
#                                             id="logo-main-ctc",
#                                             src=f"/assets/raffle/wed-raffle/Prizes/WORTH.png",
#                                             style={
#                                                 "height": "150px",
#                                                 "width": "auto",
#                                                 "max-width": "100%",
#                                                 "object-fit": "contain",
#                                             }
#                                         ),
#                                     ]
#                                 ),
#                             ]
#                         ),

                        
#                         html.Div( 
#                             id="result-wed",
#                             className="column is-12 has-text-centered", 
#                             children=[
#                                 html.Div(  
#                                     id="uid-wed",
#                                     className="has-text-centered slot-machine raffle-font",
#                                     children=['Draw is about to Begin']  
#                                 ),
                                
#                                 html.Div( 
#                                     id="initials-wed",
#                                     className="has-text-centered slot-machine raffle-font",
#                                     children=['']  
#                                 )
#                             ]
#                         )
#                     ]
#                 )
                
#             ]
#         )
#     ])


# @callback(
#     [Output('animation-store', 'data'),
#      Output('animation-interval', 'disabled')],
#     Input('interval-component', 'n_intervals'),
#     prevent_initial_call=False
# )
# def check_for_animation_trigger(n):
#     data = get_data('win_it_wednesday')
#     current_time = data.get('animation_timestamp', 0)
    
#     import time
#     if current_time > time.time() - 5:  
#         return {'animating': True, 'timestamp': current_time}, False
    
#     return {'animating': False, 'timestamp': 0}, True

# @callback(
#     [Output('uid-wed', 'children'),
#      Output('initials-wed', 'children'),
#      Output('uid-wed', 'className')],
#     [Input('animation-interval', 'n_intervals'),
#      Input('interval-component', 'n_intervals')],
#     prevent_initial_call=False
# )
# def update_frontend(anim_n, update_n):
#     import random
#     from dash import ctx
#     from pathlib import Path
    
#     data = get_data('win_it_wednesday')
    
#     import time
#     animation_time = data.get('animation_timestamp', 0)
#     is_animating = animation_time > time.time() - 3  
    
#     if is_animating and (data['uid'] != 'Draw is about to Begin' and  data['uid'] != "Next Draw at 10PM" ):
#         try:
#             uid_temp, initials_temp  = raffle.draw_animate()
#             random_uid = uid_temp
#             random_initials = initials_temp
#         except:
#             random_uid = data['uid']
#             random_initials = data['initials']
            
#         return (random_uid, random_initials,  
#                 "has-text-centered slot-machine raffle-font animating")
#     else:
#         return (data['uid'], data['initials'],  
#                 "has-text-centered slot-machine raffle-font")

# @callback(
#     Output('date-display', 'children'),
#     Output('time-display', 'children'),
#     Output('prize-wed', 'children'),
#     Input('interval-component', 'n_intervals')
# )
# def update_date(n):
#     data = get_data('win_it_wednesday')
#     date_text = html.Img(
#                 id="logo-main-ctc",
#                 src=f"/assets/raffle/wed-raffle/Dates/{data['date']}.png",
#                 style={
#                     "height": "80px",
#                     "width": "auto",
#                     "max-width": "100%",
#                     "object-fit": "contain",
#                     }
#                 ),
#     time_text = html.Img(
#                 id="logo-main-ctc",
#                 src=f"/assets/raffle/wed-raffle/Time/{data['time']}.png",
#                 style={
#                     "height": "80px",
#                     "width": "auto",
#                     "max-width": "100%",
#                     "object-fit": "contain",
#                     }
#                 )

#     prize_text = html.Img(
#                 id="logo-main-ctc",
#                 src=f"/assets/raffle/wed-raffle/Prizes/{data['prize']}.png",
#                 style={
#                     # "height": "150px",
#                     "width": "auto",
#                     "max-width": "100%",
#                     "object-fit": "contain",
#                     }
#                 ),
#     return date_text, time_text, prize_text

# """

# #nav-main {
#     position: fixed;        /* Fixes the navbar to the top of the page */
#     top: 0;
#     left: 0;
#     width: 100%;            /* Full width */
#     opacity: 0;
#     visibility: visible;
#     height: auto;
#     transition: opacity 0.3s ease-in-out, visibility 0.3s ease-in-out, height 0.3s ease-in-out;
#     z-index: 1000;          /* Ensures the navbar stays on top of other content */
# }

# #nav-main:hover {
#     opacity: 1;
#     visibility: visible;
#     height: auto;
# }
# """