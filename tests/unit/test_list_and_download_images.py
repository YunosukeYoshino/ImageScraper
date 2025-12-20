import unittest
from pathlib import Path
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


class TestListAndDownloadImages(unittest.TestCase):
    @mock.patch.object(mod, '_request_with_retry')
    def test_list_images_正規化されたURLを返す(self, mock_request: mock.Mock):
        # Arrange
        html = """
        <html><body>
          <img src="/a.jpg">
          <img data-src="//cdn.example.com/x.png?v=2">
          <img src="/not-image.txt">
          <img src="/b.svg">
        </body></html>
        """
        mock_request.return_value = DummyResp(html)

        # Act
        urls = mod.list_images("https://example.com/page", respect_robots=False)

        # Assert
        self.assertEqual(len(urls), 3)
        self.assertIn("https://cdn.example.com/x.png?v=2", urls)
        self.assertIn("https://example.com/a.jpg", urls)
        self.assertIn("https://example.com/b.svg", urls)
        mock_request.assert_called_once_with("https://example.com/page")

    @mock.patch.object(mod, '_robots_allowed')
    @mock.patch.object(mod, '_download_image')
    def test_download_images_robots_txtで禁止されたURLをスキップする(
        self,
        mock_download: mock.Mock,
        mock_robots: mock.Mock
    ):
        # Arrange
        urls = [
            "https://example.com/a.jpg",
            "https://example.com/b.png",  # このURLはrobots.txtでブロックされる
            "https://example.com/c.svg",
        ]
        saved_paths = []

        def fake_download(url: str, dest_dir: str):
            p = Path(dest_dir) / ("file_" + Path(url).suffix)
            saved_paths.append(str(p))
            return str(p)

        def fake_robots(url: str, user_agent: str = mod.DEFAULT_HEADERS["User-Agent"]):
            # 2番目のURL (b.png) をブロック
            return not url.endswith("b.png")

        mock_download.side_effect = fake_download
        mock_robots.side_effect = fake_robots

        # Act
        out = mod.download_images(urls, "./.tmp_test_out")

        # Assert
        # 2番目のURLはrobots.txtでスキップされるため、2つのみダウンロード
        self.assertEqual(len(out), 2)
        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_robots.call_count, 3)  # 全URLに対してチェック
        self.assertTrue(all(s.endswith(('.jpg', '.png', '.svg', '.bin')) for s in saved_paths))


if __name__ == "__main__":
    unittest.main()
