import types
import unittest

from src.lib import image_scraper as mod


class DummyResp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html"}
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError("HTTP error")


class TestParseImages(unittest.TestCase):
    def test_extracts_and_normalizes_img_src(self):
        html = """
        <html><head><title>t</title></head>
        <body>
          <img src="/images/a.jpg">
          <img data-src="//cdn.example.com/x.png?v=1">
          <img src="not-an-image.txt">
          <img src="/icons/icon.svg">
        </body></html>
        """
        # Monkeypatch network fetch
        def fake_request_with_retry(url: str, retries: int = 3, backoff: float = 1.2):
            return DummyResp(html)

        old_fn = mod._request_with_retry
        mod._request_with_retry = fake_request_with_retry
        try:
            res = mod.scrape_images("https://example.com/page", "./.tmp_test_out", limit=None, respect_robots=False)
        finally:
            mod._request_with_retry = old_fn
        self.assertEqual(res.page_url, "https://example.com/page")
        # Should include 3 image URLs (filtering out non-image .txt)
        self.assertEqual(len(res.image_urls), 3)
        # Ensure normalization and protocol for // links
        self.assertIn("https://cdn.example.com/x.png?v=1", res.image_urls)


if __name__ == "__main__":
    unittest.main()
