"""Public shopping page orchestrator."""

from okada import LogService

from .callbacks import ShopCallbacksMixin
from .config import ShopConfig
from .data import ShopDataMixin
from .layout import ShopLayoutMixin
from .rules import ShopRulesMixin


class ShoppingPage(
    ShopDataMixin,
    ShopRulesMixin,
    ShopLayoutMixin,
    ShopCallbacksMixin,
):
    """Coordinate configuration, layout, data access, and callbacks for one shop."""

    def __init__(self, module_name: str, config: ShopConfig):
        self.config = config
        self.suffix = config.suffix
        self.module_name = module_name
        self.logger = LogService(config.logger_name).get_logger()

    def register_callbacks(self) -> None:
        """Register all callbacks for this shop instance."""
        self._register_callbacks()

    def id(self, name: str) -> str:
        """Return a component ID namespaced to this shop instance."""
        return f"{name}-{self.suffix}"

    def wid(self, component_type: str, index) -> dict:
        """Return a pattern-matching component ID for this shop instance."""
        return {"type": f"{component_type}-{self.suffix}", "index": index}