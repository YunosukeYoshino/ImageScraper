import unittest
from unittest import mock

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
    @mock.patch.object(mod, "_request_with_retry")
    def test_画像URLを抽出し正規化する(self, mock_request):
        # Arrange
        html = """
        <html><head><title>t</title></head>
        <body>
          <img src="/images/a.jpg">
          <img data-src="//cdn.example.com/x.png?v=1">
          <img src="not-an-image.txt">
          <img src="/icons/icon.svg">
        </body></html>
        """
        mock_request.return_value = DummyResp(html)

        # Act
        res = mod.scrape_images("https://example.com/page", "./.tmp_test_out", limit=None, respect_robots=False)

        # Assert
        self.assertEqual(res.page_url, "https://example.com/page")
        # 非画像の.txtを除外して3つの画像URLを含む
        self.assertEqual(len(res.image_urls), 3)
        # //で始まるリンクのプロトコル正規化を確認
        self.assertIn("https://cdn.example.com/x.png?v=1", res.image_urls)


if __name__ == "__main__":
    unittest.main()
