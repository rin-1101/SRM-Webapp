"""Reusable CSV entitlement checker page."""

from io import StringIO

import dash
import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html
from flask_login import current_user

from utils.login_handler import has_access


class EntitlementConfig(object):
    def __init__(
        self,
        suffix,
        page_path,
        access_level,
        whitelist_path,
        default_map_columns=None,
        fetch_columns=None,
        title="Entitlement Checker",
        search_label="Patron ID",
        search_placeholder="Enter OM Number",
        logger=None,
        dev=False
    ):
        self.suffix = suffix
        self.page_path = page_path
        self.access_level = access_level
        self.whitelist_path = whitelist_path
        self.default_map_columns = list(default_map_columns or ["UniversalPlayerID"])
        self.fetch_columns = list(fetch_columns or ["Prizes"])
        self.title = title
        self.search_label = search_label
        self.search_placeholder = search_placeholder
        self.logger = logger
        self.isdev = dev

        required = ["suffix", "page_path", "whitelist_path"]
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError("EntitlementConfig missing required field(s): {}".format(", ".join(missing)))


class EntitlementPage(object):
    def __init__(self, config):
        self.config = config
        self.suffix = config.suffix

    def id(self, name):
        return "{}-{}".format(name, self.suffix)

    @staticmethod
    def _split_columns(value):
        if isinstance(value, (list, tuple)):
            raw = value
        else:
            raw = str(value or "").replace(";", ",").split(",")
        return [str(col).strip() for col in raw if str(col).strip()]

    @staticmethod
    def _format_om(value):
        if value is None:
            return ""
        text = str(value).strip().upper()
        if text.startswith("OM"):
            digits = "".join(ch for ch in text[2:] if ch.isdigit())
        else:
            digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            return text
        return "OM{}".format(digits[-9:].zfill(9))

    @classmethod
    def _normalize_value(cls, value, column_name):
        text = "" if pd.isna(value) else str(value).strip()
        column_key = str(column_name or "").replace("_", "").replace(" ", "").lower()
        if column_key in ("universalplayerid", "uid", "om", "omnumber", "patronid"):
            return cls._format_om(text)
        return text.upper()

    @staticmethod
    def _column_key(value):
        return str(value or "").strip().lower()

    @classmethod
    def _resolve_columns(cls, df, requested):
        lookup = {cls._column_key(col): col for col in df.columns}
        singular_lookup = {}
        for key, column in lookup.items():
            if key.endswith("s"):
                singular_lookup.setdefault(key[:-1], column)
            else:
                singular_lookup.setdefault(key, column)

        resolved = []
        missing = []
        for column in requested:
            key = cls._column_key(column)
            singular_key = key[:-1] if key.endswith("s") else key
            if key in lookup:
                resolved.append(lookup[key])
            elif singular_key in singular_lookup:
                resolved.append(singular_lookup[singular_key])
            else:
                missing.append(column)
        return resolved, missing

    def read_whitelist(self):
        return pd.read_csv(self.config.whitelist_path, dtype=str).fillna("")

    def check_entitlement(self, search_value, map_columns, fetch_columns=None):
        df = self.read_whitelist()
        requested_map_columns = self._split_columns(map_columns) or list(self.config.default_map_columns)
        requested_fetch_columns = self._split_columns(fetch_columns) or list(self.config.fetch_columns)

        resolved_map, missing_map = self._resolve_columns(df, requested_map_columns)
        resolved_fetch, missing_fetch = self._resolve_columns(df, requested_fetch_columns)
        if missing_map or missing_fetch:
            missing = missing_map + missing_fetch
            raise KeyError("Missing column(s): {}".format(", ".join(missing)))

        masks = []
        for column in resolved_map:
            needle = self._normalize_value(search_value, column)
            haystack = df[column].apply(lambda value: self._normalize_value(value, column))
            masks.append(haystack == needle)

        if not masks:
            return pd.DataFrame(columns=resolved_map + resolved_fetch)

        combined = masks[0]
        for mask in masks[1:]:
            combined = combined | mask

        display_columns = []
        for column in resolved_map + resolved_fetch:
            if column not in display_columns:
                display_columns.append(column)

        return df.loc[combined, display_columns].reset_index(drop=True)

    def make_table(self, df):
        if df is None or df.empty:
            return html.P("No entitlement found.", className="has-text-grey is-size-7")

        return dash_table.DataTable(
            columns=[{"name": column, "id": column} for column in df.columns],
            data=df.to_dict("records"),
            page_size=10,
            sort_action="native",
            style_table={"overflowX": "auto", "maxWidth": "100%"},
            style_header={
                "backgroundColor": "#2c3e50",
                "color": "white",
                "fontWeight": "bold",
                "textAlign": "center",
            },
            style_cell={
                "textAlign": "center",
                "padding": "6px 10px",
                "minWidth": "140px",
                "width": "160px",
                "maxWidth": "280px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f5f7fa"},
            ],
        )

    def layout(self):
        if self.config.isdev:
            return self._layout()
        if current_user.is_authenticated and has_access(current_user, self.config.page_path):
            if self.config.logger:
                self.config.logger.info("{} has accessed".format(current_user.id))
            return self._layout()
        return html.Div(["No Access!"])

    def _layout(self):
        cfg = self.config
        return html.Div(
            className="container",
            children=[
                html.H1(cfg.title, className="title has-text-centered mb-5"),
                html.Div(
                    className="box",
                    children=[
                        html.Div(
                            className="columns is-centered",
                            children=[
                                html.Div(
                                    className="column is-half",
                                    children=[
                                        html.Label(cfg.search_label, className="label has-text-centered"),
                                        dcc.Input(
                                            id=self.id("search-value"),
                                            type="text",
                                            placeholder=cfg.search_placeholder,
                                            className="input",
                                            debounce=True,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="has-text-centered mt-4",
                            children=[
                                html.Div(
                                    children=[
                                        html.Span(id=self.id("status"), className="is-size-7"),
                                    ],
                                    style={"marginBottom": "0.5rem"},
                                ),
                                html.Button("Check Entitlement", id=self.id("submit"), className="button is-primary", n_clicks=0),
                            ],
                        ),
                    ],
                ),
                dcc.Store(id=self.id("result-store")),
                dcc.Download(id=self.id("download")),
                dcc.Loading(html.Div(id=self.id("result"))),
            ],
        )

    def register_callbacks(self):
        id_ = self.id

        @callback(
            Output(id_("result"), "children"),
            Output(id_("result-store"), "data"),
            Output(id_("status"), "children"),
            Input(id_("submit"), "n_clicks"),
            State(id_("search-value"), "value"),
            prevent_initial_call=True,
        )
        def check_entitlement(n_clicks, search_value):
            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update
            if not str(search_value or "").strip():
                return "", None, html.Span("Enter a value to check.", className="has-text-warning")

            try:
                df = self.check_entitlement(search_value, self.config.default_map_columns, self.config.fetch_columns)
                stored_data = df.to_json(date_format="iso", orient="records")
                status = html.Span("{} matching row(s).".format(len(df)), className="has-text-success")
                children = [self.make_table(df)]
                return html.Div(children), stored_data, status
            except Exception as exc:
                return "", None, html.Span("Error: {}".format(exc), className="has-text-danger")

        # @callback(
        #     Output(id_("download"), "data"),
        #     Input(id_("export"), "n_clicks"),
        #     State(id_("result-store"), "data"),
        #     prevent_initial_call=True,
        # )
        # def export_entitlement(n_clicks, stored_data):
        #     if n_clicks and stored_data:
        #         df = pd.read_json(StringIO(stored_data), orient="records")
        #         return dcc.send_data_frame(df.to_csv, filename="entitlement_results.csv", index=False)
        #     return dash.no_update