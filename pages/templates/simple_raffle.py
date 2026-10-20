"""Reusable one-page raffle with drawing, reset, and persistent history."""

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from threading import Lock

import dash
import yaml
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from .raffle import Raffle


class WinnerHistoryFile(object):
    """Persist winner history independently from replaceable entry files."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self._lock = Lock()

    def _read_unlocked(self):
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            records = json.load(file)
        if not isinstance(records, list):
            raise ValueError(
                "Winner history must contain a list: {}".format(self.file_path)
            )
        return records

    def read(self):
        with self._lock:
            return self._read_unlocked()

    def add(self, user_id, name, prize=None):
        return self.add_many([(user_id, name, prize)])[0]

    def add_many(self, winners):
        """Commit a complete batch in one atomic history replacement."""
        with self._lock:
            records = self._read_unlocked()
            draw_number = max(
                [int(record.get("draw_number", 0)) for record in records] or [0]
            ) + 1
            added = []
            for user_id, name, prize in winners:
                record = {
                    "draw_number": draw_number,
                    "uid": str(user_id),
                    "name": str(name),
                    "drawn_at": datetime.now().isoformat(timespec="seconds"),
                }
                if prize is not None:
                    record["prize"] = str(prize)
                added.append(record)
                draw_number += 1
            records.extend(added)
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(records, file, indent=4)
            temp_path.replace(self.file_path)
            return added

    def clear(self):
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.file_path.with_suffix(
                self.file_path.suffix + ".tmp"
            )
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
            temp_path.replace(self.file_path)


class SimpleRaffleConfig(object):
    """Configuration for a minimal CSV-backed raffle page."""

    def __init__(
        self,
        suffix,
        page_path,
        access_level,
        entries_csv_path,
        history_file_path,
        title="Raffle",
        button_label="Draw Raffle",
        initial_message="Press the button to draw a winner.",
        stylesheet_href="/assets/simple-raffle/style.css",
        event_name=None,
        logger=None,
        prize_enabled=False,
        prize_options_path=None,
        export_enabled=False,
    ):
        self.suffix = suffix
        self.page_path = page_path
        self.access_level = access_level
        self.entries_csv_path = Path(entries_csv_path)
        self.history_file_path = Path(history_file_path)
        self.title = title
        self.button_label = button_label
        self.initial_message = initial_message
        self.stylesheet_href = stylesheet_href
        self.event_name = event_name or self.entries_csv_path.stem
        self.logger = logger
        self.prize_enabled = bool(prize_enabled)
        self.prize_options_path = (
            Path(prize_options_path) if prize_options_path else None
        )
        self.export_enabled = bool(export_enabled)

        required = (
            "suffix",
            "page_path",
            "entries_csv_path",
            "history_file_path",
            "title",
            "event_name",
        )
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError(
                "SimpleRaffleConfig missing required field(s): {}".format(
                    ", ".join(missing)
                )
            )


class SimpleRafflePage(object):
    """Render and operate a minimal raffle using the shared raffle engine."""

    def __init__(self, config, raffle=None, history=None):
        self.config = config
        self.raffle = raffle or Raffle(data_path=config.entries_csv_path.parent)
        self.history = history or WinnerHistoryFile(config.history_file_path)

    def id(self, name):
        return "{}-{}".format(name, self.config.suffix)

    def _history_rows(self):
        column_count = len(self._history_headers())
        try:
            winners = self.history.read()
        except Exception:
            if self.config.logger:
                self.config.logger.exception(
                    "Unable to load winner history from %s",
                    self.config.history_file_path,
                )
            return [
                html.Tr(
                    html.Td(
                        "Winner history is unavailable.",
                        colSpan=column_count,
                        className="simple-raffle-history-empty",
                    )
                )
            ]

        if not winners:
            return [
                html.Tr(
                    html.Td(
                        "No winners yet.",
                        colSpan=column_count,
                        className="simple-raffle-history-empty",
                    )
                )
            ]

        rows = []
        for record in winners:
            cells = [
                html.Td(int(record["draw_number"])),
                html.Td(str(record["uid"])),
                html.Td(str(record["name"])),
            ]
            if self.config.prize_enabled:
                cells.extend(self._prize_cells(record))
            cells.append(html.Td(str(record["drawn_at"]).replace("T", " ")))
            rows.append(html.Tr(children=cells))
        return rows

    def _action_buttons(self):
        cfg = self.config
        buttons = [
            html.Button(
                cfg.button_label,
                id=self.id("draw-button"),
                n_clicks=0,
                className="simple-raffle-button",
            ),
            html.Button(
                "Reset Entries",
                id=self.id("reset-button"),
                n_clicks=0,
                className="simple-raffle-button is-reset",
            ),
            html.Button(
                "Reset History",
                id=self.id("reset-history-button"),
                n_clicks=0,
                className="simple-raffle-button is-reset",
            ),
        ]
        if cfg.export_enabled:
            buttons.append(
                html.Button(
                    "Export Results",
                    id=self.id("export-button"),
                    n_clicks=0,
                    className="simple-raffle-button is-export",
                )
            )
        return buttons

    def _prize_options(self):
        path = self.config.prize_options_path
        if path is None:
            return []

        try:
            with path.open("r", encoding="utf-8") as file:
                document = yaml.safe_load(file) or {}
            prizes = document.get("prizes", []) if isinstance(document, dict) else []
            if not isinstance(prizes, list):
                raise ValueError("The prizes value must be a list")
            return [
                str(prize).strip()
                for prize in prizes
                if str(prize).strip()
            ]
        except Exception:
            if self.config.logger:
                self.config.logger.exception(
                    "Unable to load raffle prizes from %s",
                    path,
                )
            return []

    def _prize_control(self):
        if self.config.prize_options_path:
            prizes = self._prize_options()
            return dcc.Dropdown(
                id=self.id("prize-input"),
                options=[{"label": prize, "value": prize} for prize in prizes],
                value=None,
                placeholder="Select a prize",
                clearable=True,
                className="simple-raffle-prize-dropdown",
            )

        return dcc.Input(
            id=self.id("prize-input"),
            type="text",
            value="",
            placeholder="Enter the prize",
            className="simple-raffle-prize-input",
        )

    def _prize_cells(self, record):
        return [html.Td(str(record.get("prize", "")))]

    def _prize_headers(self):
        return [html.Th("Prize", scope="col")]

    def _history_headers(self):
        headers = [
            html.Th("Draw", scope="col"),
            html.Th("OM ID", scope="col"),
            html.Th("Name", scope="col"),
        ]
        if self.config.prize_enabled:
            headers.extend(self._prize_headers())
        headers.append(html.Th("Drawn At", scope="col"))
        return headers

    def layout(self):
        cfg = self.config
        return html.Div(
            id=self.id("page"),
            className="simple-raffle-page",
            children=[
                html.Link(rel="stylesheet", href=cfg.stylesheet_href),
                html.Main(
                    className="simple-raffle-shell",
                    children=[
                        html.Header(
                            className="simple-raffle-header",
                            children=[
                                html.P("RAFFLE DRAW", className="simple-raffle-kicker"),
                                html.H1(cfg.title, className="simple-raffle-title"),
                            ],
                        ),
                        html.Div(
                            id=self.id("prize-field"),
                            className=(
                                "simple-raffle-prize-field"
                                if cfg.prize_enabled
                                else "simple-raffle-prize-field is-hidden"
                            ),
                            children=[
                                html.Label(
                                    "Prize",
                                    htmlFor=self.id("prize-input"),
                                    className="simple-raffle-prize-label",
                                ),
                                self._prize_control(),
                            ],
                        ),
                        html.Div(
                            className="simple-raffle-actions",
                            children=self._action_buttons(),
                        ),
                        dcc.Download(id=self.id("results-download")),
                        dcc.Loading(
                            type="circle",
                            children=html.Section(
                                id=self.id("result"),
                                className="simple-raffle-result is-empty",
                                **{"aria-live": "polite"},
                                children=[
                                    html.P(
                                        "Raffle Result",
                                        id=self.id("result-label"),
                                        className="simple-raffle-result-label",
                                    ),
                                    html.Strong(
                                        "-",
                                        id=self.id("winner-id"),
                                        className="simple-raffle-winner-id",
                                    ),
                                    html.P(
                                        cfg.initial_message,
                                        id=self.id("winner-name"),
                                        className="simple-raffle-winner-name",
                                    ),
                                ],
                            ),
                        ),
                        html.Section(
                            className="simple-raffle-history",
                            children=[
                                html.H2(
                                    "Winner History",
                                    className="simple-raffle-history-title",
                                ),
                                html.Div(
                                    className="simple-raffle-history-table-wrap",
                                    children=html.Table(
                                        className="simple-raffle-history-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        *self._history_headers(),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id=self.id("history-body"),
                                                children=self._history_rows(),
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def register_callbacks(self):
        cfg = self.config
        id_ = self.id

        callback_args = [
            Output(id_("result-label"), "children"),
            Output(id_("winner-id"), "children"),
            Output(id_("winner-name"), "children"),
            Output(id_("result"), "className"),
            Output(id_("history-body"), "children"),
            Input(id_("draw-button"), "n_clicks"),
            Input(id_("reset-button"), "n_clicks"),
            Input(id_("reset-history-button"), "n_clicks"),
        ]
        if cfg.prize_enabled:
            callback_args.append(State(id_("prize-input"), "value"))

        @callback(*callback_args, prevent_initial_call=True)
        def handle_raffle_action(
            draw_clicks,
            reset_clicks,
            reset_history_clicks,
            prize=None,
        ):
            if not draw_clicks and not reset_clicks and not reset_history_clicks:
                return (dash.no_update,) * 5

            if dash.ctx.triggered_id == id_("reset-history-button"):
                try:
                    self.history.clear()
                except Exception:
                    if cfg.logger:
                        cfg.logger.exception(
                            "Unable to reset winner history in %s",
                            cfg.history_file_path,
                        )
                    return (
                        "History reset unavailable",
                        "-",
                        "The winner history could not be cleared.",
                        "simple-raffle-result is-error",
                        dash.no_update,
                    )

                return (
                    "History reset",
                    "-",
                    "Winner history has been cleared.",
                    "simple-raffle-result is-reset",
                    self._history_rows(),
                )

            if dash.ctx.triggered_id == id_("reset-button"):
                try:
                    summary = self.raffle.reset_entries(cfg.event_name)
                except Exception:
                    if cfg.logger:
                        cfg.logger.exception(
                            "Unable to reset entries in %s",
                            cfg.entries_csv_path,
                        )
                    return (
                        "Reset unavailable",
                        "-",
                        "The raffle entries could not be reset.",
                        "simple-raffle-result is-error",
                        dash.no_update,
                    )

                return (
                    "Entries reset",
                    "-",
                    "All {:,} raffle entries are available.".format(
                        summary["remaining"]
                    ),
                    "simple-raffle-result is-reset",
                    self._history_rows(),
                )

            normalized_prize = None
            if cfg.prize_enabled:
                normalized_prize = str(prize or "").strip()
                if not normalized_prize:
                    return (
                        "Prize required",
                        "-",
                        "Enter the prize before drawing a winner.",
                        "simple-raffle-result is-error",
                        self._history_rows(),
                    )
                if (
                    cfg.prize_options_path
                    and normalized_prize not in self._prize_options()
                ):
                    return (
                        "Prize unavailable",
                        "-",
                        "Select a prize from the configured list.",
                        "simple-raffle-result is-error",
                        self._history_rows(),
                    )

            try:
                winner_id, winner_name = self.raffle.draw(cfg.event_name)
            except Exception:
                if cfg.logger:
                    cfg.logger.exception("Unable to draw from %s", cfg.entries_csv_path)
                return (
                    "Draw unavailable",
                    "-",
                    "The raffle entries could not be loaded.",
                    "simple-raffle-result is-error",
                    dash.no_update,
                )

            if winner_id is None:
                return (
                    "No eligible entries",
                    "-",
                    "All eligible patrons have been drawn.",
                    "simple-raffle-result is-empty",
                    self._history_rows(),
                )

            try:
                self.history.add(winner_id, winner_name, prize=normalized_prize)
            except Exception:
                if cfg.logger:
                    cfg.logger.exception(
                        "Winner %s was drawn but history could not be saved to %s",
                        winner_id,
                        cfg.history_file_path,
                    )
                return (
                    "Winner - history save failed",
                    str(winner_id),
                    str(winner_name),
                    "simple-raffle-result is-error",
                    dash.no_update,
                )

            return (
                "Winner",
                str(winner_id),
                str(winner_name),
                "simple-raffle-result is-winner",
                self._history_rows(),
            )

        if cfg.export_enabled:
            @callback(
                Output(id_("results-download"), "data"),
                Input(id_("export-button"), "n_clicks"),
                prevent_initial_call=True,
            )
            def export_results(export_clicks):
                if not export_clicks:
                    raise PreventUpdate

                try:
                    winners = self.history.read()
                except Exception:
                    if cfg.logger:
                        cfg.logger.exception(
                            "Unable to export winner history from %s",
                            cfg.history_file_path,
                        )
                    raise PreventUpdate

                output = io.StringIO(newline="")
                writer = csv.writer(output)
                headers = ["Draw", "OM ID", "Name"]
                if cfg.prize_enabled:
                    headers.append("Prize")
                headers.append("Drawn At")
                writer.writerow(headers)

                for record in winners:
                    row = [
                        record.get("draw_number", ""),
                        record.get("uid", ""),
                        record.get("name", ""),
                    ]
                    if cfg.prize_enabled:
                        row.append(record.get("prize", ""))
                    row.append(str(record.get("drawn_at", "")).replace("T", " "))
                    writer.writerow(row)

                return {
                    "content": "\ufeff" + output.getvalue(),
                    "filename": "{}-results.csv".format(cfg.suffix),
                    "type": "text/csv",
                }


__all__ = ["SimpleRaffleConfig", "SimpleRafflePage", "WinnerHistoryFile"]
