import json
import os
import tempfile
import unittest
from unittest.mock import patch, Mock, MagicMock

from src.lib.topic_discovery import (
    discover_topic,
    filter_entries,
    download_selected,
    _DISCOVERY_LOG_DIR,
)
from src.lib.models_discovery import PreviewResult, ProvenanceEntry, DownloadFilter


class TestTopicDiscovery(unittest.TestCase):
    """Test topic discovery orchestrator with mocked search provider."""

    @patch("src.lib.topic_discovery.search_provider.search_pages")
    @patch("src.lib.topic_discovery.list_images")
    @patch("src.lib.topic_discovery.robots_allowed")
    def test_discover_topic_with_mocked_provider(self, mock_robots, mock_list, mock_search):
        """Test that discover_topic collects images from search results."""
        mock_search.return_value = ["https://example.com/page1", "https://example.com/page2"]
        mock_robots.return_value = True
        mock_list.side_effect = [
            ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            ["https://example.com/img3.jpg"],
        ]

        result = discover_topic("test topic", limit=10)

        self.assertIsInstance(result, PreviewResult)
        self.assertEqual(result.topic, "test topic")
        self.assertEqual(result.total_images, 3)
        self.assertEqual(len(result.entries), 3)
        # Verify provenance - convert HttpUrl to str for comparison
        for entry in result.entries:
            self.assertEqual(entry.topic, "test topic")
            self.assertIn("example.com", str(entry.source_page_url))

    @patch("src.lib.topic_discovery.search_provider.search_pages")
    @patch("src.lib.topic_discovery.list_images")
    @patch("src.lib.topic_discovery.robots_allowed")
    def test_robots_disallowed_pages_skipped(self, mock_robots, mock_list, mock_search):
        """Test that pages disallowed by robots.txt are skipped."""
        mock_search.return_value = ["https://blocked.com/", "https://allowed.com/"]
        # First page blocked, second allowed
        mock_robots.side_effect = [False, True]
        mock_list.return_value = ["https://allowed.com/img.jpg"]

        result = discover_topic("test", limit=10)

        # Only one page was allowed, so only images from that page
        self.assertEqual(result.total_images, 1)
        self.assertEqual(str(result.entries[0].source_page_url), "https://allowed.com/")

    @patch("src.lib.topic_discovery.search_provider.search_pages")
    def test_discover_topic_empty_when_no_results(self, mock_search):
        """Test that empty result is returned when search returns nothing."""
        mock_search.return_value = []

        result = discover_topic("no results topic", limit=10)

        self.assertIsInstance(result, PreviewResult)
        self.assertEqual(result.total_images, 0)
        self.assertEqual(result.query_log.topic, "no results topic")

    @patch("src.lib.topic_discovery.search_provider.search_pages")
    @patch("src.lib.topic_discovery.list_images")
    @patch("src.lib.topic_discovery.robots_allowed")
    def test_limit_respected(self, mock_robots, mock_list, mock_search):
        """Test that image limit is respected."""
        mock_search.return_value = ["https://example.com/page1", "https://example.com/page2"]
        mock_robots.return_value = True
        # Each page returns 5 images
        mock_list.return_value = [f"https://example.com/img{i}.jpg" for i in range(5)]

        result = discover_topic("test", limit=3)

        # Should stop at limit
        self.assertEqual(result.total_images, 3)

    @patch("src.lib.topic_discovery.search_provider.search_pages")
    @patch("src.lib.topic_discovery.list_images")
    @patch("src.lib.topic_discovery.robots_allowed")
    @patch("src.lib.topic_discovery.logger")
    def test_logging_called(self, mock_logger, mock_robots, mock_list, mock_search):
        """Test that proper logging is performed."""
        mock_search.return_value = []

        discover_topic("桜", limit=5)

        # Ensure start/end logs invoked
        calls = [c.args for c in mock_logger.info.call_args_list]
        start = any("discover_topic.start" in (args[0] if args else "") for args in calls)
        end = any("discover_topic.end" in (args[0] if args else "") for args in calls)
        self.assertTrue(start and end)

    @patch("src.lib.topic_discovery.search_provider.search_pages")
    @patch("src.lib.topic_discovery.list_images")
    @patch("src.lib.topic_discovery.robots_allowed")
    def test_query_log_written(self, mock_robots, mock_list, mock_search):
        """Test that query log file is created."""
        mock_search.return_value = ["https://example.com/"]
        mock_robots.return_value = True
        mock_list.return_value = ["https://example.com/img.jpg"]

        result = discover_topic("テストトピック", limit=10)

        # Check that query_log has expected fields
        self.assertEqual(result.query_log.topic, "テストトピック")
        self.assertEqual(result.query_log.provider, "duckduckgo")
        self.assertGreaterEqual(result.query_log.page_count, 0)


class TestSearchProvider(unittest.TestCase):
    """Test search_provider module in isolation."""

    def test_search_pages_empty_topic(self):
        from src.lib import search_provider
        result = search_provider.search_pages("", max_pages=5)
        self.assertEqual(result, [])

    def test_search_pages_unsupported_provider(self):
        from src.lib import search_provider
        result = search_provider.search_pages("test", provider="unknown", max_pages=5)
        self.assertEqual(result, [])


class TestFilterEntries(unittest.TestCase):
    """Test US2 filter_entries function."""

    def _make_entry(self, image_url: str, source_page_url: str = "https://example.com/") -> ProvenanceEntry:
        return ProvenanceEntry(
            topic="test",
            source_page_url=source_page_url,
            image_url=image_url,
            discovery_method="SERP",
        )

    def test_filter_no_filter_returns_all(self):
        """Without filter, all entries should be returned."""
        entries = [
            self._make_entry("https://a.com/img1.jpg"),
            self._make_entry("https://b.com/img2.jpg"),
        ]
        result = filter_entries(entries, None)
        self.assertEqual(len(result), 2)

    def test_filter_allow_domains(self):
        """Only entries from allowed domains should pass."""
        entries = [
            self._make_entry("https://allowed.com/img1.jpg"),
            self._make_entry("https://blocked.com/img2.jpg"),
            self._make_entry("https://sub.allowed.com/img3.jpg"),
        ]
        flt = DownloadFilter(allow_domains=["allowed.com"])
        result = filter_entries(entries, flt)
        self.assertEqual(len(result), 2)
        urls = [str(e.image_url) for e in result]
        self.assertIn("https://allowed.com/img1.jpg", urls)
        self.assertIn("https://sub.allowed.com/img3.jpg", urls)

    def test_filter_deny_domains(self):
        """Entries from denied domains should be excluded."""
        entries = [
            self._make_entry("https://good.com/img1.jpg"),
            self._make_entry("https://spam.com/img2.jpg"),
            self._make_entry("https://ads.spam.com/img3.jpg"),
        ]
        flt = DownloadFilter(deny_domains=["spam.com"])
        result = filter_entries(entries, flt)
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0].image_url), "https://good.com/img1.jpg")

    def test_filter_combined_allow_and_deny(self):
        """When both allow and deny are set, apply both."""
        entries = [
            self._make_entry("https://good.com/img1.jpg"),
            self._make_entry("https://ads.good.com/img2.jpg"),  # subdomain of allowed, but also denied
            self._make_entry("https://other.com/img3.jpg"),
        ]
        flt = DownloadFilter(allow_domains=["good.com"], deny_domains=["ads.good.com"])
        result = filter_entries(entries, flt)
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0].image_url), "https://good.com/img1.jpg")


class TestDownloadSelected(unittest.TestCase):
    """Test US2 download_selected function."""

    def _make_entry(self, image_url: str) -> ProvenanceEntry:
        return ProvenanceEntry(
            topic="test",
            source_page_url="https://example.com/",
            image_url=image_url,
            discovery_method="SERP",
        )

    @patch("src.lib.topic_discovery.download_images_parallel")
    def test_download_selected_creates_provenance_index(self, mock_download):
        """Test that provenance_index.json is created."""
        import hashlib

        url1 = "https://example.com/img1.jpg"
        url2 = "https://example.com/img2.jpg"
        entries = [
            self._make_entry(url1),
            self._make_entry(url2),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate correct hash-based filenames
            hash1 = hashlib.sha256(url1.encode("utf-8")).hexdigest()[:16]
            hash2 = hashlib.sha256(url2.encode("utf-8")).hexdigest()[:16]

            # Mock download to return fake file paths with correct hash names
            mock_download.return_value = [
                os.path.join(tmpdir, f"{hash1}.jpg"),
                os.path.join(tmpdir, f"{hash2}.jpg"),
            ]
            # Create fake files so provenance check passes
            for p in mock_download.return_value:
                with open(p, "wb") as f:
                    f.write(b"fake")

            saved, index_path = download_selected(entries, tmpdir)

            self.assertEqual(len(saved), 2)
            self.assertTrue(os.path.exists(index_path))

            with open(index_path, "r") as f:
                index_data = json.load(f)

            self.assertIn("entries", index_data)
            self.assertIn("total", index_data)
            self.assertIn("generated_at", index_data)

    @patch("src.lib.topic_discovery.download_images_parallel")
    def test_download_selected_applies_filter(self, mock_download):
        """Test that domain filter is applied before download."""
        entries = [
            self._make_entry("https://good.com/img1.jpg"),
            self._make_entry("https://spam.com/img2.jpg"),
        ]
        flt = DownloadFilter(deny_domains=["spam.com"])

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_download.return_value = []

            download_selected(entries, tmpdir, download_filter=flt)

            # Check that only good.com was passed to download
            call_args = mock_download.call_args
            urls_passed = call_args[0][0]  # First positional arg
            self.assertEqual(len(urls_passed), 1)
            self.assertIn("good.com", urls_passed[0])

    def test_download_selected_empty_entries_still_writes_index(self):
        """Even with no entries, provenance_index.json should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            saved, index_path = download_selected([], tmpdir)

            self.assertEqual(saved, [])
            self.assertTrue(os.path.exists(index_path))

            with open(index_path, "r") as f:
                index_data = json.load(f)

            self.assertEqual(index_data["entries"], [])
            self.assertEqual(index_data["total"], 0)


class TestResolutionFilter(unittest.TestCase):
    """Test resolution filtering (min_width/min_height) in download_selected."""

    def _make_entry(self, image_url: str) -> ProvenanceEntry:
        return ProvenanceEntry(
            topic="test",
            source_page_url="https://example.com/",
            image_url=image_url,
            discovery_method="SERP",
        )

    @patch("src.lib.topic_discovery._check_image_resolution")
    @patch("src.lib.topic_discovery.download_images_parallel")
    def test_resolution_filter_removes_small_images(self, mock_download, mock_check):
        """Test that images not meeting resolution requirements are removed."""
        import hashlib

        url1 = "https://example.com/large.jpg"
        url2 = "https://example.com/small.jpg"
        entries = [
            self._make_entry(url1),
            self._make_entry(url2),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            hash1 = hashlib.sha256(url1.encode("utf-8")).hexdigest()[:16]
            hash2 = hashlib.sha256(url2.encode("utf-8")).hexdigest()[:16]
            file1 = os.path.join(tmpdir, f"{hash1}.jpg")
            file2 = os.path.join(tmpdir, f"{hash2}.jpg")

            # Mock download returns both files
            mock_download.return_value = [file1, file2]

            # Create fake files
            for p in [file1, file2]:
                with open(p, "wb") as f:
                    f.write(b"fake")

            # Mock resolution check: first passes, second fails
            mock_check.side_effect = [True, False]

            flt = DownloadFilter(min_width=800, min_height=600)
            saved, index_path = download_selected(entries, tmpdir, download_filter=flt)

            # Only large image should remain
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0], file1)

            # Small image file should be removed
            self.assertFalse(os.path.exists(file2))

    @patch("src.lib.topic_discovery.download_images_parallel")
    def test_no_resolution_filter_keeps_all(self, mock_download):
        """Test that without resolution filter, all images are kept."""
        import hashlib

        url1 = "https://example.com/img1.jpg"
        entries = [self._make_entry(url1)]

        with tempfile.TemporaryDirectory() as tmpdir:
            hash1 = hashlib.sha256(url1.encode("utf-8")).hexdigest()[:16]
            file1 = os.path.join(tmpdir, f"{hash1}.jpg")

            mock_download.return_value = [file1]

            with open(file1, "wb") as f:
                f.write(b"fake")

            # No filter - should keep all
            saved, _ = download_selected(entries, tmpdir)
            self.assertEqual(len(saved), 1)


if __name__ == "__main__":
    unittest.main()
