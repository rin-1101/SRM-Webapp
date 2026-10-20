"""
Backward-compatible public API for the reusable shopping page.

Implementation lives in templates.modules.shopping. Existing concrete pages
can continue importing ShopConfig and ShoppingPage from this module.
"""

from .modules.shopping import ShopConfig, ShoppingPage

__all__ = ["ShopConfig", "ShoppingPage"]