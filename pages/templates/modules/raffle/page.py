"""
pages/templates/raffle.py
=========================
Base template for all raffle pages.
Do not register this directly — subclass it in a page file under pages/.
"""

import re
import time
from dash import dcc, html, Input, Output, callback


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _img(src: str, height: str = "auto", extra_style: dict = None):
    style = {
        "height": height,
        "width": "auto",
        "maxWidth": "100%",
        "objectFit": "contain",
    }
    if extra_style:
        style.update(extra_style)
    return html.Img(src=src, style=style)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class RafflePage:
    """
    Base template for a Dash raffle page.

    Subclass this in pages/<event>.py, override the config attributes,
    then call `.register()` once at module level.
    """

    # ── Routing & auth ─────────────────────────────────────────────────
    page_path: str    = "/raffle"
    access_level: str = "standard"

    # ── Shared-data store key ──────────────────────────────────────────
    store_key: str = "raffle"

    # ── DOM id prefix (must be unique per page) ────────────────────────
    container_id: str = "container-div-raffle"

    # ── Assets ─────────────────────────────────────────────────────────
    bg_image: str      = "/assets/raffle/Background/BG.jpg"
    logo_src: str      = "/assets/raffle/logo.png"
    logo_height: str   = "300px"
    date_img_dir: str  = "/assets/raffle/Dates"
    time_img_dir: str  = "/assets/raffle/Time"
    prize_img_dir: str = "/assets/raffle/Prizes"
    php_img: str       = "PHP.png"
    worth_img: str     = "WORTH.png"

    # ── Styling ────────────────────────────────────────────────────────
    font_class: str = "raffle-font"
    padding_top = 0
    padding_bottom = 0
    padding_left = 0
    padding_right = 0
    prize_prefix: str = "PHP"
    prize_suffix: str = "FREE PLAY"
    time_suffix: str = "DRAW"

    # ── Copy ───────────────────────────────────────────────────────────
    default_uid_text: str = "Draw is about to Begin"
    standby_text: str     = "Next Draw Soon"

    # ── Timings ────────────────────────────────────────────────────────
    poll_interval_ms: int    = 1_000
    anim_interval_ms: int    = 100
    animation_window_s: float = 3.0
    trigger_window_s: float   = 5.0

    # ── Feature flags ──────────────────────────────────────────────────
    show_prize: bool = True
    show_time: bool  = True

    # ──────────────────────────────────────────────────────────────────
    # Constructor
    # ──────────────────────────────────────────────────────────────────

    def __init__(self, raffle_app, get_data_fn=None, show_prize: bool = None, show_time: bool = None):
        self._raffle_app = raffle_app

        if get_data_fn is not None:
            self._get_data = get_data_fn
        else:
            from .state import get_data
            self._get_data = get_data

        # Instance-level overrides; fall back to class attribute if not passed
        if show_prize is not None:
            self.show_prize = show_prize
        if show_time is not None:
            self.show_time = show_time

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def register(self, module_name: str):
        """
        Kept for backwards compatibility.
        Preferred pattern: in the page file, call dash.register_page(__name__)
        at module level, expose `layout = _page.layout`, then call
        `_page._register_callbacks()` — matching Dash's multi-page discovery.
        """
        import dash
        from utils.login_handler import require_login

        dash.register_page(module_name, path=self.page_path, layout=self.layout)
        require_login(module_name, access_level=self.access_level)
        self._register_callbacks()

    # ──────────────────────────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────────────────────────

    def layout(self):
        p = self._prefix()

        meta_items = [
            html.Div(
                id=f"{p}-date",
                className=f"has-text-centered {self.font_class} raffle-meta-value raffle-date",
            )
        ]
        if self.show_time:
            meta_items.append(
                html.Div(
                    id=f"{p}-time",
                    className=f"has-text-centered {self.font_class} raffle-meta-value raffle-time",
                )
            )

        winner_items = [
            html.Div(
                id=f"{p}-uid",
                className=f"has-text-centered {self.font_class} raffle-winner-id is-message",
                children=self.default_uid_text,
            ),
            html.Div(
                id=f"{p}-initials",
                className=f"has-text-centered {self.font_class} raffle-winner-name",
            ),
        ]

        content_class = "raffle-page-content"
        if not self.show_prize:
            content_class += " raffle-no-prize"

        content_children = [
            html.Div(
                className="raffle-header",
                children=[
                    html.Div(
                        className="raffle-logo",
                        children=[_img(self.logo_src, height=self.logo_height)],
                    ),
                    # html.Div(
                    #     id=f"{p}-details",
                    #     className="raffle-meta",
                    #     children=meta_items,
                    # ),
                ],
            ),
        ]
        if self.show_prize:
            content_children.append(
                html.Div(
                    id=f"{p}-prize",
                    className="has-text-centered raffle-prize",
                )
            )
        content_children.extend([
            html.Div(className="raffle-divider", **{"aria-hidden": "true"}),
            html.Div(
                id=f"{p}-subdetails",
                className="raffle-winner",
                children=winner_items,
            ),
        ])

        return html.Div([
            html.Link(rel="stylesheet", href="/assets/raffle/raffle.css"),
            dcc.Interval(id=f"{p}-poll", interval=self.poll_interval_ms, n_intervals=0),
            dcc.Interval(
                id=f"{p}-anim",
                interval=self.anim_interval_ms,
                n_intervals=0,
                disabled=True,
            ),
            dcc.Location(id=f"{p}-url", refresh=False),
            dcc.Store(id=f"{p}-anim-store", data={"animating": False, "timestamp": 0}),
            html.Div(
                id=self.container_id,
                className="raffle-page",
                style={"backgroundImage": f"url('{self.bg_image}')"},
                children=[
                    html.Div(
                        id=f"{p}-details",
                        className="raffle-meta",
                        children=meta_items,
                    ),
                    html.Div(
                        className=content_class,
                        style={
                            "paddingTop": self.padding_top,
                            "paddingBottom": self.padding_bottom,
                            "paddingLeft": self.padding_left,
                            "paddingRight": self.padding_right,
                        },
                        children=content_children,
                    ),
                ],
            ),
        ])

    def _format_draw_time(self, value):
        text = str(value or "").strip().replace("_", ":")
        if not text or text == "-":
            return text or "-"
        text = text.replace(":00 ", " ")
        if text.startswith("0"):
            text = text[1:]
        return "{} {}".format(text, self.time_suffix).strip()

    def _build_prize_children(self, prize):
        amount = prize if isinstance(prize, int) else None
        if isinstance(prize, str) and prize.strip():
            text = prize.strip()
            prefix = re.escape(self.prize_prefix)
            suffix = r"\s+".join(re.escape(part) for part in self.prize_suffix.split())
            match = re.fullmatch(
                rf"{prefix}\s+([\d,]+)\s+(?:worth\s+of\s+)?{suffix}",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                amount = int(match.group(1).replace(",", ""))
            else:
                return html.Span(text, className="raffle-prize-custom")

        if amount is not None:
            return [
                html.Span(self.prize_prefix, className="raffle-prize-prefix"),
                html.Strong("{:,}".format(amount), className="raffle-prize-amount"),
                html.Span(self.prize_suffix, className="raffle-prize-suffix"),
            ]
        return ""
    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _register_callbacks(self):
        p = self._prefix()

        # Capture config as locals so closures are stable
        store_key      = self.store_key
        get_data       = self._get_data
        raffle_app     = self._raffle_app
        trigger_win    = self.trigger_window_s
        anim_win       = self.animation_window_s
        default_uid    = self.default_uid_text
        standby        = self.standby_text
        font_class     = self.font_class
        date_dir       = self.date_img_dir
        time_dir       = self.time_img_dir
        prize_dir      = self.prize_img_dir
        show_prize     = self.show_prize
        show_time      = self.show_time

        @callback(
            Output(f"{p}-anim-store", "data"),
            Output(f"{p}-anim", "disabled"),
            Input(f"{p}-poll", "n_intervals"),
            prevent_initial_call=False,
        )
        def _check_animation(n):
            data = get_data(store_key)
            ts = data.get("animation_timestamp", 0)
            if ts > time.time() - trigger_win:
                return {"animating": True, "timestamp": ts}, False
            return {"animating": False, "timestamp": 0}, True

        @callback(
            Output(f"{p}-uid",      "children"),
            Output(f"{p}-initials", "children"),
            Output(f"{p}-uid",      "className"),
            Input(f"{p}-anim", "n_intervals"),
            Input(f"{p}-poll", "n_intervals"),
            prevent_initial_call=False,
        )
        def _update_display(anim_n, poll_n):
            data = get_data(store_key)
            ts = data.get("animation_timestamp", 0)
            is_animating = ts > time.time() - anim_win

            uid      = data.get("uid",      default_uid)
            initials = data.get("initials", "")

            if is_animating and uid not in (default_uid, standby):
                try:
                    uid, initials = raffle_app.draw_animate()
                except Exception:
                    pass
                return uid, initials, f"has-text-centered {font_class} raffle-winner-id animating"

            class_name = f"has-text-centered {font_class} raffle-winner-id"
            if uid in (default_uid, standby) or str(initials).strip() in ("", "-"):
                class_name += " is-message"
            return uid, initials, class_name

        _meta_outputs = [Output(f"{p}-date", "children")]
        if show_time:
            _meta_outputs.append(Output(f"{p}-time", "children"))
        if show_prize:
            _meta_outputs.append(Output(f"{p}-prize", "children"))

        @callback(
            _meta_outputs,
            Input(f"{p}-poll", "n_intervals"),
        )
        def _update_meta(n):
            data = get_data(store_key)
            result = [str(data.get("date", "-"))]
            if show_time:
                result.append(self._format_draw_time(data.get("time", "-")))
            if show_prize:
                result.append(self._build_prize_children(data.get("prize")))
            return result

    # ──────────────────────────────────────────────────────────────────
    # Private
    # ──────────────────────────────────────────────────────────────────

    def _prefix(self) -> str:
        """Derive a safe DOM id prefix from the page path."""
        return self.page_path.strip("/").replace("/", "-")