"""Reusable Dash layouts and callbacks for Lotto entry and result pages."""

import base64
import uuid
from datetime import datetime

import dash
from dash import ALL, Input, Output, State, callback, clientside_callback, dcc, html
from dash.exceptions import PreventUpdate

from utils.lotto import (
    LOTTO_TIMEZONE,
    LottoStore,
    build_results_workbook,
    match_entries,
    normalize_numbers,
)


def _number_button_class(number, selected):
    class_name = "lotto-number-button"
    if number in selected:
        class_name += " is-selected"
    return class_name


def _number_grid(type_name):
    return html.Div(
        [
            html.Button(
                str(number),
                id={"type": type_name, "index": number},
                n_clicks=0,
                className="lotto-number-button",
            )
            for number in range(1, 50)
        ],
        className="lotto-number-grid",
    )


class LottoEntryPage(object):
    def __init__(self, suffix="lotto", store=None):
        self.suffix = suffix
        self.store = store or LottoStore()
        self.number_type = "lotto-number-{}".format(suffix)

    def id(self, name):
        return "{}-{}".format(name, self.suffix)

    def layout(self):
        return html.Div(
            [
                html.Link(rel="stylesheet", href="/assets/lotto/style.css"),
                dcc.Store(id=self.id("selected"), data=[]),
                dcc.Store(id=self.id("submission-id"), data=str(uuid.uuid4())),
                html.Main(
                    [
                        html.Header(
                            [
                                html.P("LOTTO", className="lotto-kicker"),
                                html.H1("Choose Your Numbers", className="lotto-title"),
                                html.P(
                                    "Select exactly 6 numbers from 1 to 49.",
                                    className="lotto-subtitle",
                                ),
                            ],
                            className="lotto-header",
                        ),
                        html.Div(
                            [
                                html.Label("Player Number", htmlFor=self.id("player-number")),
                                dcc.Input(
                                    id=self.id("player-number"),
                                    type="text",
                                    placeholder="Enter player number",
                                    maxLength=50,
                                    className="lotto-player-input",
                                ),
                            ],
                            className="lotto-player-field",
                        ),
                        _number_grid(self.number_type),
                        html.P(
                            "0 of 6 selected",
                            id=self.id("selection-status"),
                            className="lotto-selection-status",
                        ),
                        html.Button(
                            "Submit Lotto Entry",
                            id=self.id("submit"),
                            n_clicks=0,
                            className="lotto-primary-button",
                        ),
                        html.Div(
                            id=self.id("submit-message"),
                            className="lotto-message",
                            **{"aria-live": "polite"},
                        ),
                    ],
                    className="lotto-card",
                ),
            ],
            className="lotto-page",
        )

    def register_callbacks(self):
        id_ = self.id
        number_type = self.number_type

        @callback(
            Output({"type": number_type, "index": ALL}, "className"),
            Output(id_("selected"), "data"),
            Output(id_("selection-status"), "children"),
            Output(id_("submit-message"), "children"),
            Output(id_("submit-message"), "className"),
            Output(id_("submission-id"), "data"),
            Input({"type": number_type, "index": ALL}, "n_clicks"),
            Input(id_("submit"), "n_clicks"),
            State(id_("selected"), "data"),
            State(id_("player-number"), "value"),
            State(id_("submission-id"), "data"),
            prevent_initial_call=True,
        )
        def handle_entry(
            number_clicks,
            submit_clicks,
            selected_numbers,
            player_number,
            submission_id,
        ):
            selected = sorted({int(number) for number in (selected_numbers or [])})
            triggered = dash.ctx.triggered_id

            if triggered == id_("submit"):
                try:
                    record, created = self.store.submit(
                        submission_id,
                        player_number,
                        selected,
                    )
                except Exception as exc:
                    return (
                        [_number_button_class(number, selected) for number in range(1, 50)],
                        selected,
                        "{} of 6 selected".format(len(selected)),
                        str(exc),
                        "lotto-message is-error",
                        dash.no_update,
                    )

                message = "Entry saved. PDF: {}".format(record["pdf_file"])
                if not created:
                    message = "This entry was already saved. PDF: {}".format(
                        record["pdf_file"]
                    )
                return (
                    [_number_button_class(number, []) for number in range(1, 50)],
                    [],
                    "0 of 6 selected",
                    message,
                    "lotto-message is-success",
                    str(uuid.uuid4()),
                )

            if isinstance(triggered, dict) and triggered.get("type") == number_type:
                number = int(triggered["index"])
                if number in selected:
                    selected.remove(number)
                    message = ""
                    message_class = "lotto-message"
                elif len(selected) >= 6:
                    message = "A maximum of 6 numbers can be selected."
                    message_class = "lotto-message is-error"
                else:
                    selected.append(number)
                    selected.sort()
                    message = ""
                    message_class = "lotto-message"

                return (
                    [_number_button_class(value, selected) for value in range(1, 50)],
                    selected,
                    "{} of 6 selected".format(len(selected)),
                    message,
                    message_class,
                    dash.no_update,
                )

            return (dash.no_update,) * 6


class LottoResultsPage(object):
    def __init__(self, suffix="lotto-results", store=None):
        self.suffix = suffix
        self.store = store or LottoStore()
        self.number_type = "lotto-winning-number-{}".format(suffix)

    def id(self, name):
        return "{}-{}".format(name, self.suffix)

    def layout(self):
        return html.Div(
            [
                html.Link(rel="stylesheet", href="/assets/lotto/style.css"),
                dcc.Store(id=self.id("winning-numbers"), data=[]),
                dcc.Store(id=self.id("results"), data=[]),
                dcc.Download(id=self.id("download")),
                html.Main(
                    [
                        html.Header(
                            [
                                html.P("LOTTO", className="lotto-kicker"),
                                html.H1("Winning Numbers", className="lotto-title"),
                                html.P(
                                    "Select the 6 official winning numbers.",
                                    className="lotto-subtitle",
                                ),
                            ],
                            className="lotto-header",
                        ),
                        _number_grid(self.number_type),
                        html.P(
                            "0 of 6 selected",
                            id=self.id("selection-status"),
                            className="lotto-selection-status",
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "Check Results",
                                    id=self.id("check"),
                                    n_clicks=0,
                                    className="lotto-primary-button",
                                ),
                                html.Button(
                                    "Export Excel",
                                    id=self.id("export"),
                                    n_clicks=0,
                                    className="lotto-secondary-button",
                                ),
                            ],
                            className="lotto-result-actions",
                        ),
                        html.Div(
                            id=self.id("message"),
                            className="lotto-message",
                            **{"aria-live": "polite"},
                        ),
                        html.Div(id=self.id("groups"), className="lotto-result-groups"),
                    ],
                    className="lotto-card lotto-results-card",
                ),
            ],
            className="lotto-page",
        )

    def _result_groups(self, results):
        groups = []
        for match_count in range(1, 7):
            matched = [
                result for result in results if int(result["matches"]) == match_count
            ]
            rows = [
                html.Tr(
                    [
                        html.Td(result["player_number"]),
                        html.Td(result["selected_numbers"]),
                        html.Td(str(result["submitted_at"]).replace("T", " ")),
                    ]
                )
                for result in matched
            ]
            if not rows:
                rows = [
                    html.Tr(
                        html.Td(
                            "No winners",
                            colSpan=3,
                            className="lotto-empty-result",
                        )
                    )
                ]
            groups.append(
                html.Section(
                    [
                        html.H2(
                            "{} Match{} ({})".format(
                                match_count,
                                "" if match_count == 1 else "es",
                                len(matched),
                            ),
                            className="lotto-group-title",
                        ),
                        html.Div(
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Player Number"),
                                                html.Th("Selected Numbers"),
                                                html.Th("Submitted At"),
                                            ]
                                        )
                                    ),
                                    html.Tbody(rows),
                                ],
                                className="lotto-results-table",
                            ),
                            className="lotto-table-wrap",
                        ),
                    ],
                    className="lotto-result-group",
                )
            )
        return groups

    def register_callbacks(self):
        id_ = self.id
        number_type = self.number_type

        @callback(
            Output({"type": number_type, "index": ALL}, "className"),
            Output(id_("winning-numbers"), "data"),
            Output(id_("selection-status"), "children"),
            Input({"type": number_type, "index": ALL}, "n_clicks"),
            State(id_("winning-numbers"), "data"),
            prevent_initial_call=True,
        )
        def toggle_winning_number(number_clicks, winning_numbers):
            selected = sorted({int(number) for number in (winning_numbers or [])})
            triggered = dash.ctx.triggered_id
            if not isinstance(triggered, dict) or triggered.get("type") != number_type:
                return (dash.no_update,) * 3

            number = int(triggered["index"])
            if number in selected:
                selected.remove(number)
            elif len(selected) < 6:
                selected.append(number)
                selected.sort()

            return (
                [_number_button_class(value, selected) for value in range(1, 50)],
                selected,
                "{} of 6 selected".format(len(selected)),
            )

        @callback(
            Output(id_("groups"), "children"),
            Output(id_("results"), "data"),
            Output(id_("message"), "children"),
            Output(id_("message"), "className"),
            Input(id_("check"), "n_clicks"),
            State(id_("winning-numbers"), "data"),
            prevent_initial_call=True,
        )
        def check_results(check_clicks, winning_numbers):
            if not check_clicks:
                raise PreventUpdate
            try:
                winning = normalize_numbers(winning_numbers)
                results = match_entries(self.store.read(), winning)
            except Exception as exc:
                return [], [], str(exc), "lotto-message is-error"

            matched_count = sum(1 for result in results if result["matches"] > 0)
            return (
                self._result_groups(results),
                results,
                "Checked {:,} entries; {:,} have at least one match.".format(
                    len(results),
                    matched_count,
                ),
                "lotto-message is-success",
            )

        @callback(
            Output(id_("download"), "data"),
            Input(id_("export"), "n_clicks"),
            State(id_("results"), "data"),
            State(id_("winning-numbers"), "data"),
            prevent_initial_call=True,
        )
        def export_results(export_clicks, results, winning_numbers):
            if not export_clicks or not results:
                raise PreventUpdate
            workbook = build_results_workbook(results, winning_numbers)
            filename = "Lotto_Results_{}.xlsx".format(
                datetime.now(LOTTO_TIMEZONE).strftime("%Y%m%d_%H%M%S")
            )
            return {
                "content": base64.b64encode(workbook).decode("ascii"),
                "filename": filename,
                "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "base64": True,
            }


class LottoTicketsPage(object):
    def __init__(self, suffix="lotto-tickets", store=None):
        self.suffix = suffix
        self.store = store or LottoStore()
        self.print_button_type = "lotto-ticket-print-{}".format(suffix)

    def id(self, name):
        return "{}-{}".format(name, self.suffix)

    @staticmethod
    def _record_numbers(record):
        return [str(record.get("number_{}".format(index), "")) for index in range(1, 7)]

    def _ticket(self, record, printable=False):
        numbers = self._record_numbers(record)
        children = [
            html.P("LOTTO ENTRY", className="lotto-ticket-kicker"),
            html.H2(record.get("player_number", ""), className="lotto-ticket-player"),
            html.P(
                str(record.get("submitted_at", "")).replace("T", " "),
                className="lotto-ticket-time",
            ),
            html.Div(
                [html.Span(number, className="lotto-ticket-number") for number in numbers],
                className="lotto-ticket-numbers",
            ),
        ]
        if not printable:
            children.append(
                html.Button(
                    "Print Ticket",
                    id={
                        "type": self.print_button_type,
                        "index": record.get("submission_id", ""),
                    },
                    n_clicks=0,
                    className="lotto-secondary-button lotto-ticket-print-button",
                )
            )
        return html.Article(children, className="lotto-ticket")

    def _load_ticket_cards(self, player_query=None):
        try:
            records = list(reversed(self.store.read()))
        except Exception as exc:
            return (
                [],
                str(exc),
                "lotto-message is-error",
            )
        query = str(player_query or "").strip().upper()
        if query:
            records = [
                record
                for record in records
                if query in str(record.get("player_number", "")).upper()
            ]
        if not records:
            empty_message = "No Lotto tickets have been submitted."
            status_message = "0 tickets"
            if query:
                empty_message = "No tickets found for {}.".format(query)
                status_message = "0 matching tickets"
            return (
                html.P(empty_message, className="lotto-empty-result"),
                status_message,
                "lotto-message",
            )
        return (
            [self._ticket(record) for record in records],
            "{:,} {}ticket{}".format(
                len(records),
                "matching " if query else "",
                "" if len(records) == 1 else "s",
            ),
            "lotto-message is-success",
        )

    def layout(self):
        cards, message, message_class = self._load_ticket_cards()
        return html.Div(
            [
                html.Link(rel="stylesheet", href="/assets/lotto/style.css"),
                dcc.Store(id=self.id("print-trigger")),
                dcc.Store(id=self.id("print-complete")),
                html.Main(
                    [
                        html.Header(
                            [
                                html.P("LOTTO", className="lotto-kicker"),
                                html.H1("Lotto Tickets", className="lotto-title"),
                                html.P(
                                    "Select a ticket to open the workstation print dialog.",
                                    className="lotto-subtitle",
                                ),
                            ],
                            className="lotto-header",
                        ),
                        html.Div(
                            [
                                dcc.Input(
                                    id=self.id("find-player"),
                                    type="text",
                                    placeholder="Enter player number",
                                    debounce=False,
                                    maxLength=50,
                                    n_submit=0,
                                    className="lotto-player-input",
                                ),
                                html.Button(
                                    "Find Player",
                                    id=self.id("find"),
                                    n_clicks=0,
                                    className="lotto-primary-button",
                                ),
                                html.Button(
                                    "Refresh Tickets",
                                    id=self.id("refresh"),
                                    n_clicks=0,
                                    className="lotto-secondary-button",
                                ),
                            ],
                            className="lotto-ticket-search",
                        ),
                        html.Div(
                            message,
                            id=self.id("message"),
                            className=message_class,
                            **{"aria-live": "polite"},
                        ),
                        html.Div(
                            cards,
                            id=self.id("ticket-list"),
                            className="lotto-ticket-list",
                        ),
                    ],
                    className="lotto-card lotto-results-card",
                ),
                html.Div(id=self.id("print-area"), className="lotto-print-area"),
            ],
            className="lotto-page lotto-tickets-page",
        )

    def register_callbacks(self):
        id_ = self.id

        @callback(
            Output(id_("ticket-list"), "children"),
            Output(id_("message"), "children"),
            Output(id_("message"), "className"),
            Input(id_("refresh"), "n_clicks"),
            Input(id_("find"), "n_clicks"),
            Input(id_("find-player"), "n_submit"),
            State(id_("find-player"), "value"),
            prevent_initial_call=True,
        )
        def refresh_tickets(refresh_clicks, find_clicks, find_submits, player_query):
            if not refresh_clicks and not find_clicks and not find_submits:
                raise PreventUpdate
            return self._load_ticket_cards(player_query)

        @callback(
            Output(id_("print-area"), "children"),
            Output(id_("print-trigger"), "data"),
            Input({"type": self.print_button_type, "index": ALL}, "n_clicks"),
            prevent_initial_call=True,
        )
        def prepare_ticket_for_print(print_clicks):
            if not any(print_clicks or []):
                raise PreventUpdate
            triggered = dash.ctx.triggered_id
            if not isinstance(triggered, dict):
                raise PreventUpdate
            submission_id = str(triggered.get("index", ""))
            record = next(
                (
                    item
                    for item in self.store.read()
                    if item.get("submission_id") == submission_id
                ),
                None,
            )
            if record is None:
                raise PreventUpdate
            return self._ticket(record, printable=True), str(uuid.uuid4())

        clientside_callback(
            """
            function(trigger) {
                if (!trigger) {
                    return window.dash_clientside.no_update;
                }
                window.setTimeout(function() { window.print(); }, 150);
                return trigger;
            }
            """,
            Output(id_("print-complete"), "data"),
            Input(id_("print-trigger"), "data"),
            prevent_initial_call=True,
        )


__all__ = ["LottoEntryPage", "LottoResultsPage", "LottoTicketsPage"]
