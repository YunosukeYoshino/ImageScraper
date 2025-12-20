import os
import json
import types
from unittest import TestCase, mock
from fastapi.testclient import TestClient

# We will import app after creating src/api/app.py
try:
    from src.api.app import app
except Exception:
    app = None

class TestAPI(TestCase):
    def setUp(self):
        if app is None:
            self.skipTest("API app not yet implemented")
        self.client = TestClient(app)

    def test_healthzエンドポイントが正常ステータスを返す(self):
        # Arrange (なし)

        # Act
        r = self.client.get("/healthz")

        # Assert
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("status"), "ok")

    def test_不正なURL形式でリクエストすると422エラーを返す(self):
        # Arrange
        invalid_payload = {"url": "not-a-url"}

        # Act
        r = self.client.post("/scrape", json=invalid_payload)

        # Assert
        # FastAPI/Pydantic invalid URL -> 422 Unprocessable Entity by default
        self.assertEqual(r.status_code, 422)

    @mock.patch("src.api.app.scrape_images")
    def test_robots_txtで禁止されている場合403エラーを返す(self, mock_scrape):
        # Arrange
        mock_scrape.side_effect = PermissionError("Blocked by robots.txt: https://example.com")
        payload = {"url": "https://example.com"}

        # Act
        r = self.client.post("/scrape", json=payload)

        # Assert
        self.assertEqual(r.status_code, 403)
        self.assertIn("robots.txt", r.json().get("message", ""))

    @mock.patch("src.api.app.scrape_images")
    def test_画像スクレイピングが成功すると200と結果を返す(self, mock_scrape):
        # Arrange
        fake_result = types.SimpleNamespace(
            page_url="https://example.com",
            image_urls=["https://example.com/a.png"],
            saved_files=["images/abc.png"],
            drive_file_ids=[],
        )
        mock_scrape.return_value = fake_result
        payload = {"url": "https://example.com"}

        # Act
        r = self.client.post("/scrape", json=payload)

        # Assert
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("saved"), 1)
        self.assertEqual(data.get("failed"), 0)
        self.assertEqual(data.get("output_dir"), "./images")
        self.assertIn("images/abc.png", data.get("files", []))
