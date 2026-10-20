"""Prize-limited raffles with durable, event-wide winner exclusion."""

import csv
import io
import os
import random
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import dash
import yaml
from dash import Input, Output, callback, dcc, html
from dash.exceptions import PreventUpdate

from .simple_raffle import SimpleRafflePage
from .modules.raffle.draw import parse_entry_count


@contextmanager
def event_lock(history_path):
    """Serialize draws and history resets across app workers."""
    lock_path = history_path.with_suffix(history_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as file:
        file.seek(0, os.SEEK_END)
        if file.tell() == 0:
            file.write(b"0")
            file.flush()
        deadline = time.monotonic() + 10
        while True:
            try:
                file.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Another raffle action is in progress. Try again.")
                time.sleep(0.05)
        try:
            yield
        finally:
            file.seek(0)
            if os.name == "nt":
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)


class LimitedRafflePage(SimpleRafflePage):
    def __init__(self, config, prize_pool, **kwargs):
        super().__init__(config, **kwargs)
        self.prize_pool = prize_pool

    def _pool(self):
        with self.config.prize_options_path.open(encoding="utf-8") as file:
            prizes = yaml.safe_load(file)[self.prize_pool]
        if not prizes or any(
            not isinstance(p.get("name"), str)
            or not p["name"].strip()
            or type(p.get("limit")) is not int
            or p["limit"] <= 0
            for p in prizes
        ):
            raise ValueError("Invalid raffle prize configuration.")
        return prizes

    def _prize_options(self):
        return [p["name"] for p in self._pool()]

    def _prize_category(self, prize_name, pool=None):
        for prize in self._pool() if pool is None else pool:
            if prize_name in {prize["name"], *prize.get("aliases", [])}:
                return prize.get("category", "")
        return ""

    def _prize_headers(self):
        return [html.Th("Prize Category", scope="col"), *super()._prize_headers()]

    def _prize_cells(self, record):
        return [
            html.Td(self._prize_category(record.get("prize", ""))),
            *super()._prize_cells(record),
        ]

    @staticmethod
    def _count(prize, records):
        names = {prize["name"], *prize.get("aliases", [])}
        return sum(record.get("prize") in names for record in records)

    def prize_status(self):
        try:
            records = self.history.read()
            pool = self._pool()
            remaining = sum(max(0, p["limit"] - self._count(p, records)) for p in pool)
            summary = html.Ul([
                html.Li([
                    *([html.Strong(p["category"]), " "] if p.get("category") else []),
                    "{}: {}/{} winners".format(
                        p["name"], self._count(p, records), p["limit"]
                    ),
                ]) for p in pool
            ])
            message = (
                "All prizes have been drawn. Reset to start a new round."
                if not remaining else
                "Draw Raffle will draw all {} remaining winners.".format(remaining)
            )
            return not remaining, html.Div([summary, html.P(message)])
        except Exception:
            return True, "Prize configuration or winner history is unavailable."

    def _action_buttons(self):
        buttons = super()._action_buttons()
        buttons = [b for b in buttons if b.id != self.id("reset-button")]
        for button in buttons:
            if button.id == self.id("reset-history-button"):
                button.children = "Reset"
        buttons[0].disabled = True
        return buttons

    def _prize_control(self):
        return html.Div([
            html.Div(id=self.id("prize-status"), **{"aria-live": "polite"}),
            dcc.Interval(id=self.id("prize-refresh"), interval=2000),
        ])

    def draw_all(self):
        cfg = self.config
        with event_lock(cfg.history_file_path):
            records = self.history.read()
            slots = [p["name"] for p in self._pool()
                     for _ in range(max(0, p["limit"] - self._count(p, records)))]
            if not slots:
                raise ValueError("All prizes have been drawn. Reset to start a new round.")

            with cfg.entries_csv_path.open(newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                fields = reader.fieldnames
                if not {"UniversalPlayerID", "Name", "Entries"}.issubset(fields or []):
                    raise ValueError("Raffle entries are missing required columns.")
                rows = list(reader)
            if "won_entries" not in fields:
                fields.append("won_entries")
            normalize = lambda value: str(value).strip().casefold()
            excluded = {normalize(r["uid"]) for r in records}
            excluded.update(normalize(uid) for uid in
                            self.raffle.winner_sets.winner_ids(cfg.event_name))
            for row in rows:
                entries = parse_entry_count(row["Entries"], "Entries")
                used = parse_entry_count(row.get("won_entries"), "won_entries", allow_blank=True)
                row["Entries"] = entries
                row["won_entries"] = used
                if entries < 0 or used < 0 or used > entries:
                    raise ValueError("Invalid raffle entry counts.")
                if used:
                    excluded.add(normalize(row["UniversalPlayerID"]))
            eligible = [r for r in rows if int(r["Entries"]) > 0
                        and normalize(r["UniversalPlayerID"]) not in excluded]
            unique_count = len({normalize(r["UniversalPlayerID"]) for r in eligible})
            if unique_count < len(slots):
                raise ValueError(
                    "Need {} unique eligible patrons, but only {} are available. No winners were drawn."
                    .format(len(slots), unique_count)
                )
            winners = []
            for prize_name in slots:
                winner = random.choices(
                    eligible, weights=[int(r["Entries"]) for r in eligible]
                )[0]
                winners.append((winner["UniversalPlayerID"].strip(),
                                winner["Name"].strip(), prize_name))
                winner["won_entries"] = int(winner.get("won_entries") or 0) + 1
                winner_id = normalize(winner["UniversalPlayerID"])
                eligible = [r for r in eligible
                            if normalize(r["UniversalPlayerID"]) != winner_id]

            # Save the entire batch before updating entry bookkeeping. History
            # remains authoritative if a later write fails.
            added = self.history.add_many(winners)
            warning = None
            try:
                temp = cfg.entries_csv_path.with_suffix(".csv.tmp")
                with temp.open("w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                temp.replace(cfg.entries_csv_path)
                for record in added:
                    self.raffle.winner_sets.add(cfg.event_name, record["uid"], record["name"])
            except Exception:
                if cfg.logger:
                    cfg.logger.exception("Winner saved; raffle entry bookkeeping failed")
                warning = "Winners saved, but entry bookkeeping failed. Contact support before resetting."
            return added, warning

    def register_callbacks(self):
        id_ = self.id

        @callback(
            Output(id_("draw-button"), "disabled"),
            Output(id_("prize-status"), "children"),
            Input(id_("history-body"), "children"),
            Input(id_("prize-refresh"), "n_intervals"),
        )
        def update_status(_history, _interval):
            return self.prize_status()

        @callback(
            Output(id_("result-label"), "children"),
            Output(id_("winner-id"), "children"),
            Output(id_("winner-name"), "children"),
            Output(id_("result"), "className"),
            Output(id_("history-body"), "children"),
            Input(id_("draw-button"), "n_clicks"),
            Input(id_("reset-history-button"), "n_clicks"),
            prevent_initial_call=True,
        )
        def handle_action(draw_clicks, reset_clicks):
            trigger = dash.ctx.triggered_id
            if not ((trigger == id_("draw-button") and draw_clicks)
                    or (trigger == id_("reset-history-button") and reset_clicks)):
                raise PreventUpdate
            try:
                if trigger == id_("reset-history-button"):
                    with event_lock(self.config.history_file_path):
                        # Keep history until entry/set reset succeeds so a failed
                        # reset cannot accidentally reopen prize slots.
                        self.raffle.reset_entries(self.config.event_name)
                        self.history.clear()
                    return ("Raffle reset", "-", "Entries restored. Winner history and prize limits cleared. All patrons are eligible again.",
                            "simple-raffle-result is-reset", self._history_rows())
                winners, warning = self.draw_all()
                return ("Raffle complete", "{} winners".format(len(winners)),
                        warning or "All prizes drawn. See the winners and their prizes below.",
                        "simple-raffle-result is-winner", self._history_rows())
            except Exception as exc:
                if self.config.logger:
                    self.config.logger.exception("Raffle action failed")
                message = str(exc) if isinstance(exc, ValueError) else "Raffle data is unavailable. Try again."
                return ("Draw unavailable", "-", message,
                        "simple-raffle-result is-error", self._history_rows())

        @callback(
            Output(id_("results-download"), "data"),
            Input(id_("export-button"), "n_clicks"), prevent_initial_call=True,
        )
        def export_results(clicks):
            if not clicks:
                raise PreventUpdate
            output = io.StringIO(newline="")
            writer = csv.writer(output)
            writer.writerow(["Draw", "OM ID", "Name", "Prize Category", "Prize", "Drawn At"])
            pool = self._pool()
            for r in self.history.read():
                writer.writerow([r["draw_number"], r["uid"], r["name"],
                                 self._prize_category(r.get("prize", ""), pool),
                                 r.get("prize", ""), r["drawn_at"].replace("T", " ")])
            export_date = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
            return {"content": "\ufeff" + output.getvalue(),
                    "filename": f"{self.config.suffix}-results-{export_date}.csv", "type": "text/csv"}
