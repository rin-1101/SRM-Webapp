"""
 CREDIT: This code is adapted for `pages`  based on Nader Elshehabi's  article:
   https://dev.to/naderelshehabi/securing-plotly-dash-using-flask-login-4ia2
   https://github.com/naderelshehabi/dash-flask-login

For other Authentication options see:
  Dash Enterprise:  https://dash.plotly.com/authentication#dash-enterprise-auth
  Dash Basic Auth:  https://dash.plotly.com/authentication#basic-auth

"""
# Secure Cookies
import secrets

def generate_session_id():
    session_id = secrets.token_hex(32)  # Generates a 32-character hex string
    return session_id


import os
from flask import Flask, request, redirect, session, jsonify

# NOTE: Werkzeug has to be pinned down to 2.3.0 as Flask made some braking changes
from flask_login import login_user, LoginManager, UserMixin, logout_user, current_user
from ldap3 import Server, Connection, ALL

import dash
from dash import dcc, html, Input, Output, State, ALL, Dash
from dash.exceptions import PreventUpdate

# Internal Imports
from utils.login_handler import restricted_page, ACCOUNTS
from ui.nav import nav_bar
from ui.footer import footer

# TO DO: Move to .env file and Install python dotenv so the values will be loaded there

os.environ["LDAP_SERVER"] = "int.okadamanila.com"
os.environ["SECRET_KEY"] = generate_session_id()


# Exposing the Flask Server to enable configuring it for logging in
server = Flask(__name__)

@server.route('/check-auth')
def check_auth():
    port = request.environ.get('SERVER_PORT')
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'port': port
    })

@server.before_request
def redirect_ip_to_domain():
    if request.host.startswith("10.36.21.60"):
        return redirect("https://srm.okadamanila.com:8050", code=301)
    
@server.after_request
def add_clickjacking_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'  # Or 'DENY'
    return response


@server.route("/login", methods=["POST"])
def login_button_click():
    if request.form:
        username = request.form["username"].lower()
        password = request.form["password"]

        ldap_server = Server(os.getenv("LDAP_SERVER"), use_ssl=True, get_info=ALL)
        conn = Connection(
            ldap_server,
            username + "@" + os.getenv("LDAP_SERVER"),
            password,
            auto_bind=False,
            raise_exceptions=False,
        )
        try:
            conn.bind()
            if conn.result["result"] == 0:  # Successful
                user = User(username)
                login_user(user)
                if "url" in session:
                    if session["url"]:
                        url = session["url"]
                        session["url"] = None
                        if url == "/":
                            return redirect("/home")  ## redirect to home url
                        else:
                            return redirect(url)
                    else:
                        return redirect("/home")

                return redirect("/home")  ## redirect to home
            elif conn.result["result"] == 49:  # Invalid credentials
                return """Invalid username and/or password <a href='/login'>login here</a>"""
        except Exception as e:
            return (
                """Invalid username and/or password <a href='/login'>login here</a>"""
            )
        finally:
            if conn.bound:
                conn.unbind()


app = Dash(__name__, server=server, use_pages=True, suppress_callback_exceptions=True)

# Updating the Flask Server configuration with Secret Key to encrypt the user session cookie
server.config.update(SECRET_KEY=generate_session_id())
server.config['SESSION_COOKIE_NAME'] = 'sessionSM'
server.config["SESSION_COOKIE_HTTPONLY"] = True
server.config['SESSION_COOKIE_SECURE'] = True
server.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Login manager object will be used to login / logout users
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


class User(UserMixin):
    # User data model. It has to have at least self.id as a minimum
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    """
    This function loads the user by user id. Typically this looks up the user from a user database.
    We won't be registering or looking up users in this example, since we'll just login using LDAP server.
    So we'll simply return a User object with the passed in username.
    """
    return User(username)


app.layout = html.Div(
    [
        html.Nav(
            id="nav-main",  # Added ID to the navbar
            className="navbar is-white has-shadow",
            children=[
                nav_bar
            ]
        ),
        # runs the entire page.
        dcc.Location(id="url"),
        html.Div(
            html.Div(dash.page_container),
            style={
                "overflowX": "auto", 
                "whiteSpace": "nowrap", 
                "margin": "0 !important", 
                "padding": "0 !important",
                # "paddingTop": "60px"  # Adjust this padding value based on the height of your navbar
            },
        ),
    ]
)


@app.callback(
    Output("login-status", "children"),
    Input("url", "pathname"),
    Input({"index": ALL, "type": "redirect"}, "n_intervals"),
)
def update_authentication_status(path, n):
    if current_user.is_authenticated:
        return dcc.Link("Logout", href="/logout")
    else:
        return dcc.Link("Login", href="/login")

@app.callback(
    Output('nav-main', 'className'),
    Input('url', 'pathname')  # Trigger callback on URL change
)
def on_page_load(pathname):
    if "raffle" in pathname:
        return "invisible"
    return ""
# testssl (file://OMPYTSRVD00001V/testssl)
CERT_PATH = f"\\\\OMPYTSRVD00001V\\testssl"


if __name__ == "__main__":
    app.run_server(
        debug=False,
        host="0.0.0.0",
        port=5000,
        ssl_context=(f"{CERT_PATH}\\wildcard_okadamanila_com.pem", f"{CERT_PATH}\\wildcard_okadamanila_com_key.pem"),
    )
