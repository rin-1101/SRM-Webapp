"""
Stable public API for reusable raffle pages.

Implementation lives in templates.modules.raffle so concrete pages can keep a
small, configuration-only surface.
"""

from .modules.raffle import (
    Raffle,
    RaffleApp,
    Raffle_app,
    RaffleControl,
    RafflePage,
    RaffleState,
    WinnerSetState,
    get_data,
    save_data,
)

__all__ = [
    "Raffle",
    "RaffleApp",
    "Raffle_app",
    "RaffleControl",
    "RafflePage",
    "RaffleState",
    "WinnerSetState",
    "get_data",
    "save_data",
]
