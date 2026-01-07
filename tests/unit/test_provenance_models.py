import unittest
from datetime import datetime

from src.lib.models_discovery import PreviewResult, ProvenanceEntry, QueryLogEntry


class TestProvenanceModels(unittest.TestCase):
    def test_provenance_entry_fields(self):
        entry = ProvenanceEntry(
            topic="富士山",
            source_page_url="https://example.com/page",  # type: ignore[arg-type]
            image_url="https://example.com/img.jpg",  # type: ignore[arg-type]
            discovery_method="SERP",
        )
        self.assertIsInstance(entry.timestamp, datetime)
        self.assertEqual(entry.topic, "富士山")

    def test_query_log_entry_defaults(self):
        log = QueryLogEntry(topic="富士山", provider="duckduckgo", query="富士山")
        self.assertEqual(log.page_count, 0)
        self.assertEqual(log.image_count, 0)
        self.assertIsInstance(log.timestamp, datetime)

    def test_preview_result_to_dict(self):
        entry = ProvenanceEntry(
            topic="富士山",
            source_page_url="https://example.com/page",  # type: ignore[arg-type]
            image_url="https://example.com/img.jpg",  # type: ignore[arg-type]
            discovery_method="SERP",
        )
        log = QueryLogEntry(topic="富士山", provider="duckduckgo", query="富士山")
        preview = PreviewResult(
            topic="富士山",
            entries=[entry],
            total_images=1,
            provider="duckduckgo",
            query_log=log,
        )
        d = preview.to_dict()
        self.assertEqual(d["total_images"], 1)
        self.assertIn("entries", d)
        self.assertEqual(d["entries"][0]["topic"], "富士山")


if __name__ == "__main__":
    unittest.main()
