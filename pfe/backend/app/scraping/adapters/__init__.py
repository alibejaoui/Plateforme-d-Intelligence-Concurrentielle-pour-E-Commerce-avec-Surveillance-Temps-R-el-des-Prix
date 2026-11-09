from app.scraping.adapters.base_adapter import BaseCatalogAdapter
from app.scraping.adapters.platform_adapters import (
    GenericAdapter,
    ShopifyAdapter,
    WooCommerceAdapter,
    PrestaShopAdapter,
    get_adapter,
)

__all__ = [
    "BaseCatalogAdapter",
    "GenericAdapter",
    "ShopifyAdapter",
    "WooCommerceAdapter",
    "PrestaShopAdapter",
    "get_adapter",
]

