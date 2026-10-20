"""Reusable CSV-backed raffle-entry checker page."""

from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import dash
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from flask_login import current_user

from utils.login_handler import has_access


_MONTH_LABELS = (
    "",
    "Jan",
    "Feb",
    "March",
    "April",
    "May",
    "June",
    "July",
    "Aug",
    "Sept",
    "Oct",
    "Nov",
    "Dec",
)


def saturday_raffle_entry_label(now=None, timezone_name="Asia/Manila"):
    """Return the active Saturday draw label after the Friday 06:00 rollover."""
    timezone = ZoneInfo(timezone_name)
    if now is None:
        local_now = datetime.now(timezone)
    elif now.tzinfo is None:
        local_now = now.replace(tzinfo=timezone)
    else:
        local_now = now.astimezone(timezone)

    friday_date = local_now.date() - timedelta(
        days=(local_now.weekday() - 4) % 7
    )
    friday_rollover = datetime.combine(
        friday_date,
        time(hour=6),
        tzinfo=timezone,
    )
    if local_now < friday_rollover:
        friday_rollover -= timedelta(days=7)

    raffle_date = friday_rollover.date()
    return "Entitled Entries for {} {}".format(
        _MONTH_LABELS[raffle_date.month],
        raffle_date.day,
    )


class RaffleEntriesConfig(object):
    """Configuration for one patron-facing raffle-entry checker."""

    def __init__(
        self,
        suffix,
        page_path,
        access_level,
        entries_csv_path,
        title="Raffle Entries Checker",
        subtitle="Enter your patron ID to view your entitled raffle entries.",
        search_placeholder="Enter OM Number",
        user_id_column="UniversalPlayerID",
        name_column="Name",
        entries_column="Entries",
        entry_label="ENTITLED RAFFLE ENTRIES",
        entry_label_provider=None,
        logo_src=None,
        background_src=None,
        logger=None,
        dev=False,
    ):
        self.suffix = suffix
        self.page_path = page_path
        self.access_level = access_level
        self.entries_csv_path = Path(entries_csv_path)
        self.title = title
        self.subtitle = subtitle
        self.search_placeholder = search_placeholder
        self.user_id_column = user_id_column
        self.name_column = name_column
        self.entries_column = entries_column
        self.entry_label = entry_label
        self.entry_label_provider = entry_label_provider
        self.logo_src = logo_src
        self.background_src = background_src
        self.logger = logger
        self.isdev = bool(dev)

        required = (
            "suffix",
            "page_path",
            "entries_csv_path",
            "user_id_column",
            "name_column",
            "entries_column",
        )
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError(
                "RaffleEntriesConfig missing required field(s): {}".format(
                    ", ".join(missing)
                )
            )


class RaffleEntriesPage(object):
    """Render and operate a user-ID lookup against a raffle entries CSV."""

    def __init__(self, config):
        self.config = config
        self.suffix = config.suffix

    def id(self, name):
        return "{}-{}".format(name, self.suffix)

    @staticmethod
    def normalize_user_id(value):
        """Normalize numeric or OM-prefixed input to the standard OM format."""
        text = str(value or "").strip().upper()
        if not text:
            return ""

        compact = "".join(character for character in text if character.isalnum())
        candidate = compact[2:] if compact.startswith("OM") else compact
        if candidate.isdigit():
            return "OM{}".format(candidate[-9:].zfill(9))
        return compact

    @staticmethod
    def _column_key(value):
        return str(value or "").lstrip("\ufeff").strip().casefold()

    def _resolve_column(self, dataframe, requested_column):
        columns = {
            self._column_key(column): column
            for column in dataframe.columns
        }
        resolved = columns.get(self._column_key(requested_column))
        if resolved is None:
            raise KeyError("Missing column: {}".format(requested_column))
        return resolved

    def read_entries(self):
        """Read the current CSV so file replacements are visible immediately."""
        dataframe = pd.read_csv(
            self.config.entries_csv_path,
            dtype=str,
            encoding="utf-8-sig",
        )
        return dataframe.fillna("")

    def lookup_entries(self, user_id):
        """Return patron identity and entitled-entry total, or ``None``."""
        normalized_user_id = self.normalize_user_id(user_id)
        if not normalized_user_id:
            return None

        dataframe = self.read_entries()
        user_id_column = self._resolve_column(
            dataframe, self.config.user_id_column
        )
        name_column = self._resolve_column(dataframe, self.config.name_column)
        entries_column = self._resolve_column(
            dataframe, self.config.entries_column
        )

        normalized_values = dataframe[user_id_column].map(self.normalize_user_id)
        matches = dataframe.loc[normalized_values == normalized_user_id]
        if matches.empty:
            return None

        entry_values = pd.to_numeric(
            matches[entries_column].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )
        if entry_values.isna().any():
            raise ValueError(
                "Invalid raffle entry value for {}".format(normalized_user_id)
            )

        total_entries = float(entry_values.sum())
        display_entries = (
            str(int(total_entries))
            if total_entries.is_integer()
            else "{:g}".format(total_entries)
        )
        names = [
            str(value).strip()
            for value in matches[name_column]
            if str(value).strip()
        ]
        return {
            "user_id": normalized_user_id,
            "name": names[0] if names else "Patron",
            "entries": display_entries,
        }

    def layout(self):
        if self.config.isdev:
            return self._layout()
        if current_user.is_authenticated and has_access(
            current_user, self.config.page_path
        ):
            if self.config.logger:
                self.config.logger.info("%s has accessed", current_user.id)
            return self._layout()
        return self._layout()
        # return html.Div(["No Access!"])

    def _layout(self):
        cfg = self.config
        background_style = {}
        if cfg.background_src:
            background_style = {
                "backgroundImage": (
                    "linear-gradient(rgba(3, 10, 20, 0.52), "
                    "rgba(3, 10, 20, 0.76)), url(\"{}\")"
                ).format(cfg.background_src)
            }
        return html.Div(
            id=self.id("main-container"),
            className="raffle-entries-page",
            style=background_style,
            children=[
                html.Link(
                    rel="stylesheet",
                    href="/assets/raffle-entries/style.css",
                ),
                dcc.Interval(
                    id=self.id("entry-label-refresh"),
                    interval=60 * 1000,
                    n_intervals=0,
                ) if cfg.entry_label_provider else None,
                html.A("Refresh", href=cfg.page_path, className="rfe-refresh"),
                html.Main(
                    className="rfe-shell",
                    children=[
                        html.Header(
                            className="rfe-page-header",
                            children=[
                                html.Span("RAFFLE ENTRIES", className="rfe-kicker"),
                                html.H1(
                                    cfg.title,
                                    className=(
                                        "rfe-visually-hidden"
                                        if cfg.logo_src
                                        else "rfe-page-title"
                                    ),
                                ),
                                html.Img(
                                    src=cfg.logo_src,
                                    alt=cfg.title,
                                    className="rfe-page-logo",
                                ) if cfg.logo_src else None,
                                html.P(cfg.subtitle, className="rfe-page-subtitle"),
                            ],
                        ),
                        html.Section(
                            className="rfe-member-card",
                            children=[
                                html.Div(
                                    className="rfe-card-heading",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.Span("MEMBER", className="rfe-kicker"),
                                                html.H2(
                                                    "Find your raffle entries",
                                                    className="rfe-section-title",
                                                ),
                                            ]
                                        ),
                                        html.Span(
                                            "CURRENT RAFFLE LIST",
                                            className="rfe-current-badge",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="rfe-search-row",
                                    children=[
                                        dcc.Input(
                                            id=self.id("user-id"),
                                            type="text",
                                            placeholder=cfg.search_placeholder,
                                            className="rfe-search-input",
                                            autoComplete="off",
                                            debounce=False,
                                            n_submit=0,
                                        ),
                                        html.Button(
                                            "Check",
                                            id=self.id("check-button"),
                                            n_clicks=0,
                                            className="rfe-primary-button",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id=self.id("status"),
                                    className="rfe-status",
                                    role="status",
                                ),
                            ],
                        ),
                        dcc.Loading(
                            type="circle",
                            children=html.Section(
                                id=self.id("result"),
                                className="rfe-result-card",
                                style={"display": "none"},
                                children=[
                                    html.Div(
                                        className="rfe-result-heading",
                                        children=[
                                            html.Span(
                                                "ELIGIBLE PATRON",
                                                className="rfe-kicker",
                                            ),
                                            html.H2(
                                                id=self.id("patron-name"),
                                                className="rfe-patron-name",
                                            ),
                                            html.P(
                                                id=self.id("patron-id"),
                                                className="rfe-patron-id",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="rfe-entry-metric",
                                        children=[
                                            html.Span(
                                                (
                                                    cfg.entry_label_provider()
                                                    if cfg.entry_label_provider
                                                    else cfg.entry_label
                                                ),
                                                id=self.id("entry-label"),
                                                className="rfe-entry-label",
                                            ),
                                            html.Strong(
                                                id=self.id("entry-count"),
                                                className="rfe-entry-count",
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        "Entries are refreshed every hour.",
                                        className="rfe-result-note",
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        )

    def register_callbacks(self):
        id_ = self.id

        if self.config.entry_label_provider:
            @callback(
                Output(id_("entry-label"), "children"),
                Input(id_("entry-label-refresh"), "n_intervals"),
            )
            def refresh_entry_label(_interval_count):
                return self.config.entry_label_provider()

        @callback(
            Output(id_("patron-name"), "children"),
            Output(id_("patron-id"), "children"),
            Output(id_("entry-count"), "children"),
            Output(id_("result"), "style"),
            Output(id_("status"), "children"),
            Output(id_("status"), "className"),
            Input(id_("check-button"), "n_clicks"),
            Input(id_("user-id"), "n_submit"),
            State(id_("user-id"), "value"),
            prevent_initial_call=True,
        )
        def check_entries(button_clicks, enter_presses, user_id):
            if not button_clicks and not enter_presses:
                return (dash.no_update,) * 6

            if not str(user_id or "").strip():
                return (
                    "", "", "", {"display": "none"},
                    "Enter a patron ID to check.",
                    "rfe-status is-warning",
                )

            normalized_user_id = self.normalize_user_id(user_id)
            try:
                result = self.lookup_entries(user_id)
            except Exception:
                if self.config.logger:
                    self.config.logger.exception(
                        "Unable to check raffle entries for %s",
                        normalized_user_id,
                    )
                return (
                    "", "", "", {"display": "none"},
                    "Raffle entries are currently unavailable. Please contact the event team.",
                    "rfe-status is-error",
                )

            if result is None:
                return (
                    "", "", "", {"display": "none"},
                    "No raffle entries found for {}.".format(normalized_user_id),
                    "rfe-status is-warning",
                )

            return (
                result["name"],
                result["user_id"],
                result["entries"],
                {"display": "grid"},
                "Raffle entries found.",
                "rfe-status is-success",
            )


__all__ = [
    "RaffleEntriesConfig",
    "RaffleEntriesPage",
    "saturday_raffle_entry_label",
]