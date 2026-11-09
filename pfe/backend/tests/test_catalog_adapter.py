import pytest
import requests

from app.scraping.adapters.base_adapter import BaseCatalogAdapter, CatalogAdapterError, CatalogBlockedError


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def adapter(**catalog):
    return BaseCatalogAdapter({"catalog": {"base_url": "https://shop.example", **catalog}})


def test_successful_scraping_extracts_product(monkeypatch):
    a = adapter(title_selector="h1", price_selector=".price", availability_selector=".stock")
    monkeypatch.setattr(
        a.session,
        "get",
        lambda *args, **kwargs: FakeResponse("<html><h1>Phone</h1><span class='price'>999,90 EUR</span><div class='stock'>in stock</div></html>"),
    )

    data = a.extract_product("/p/phone")

    assert data["title"] == "Phone"
    assert data["price"] == 999.90
    assert data["availability"] == "in stock"
    assert a.health_status()["success_rate"] == 1.0


def test_timeout_retries_then_fails(monkeypatch):
    a = adapter(retry_count=1, backoff_base_s=0)

    def boom(*args, **kwargs):
        raise requests.Timeout("slow")

    monkeypatch.setattr(a.session, "get", boom)

    with pytest.raises(CatalogAdapterError):
        a.fetch_html("/timeout")
    assert a.metrics["retries"] == 1
    assert a.metrics["failures"] >= 1


def test_invalid_html_does_not_crash(monkeypatch):
    a = adapter(price_selector=".price")
    monkeypatch.setattr(a.session, "get", lambda *args, **kwargs: FakeResponse("<div><span class='price'>bad</span>"))

    data = a.extract_product("/broken")

    assert data["title"] is None
    assert data["price"] is None


def test_api_failures_retry(monkeypatch):
    a = adapter(retry_count=1, backoff_base_s=0)
    responses = [FakeResponse("temporary", 503), FakeResponse("<h1>Recovered</h1>", 200)]

    monkeypatch.setattr(a.session, "get", lambda *args, **kwargs: responses.pop(0))

    assert "Recovered" in a.fetch_html("/p")
    assert a.metrics["retries"] == 1


def test_pagination_discovers_multiple_pages(monkeypatch):
    a = adapter(product_url_regex=r"/product/", next_page_selector=".next")
    pages = {
        "https://shop.example/cat": "<a href='/product/a'>A</a><a class='next' href='/cat?page=2'>next</a>",
        "https://shop.example/cat?page=2": "<a href='/product/b'>B</a>",
    }
    monkeypatch.setattr(a.session, "get", lambda url, **kwargs: FakeResponse(pages[url]))

    urls = a.discover_product_urls(["/cat"])

    assert sorted(urls) == ["https://shop.example/product/a", "https://shop.example/product/b"]


def test_block_detection_raises(monkeypatch):
    a = adapter(retry_count=0)
    monkeypatch.setattr(a.session, "get", lambda *args, **kwargs: FakeResponse("<html>captcha required</html>", 200))

    with pytest.raises(CatalogBlockedError):
        a.fetch_html("/blocked")
