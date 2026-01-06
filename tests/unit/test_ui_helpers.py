import json
import os
import tempfile
import unittest
from pathlib import Path

from src.lib.ui_helpers import (
    build_full_url,
    load_config,
    mask_headers,
    save_config,
    summarize_response,
    validate_json_text,
)


class TestUiHelpers(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)
        os.environ["IMAGE_SAVER_CONFIG_DIR"] = str(self.tmpdir)

    def tearDown(self):
        os.environ.pop("IMAGE_SAVER_CONFIG_DIR", None)
        self._tmpdir.cleanup()

    def test_空文字列を検証するとエラーなしで成功する(self):
        # Arrange
        text = ""

        # Act
        ok, err = validate_json_text(text)

        # Assert
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_正しいJSON文字列を検証するとエラーなしで成功する(self):
        # Arrange
        text = '{\n  "a": 1\n}'

        # Act
        ok, err = validate_json_text(text)

        # Assert
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_不正なJSON文字列を検証するとエラーが返る(self):
        # Arrange
        text = "{bad"

        # Act
        ok, err = validate_json_text(text)

        # Assert
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_機密情報を含むヘッダーがマスクされる(self):
        # Arrange
        headers = {"Authorization": "Bearer 123", "X-Test": "ok", "Api-Key": "secret"}

        # Act
        masked = mask_headers(headers)

        # Assert
        self.assertEqual(masked["Authorization"], "***")
        self.assertEqual(masked["Api-Key"], "***")
        self.assertEqual(masked["X-Test"], "ok")

    def test_ベースURLとパスとクエリパラメータから完全なURLが構築される(self):
        # Arrange
        base_url = "https://example.com/"
        path = "api"
        params = {"q": "x y", "tags": [1, 2]}

        # Act
        url = build_full_url(base_url, path, params)

        # Assert
        self.assertTrue(url.startswith("https://example.com/api?"))
        self.assertIn("q=x+y", url)
        self.assertIn("tags=1", url)
        self.assertIn("tags=2", url)

    def test_設定を保存して読み込むと元の設定が復元される(self):
        # Arrange
        cfg = {"base_url": "http://localhost:8000", "recent": ["/healthz"]}

        # Act
        save_config(cfg)
        loaded = load_config()

        # Assert
        self.assertEqual(cfg, loaded)

    def test_JSONレスポンスがサマリーとして整形される(self):
        # Arrange
        text = json.dumps({"hello": "world"})
        status = 200
        elapsed_ms = 123
        content_type = "application/json"

        # Act
        summary = summarize_response(status, elapsed_ms, text, content_type)

        # Assert
        self.assertEqual(summary["status"], 200)
        self.assertEqual(summary["body_type"], "json")
        self.assertIn("hello", summary["body_preview"])

    def test_大きなレスポンスボディがトランケートされる(self):
        # Arrange
        big = "x" * 9000
        status = 200
        elapsed_ms = 50
        content_type = "text/plain"

        # Act
        summary = summarize_response(status, elapsed_ms, big, content_type)

        # Assert
        self.assertEqual(summary["body_type"], "text")
        self.assertTrue(summary["body_preview"].endswith("(truncated)"))


if __name__ == "__main__":
    unittest.main()
