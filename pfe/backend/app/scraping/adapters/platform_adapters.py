from __future__ import annotations

from app.scraping.adapters.base_adapter import BaseCatalogAdapter


class GenericAdapter(BaseCatalogAdapter):
    platform = "generic"


class ShopifyAdapter(BaseCatalogAdapter):
    platform = "shopify"


class WooCommerceAdapter(BaseCatalogAdapter):
    platform = "woocommerce"


class PrestaShopAdapter(BaseCatalogAdapter):
    platform = "prestashop"


def get_adapter(platform: str | None, config: dict) -> BaseCatalogAdapter:
    p = (platform or "generic").lower().strip()
    if p == "shopify":
        return ShopifyAdapter(config)
    if p == "woocommerce":
        return WooCommerceAdapter(config)
    if p == "prestashop":
        return PrestaShopAdapter(config)
    return GenericAdapter(config)

