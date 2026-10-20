"""Pure business rules shared by shopping page callbacks."""

import re
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd


class ShopRulesMixin(object):
    @staticmethod
    def format_om(om) -> str:
        digits = re.sub(r"\D", "", str(om or ""))
        return f"OM{digits.zfill(9)}" if digits else ""

    @staticmethod
    def is_valid_om(om) -> bool:
        """Return whether an OM value contains at least one digit."""
        return bool(re.sub(r"\D", "", str(om or "")))

    @staticmethod
    def category_slug(value) -> str:
        """Return a stable browser-safe value for category filters."""
        slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().casefold())
        return slug.strip("-") or "uncategorized"

    @staticmethod
    def extract_tier(category: str) -> Optional[int]:
        match = re.search(r"Tier\s*(\d+)", str(category))
        return int(match.group(1)) if match else None

    @staticmethod
    def get_gamedate(now: datetime) -> date:
        cutoff = now.replace(hour=6, minute=0, second=0, microsecond=0)
        return (now - timedelta(days=1)).date() if now < cutoff else now.date()
    @staticmethod
    def allocate_payment(order_items: list, credits_balance: int, cp_balance: int = 0) -> list:
        """Allocate credits first, then CP, for each order item."""
        credits_balance = max(0, credits_balance)
        cp_balance = max(0, cp_balance)
        results = []
        for item in order_items:
            cost = item["total"]
            use_credits = min(cost, credits_balance)
            use_cp = min(cost - use_credits, cp_balance)
            credits_balance -= use_credits
            cp_balance -= use_cp
            results.append({**item, "credits_used": use_credits, "cp_used": use_cp})
        return results

    @staticmethod
    def calculate_total_value(quantities: dict, df: pd.DataFrame) -> float:
        total = 0
        for idx_str, qty in quantities.items():
            try:
                total += df.loc[int(idx_str), "cost"] * qty
            except KeyError:
                pass
        return total

    @staticmethod
    def _total_redeemed_quantity(prev_cat_counts: dict) -> int:
        total = 0
        for value in (prev_cat_counts or {}).values():
            try:
                total += max(0, int(value or 0))
            except (TypeError, ValueError):
                continue
        return total

    def _within_redemption_limit(
        self,
        prev_cat_counts: dict,
        basket_quantity: int = 0,
        uid=None,
    ) -> bool:
        limit = self.get_redemption_limit(uid)
        if limit is None:
            return True
        return (
            self._total_redeemed_quantity(prev_cat_counts)
            + max(0, int(basket_quantity or 0))
            <= limit
        )

    def _redemption_warning(self, prev_cat_counts: dict, uid=None) -> str:
        limit = self.get_redemption_limit(uid)
        if limit is None or self._within_redemption_limit(
            prev_cat_counts, 1, uid
        ):
            return ""
        return (
            "You have already redeemed the maximum ({}) allowed for this "
            "campaign.".format(limit)
        )

    def _category_warning(
        self, category: str, prev_cat_counts: dict, uid=None
    ) -> str:
        prev_qty = int(prev_cat_counts.get(category, 0))
        limit = self.get_category_limit(uid)
        if prev_qty >= limit:
            return f"You have already redeemed the maximum ({limit}) for this category."
        if prev_qty > 0:
            return f"You have redeemed {prev_qty} of {limit} allowed for this category."
        return ""

    # ------------------------------------------------------------
