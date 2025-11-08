import os
import json
import time
from pathlib import Path
import unittest

from src.lib.ui_helpers import (
    validate_json_text,
    mask_headers,
    build_full_url,
    load_config,
    save_config,
    summarize_response,
)


class TestUiHelpers(unittest.TestCase):
    def setUp(self):
        # use temp config dir override
        self.tmpdir = Path("./.tmp-test-config")
        os.environ["IMAGE_SAVER_CONFIG_DIR"] = str(self.tmpdir)
        if self.tmpdir.exists():
            for f in self.tmpdir.glob("*"):
                f.unlink()
        else:
            self.tmpdir.mkdir(parents=True)

    def tearDown(self):
        for f in self.tmpdir.glob("*"):
            f.unlink()
        self.tmpdir.rmdir()
        os.environ.pop("IMAGE_SAVER_CONFIG_DIR", None)

    def test_validate_json_text(self):
        ok, err = validate_json_text("")
        self.assertTrue(ok)
        self.assertIsNone(err)
        ok, err = validate_json_text("{\n  \"a\": 1\n}")
        self.assertTrue(ok)
        self.assertIsNone(err)
        ok, err = validate_json_text("{bad")
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_mask_headers(self):
        headers = {"Authorization": "Bearer 123", "X-Test": "ok", "Api-Key": "secret"}
        masked = mask_headers(headers)
        self.assertEqual(masked["Authorization"], "***")
        self.assertEqual(masked["Api-Key"], "***")
        self.assertEqual(masked["X-Test"], "ok")

    def test_build_full_url(self):
        url = build_full_url("https://example.com/", "api", {"q": "x y", "tags": [1, 2]})
        self.assertTrue(url.startswith("https://example.com/api?"))
        self.assertIn("q=x+y", url)
        self.assertIn("tags=1", url)
        self.assertIn("tags=2", url)

    def test_config_roundtrip(self):
        cfg = {"base_url": "http://localhost:8000", "recent": ["/healthz"]}
        save_config(cfg)
        loaded = load_config()
        self.assertEqual(cfg, loaded)

    def test_summarize_response(self):
        text = json.dumps({"hello": "world"})
        summary = summarize_response(200, 123, text, "application/json")
        self.assertEqual(summary["status"], 200)
        self.assertEqual(summary["body_type"], "json")
        self.assertIn("hello", summary["body_preview"])
        # Large body truncation
        big = "x" * 9000
        summary_big = summarize_response(200, 50, big, "text/plain")
        self.assertEqual(summary_big["body_type"], "text")
        self.assertTrue(summary_big["body_preview"].endswith("(truncated)"))


if __name__ == "__main__":
    unittest.main()
