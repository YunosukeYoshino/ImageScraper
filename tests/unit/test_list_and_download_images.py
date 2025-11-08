import unittest
from pathlib import Path

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


class TestListAndDownloadImages(unittest.TestCase):
    def test_list_images_returns_normalized_urls(self):
        html = """
        <html><body>
          <img src="/a.jpg">
          <img data-src="//cdn.example.com/x.png?v=2">
          <img src="/not-image.txt">
          <img src="/b.svg">
        </body></html>
        """
        def fake_request_with_retry(url: str, retries: int = 3, backoff: float = 1.2):
            return DummyResp(html)

        old = mod._request_with_retry
        mod._request_with_retry = fake_request_with_retry
        try:
            urls = mod.list_images("https://example.com/page")
        finally:
            mod._request_with_retry = old
        self.assertEqual(len(urls), 3)
        self.assertIn("https://cdn.example.com/x.png?v=2", urls)

    def test_download_images_uses_downloader_and_respects_robots(self):
        # Prepare 3 fake urls
        urls = [
            "https://example.com/a.jpg",
            "https://example.com/b.png",
            "https://example.com/c.svg",
        ]
        saved = []

        def fake_download(url: str, dest_dir: str):
            p = Path(dest_dir) / ("file_" + Path(url).suffix)
            saved.append(str(p))
            return str(p)

        def fake_robots(url: str, user_agent: str = mod.DEFAULT_HEADERS["User-Agent"]):
            # block the second url
            return not url.endswith("b.png")

        old_dl = mod._download_image
        old_robot = mod._robots_allowed
        mod._download_image = fake_download
        mod._robots_allowed = fake_robots
        try:
            out = mod.download_images(urls, "./.tmp_test_out")
        finally:
            mod._download_image = old_dl
            mod._robots_allowed = old_robot

        # second url should be skipped by robots
        self.assertEqual(len(out), 2)
        self.assertTrue(all(s.endswith(('.jpg', '.png', '.svg', '.bin')) for s in saved))


if __name__ == "__main__":
    unittest.main()
