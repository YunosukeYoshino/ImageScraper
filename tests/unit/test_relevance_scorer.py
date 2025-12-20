"""Unit tests for relevance scoring module."""
from __future__ import annotations
import unittest

from src.lib.relevance_scorer import (
    calculate_relevance_score,
    extract_filename_from_url,
    extract_domain_from_url,
    _tokenize,
    _calculate_match_ratio,
    _score_domain,
)


class TestTokenize(unittest.TestCase):
    """Tests for _tokenize function."""

    def test_empty_string(self):
        self.assertEqual(_tokenize(""), [])

    def test_none_input(self):
        self.assertEqual(_tokenize(None), [])

    def test_english_words(self):
        tokens = _tokenize("Hello World Test")
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)
        self.assertIn("test", tokens)

    def test_japanese_words(self):
        tokens = _tokenize("富士山 紅葉")
        self.assertIn("富士山", tokens)
        self.assertIn("紅葉", tokens)

    def test_mixed_language(self):
        tokens = _tokenize("富士山 Mount Fuji")
        self.assertIn("富士山", tokens)
        self.assertIn("mount", tokens)
        self.assertIn("fuji", tokens)

    def test_single_char_filtered(self):
        tokens = _tokenize("a b c test")
        self.assertIn("test", tokens)
        self.assertNotIn("a", tokens)


class TestCalculateMatchRatio(unittest.TestCase):
    """Tests for _calculate_match_ratio function."""

    def test_full_match(self):
        tokens = ["hello", "world"]
        text = "hello world example"
        self.assertEqual(_calculate_match_ratio(tokens, text), 1.0)

    def test_partial_match(self):
        tokens = ["hello", "world"]
        text = "hello example"
        self.assertEqual(_calculate_match_ratio(tokens, text), 0.5)

    def test_no_match(self):
        tokens = ["hello", "world"]
        text = "example text"
        self.assertEqual(_calculate_match_ratio(tokens, text), 0.0)

    def test_empty_tokens(self):
        self.assertEqual(_calculate_match_ratio([], "hello"), 0.0)

    def test_empty_text(self):
        self.assertEqual(_calculate_match_ratio(["hello"], ""), 0.0)


class TestScoreDomain(unittest.TestCase):
    """Tests for _score_domain function."""

    def test_trusted_domain(self):
        self.assertEqual(_score_domain("wikimedia.org"), 1.0)
        self.assertEqual(_score_domain("upload.wikimedia.org"), 1.0)
        self.assertEqual(_score_domain("pixabay.com"), 1.0)

    def test_untrusted_domain(self):
        self.assertEqual(_score_domain("example.com"), 0.0)
        self.assertEqual(_score_domain("random-site.net"), 0.0)

    def test_empty_domain(self):
        self.assertEqual(_score_domain(""), 0.0)
        self.assertEqual(_score_domain(None), 0.0)


class TestExtractFilenameFromUrl(unittest.TestCase):
    """Tests for extract_filename_from_url function."""

    def test_simple_url(self):
        url = "https://example.com/images/photo.jpg"
        self.assertEqual(extract_filename_from_url(url), "photo.jpg")

    def test_url_with_query(self):
        url = "https://example.com/images/photo.jpg?width=100"
        self.assertEqual(extract_filename_from_url(url), "photo.jpg")

    def test_empty_url(self):
        self.assertIsNone(extract_filename_from_url(""))
        self.assertIsNone(extract_filename_from_url(None))


class TestExtractDomainFromUrl(unittest.TestCase):
    """Tests for extract_domain_from_url function."""

    def test_simple_url(self):
        url = "https://example.com/path"
        self.assertEqual(extract_domain_from_url(url), "example.com")

    def test_subdomain(self):
        url = "https://upload.wikimedia.org/image.png"
        self.assertEqual(extract_domain_from_url(url), "upload.wikimedia.org")

    def test_empty_url(self):
        self.assertIsNone(extract_domain_from_url(""))
        self.assertIsNone(extract_domain_from_url(None))


class TestCalculateRelevanceScore(unittest.TestCase):
    """Tests for calculate_relevance_score function."""

    def test_empty_topic(self):
        score = calculate_relevance_score("", alt_text="test")
        self.assertEqual(score, 0.0)

    def test_high_relevance_alt_match(self):
        # Alt text has weight 0.4
        score = calculate_relevance_score(
            topic="富士山",
            alt_text="富士山の美しい写真",
            filename=None,
            context_text=None,
            domain=None,
        )
        self.assertGreaterEqual(score, 0.4)

    def test_high_relevance_filename_match(self):
        # Filename has weight 0.3
        score = calculate_relevance_score(
            topic="fuji",
            alt_text=None,
            filename="fuji_mountain.jpg",
            context_text=None,
            domain=None,
        )
        self.assertGreaterEqual(score, 0.3)

    def test_trusted_domain_bonus(self):
        # Domain has weight 0.1
        score = calculate_relevance_score(
            topic="test",
            alt_text=None,
            filename=None,
            context_text=None,
            domain="wikimedia.org",
        )
        self.assertEqual(score, 0.1)

    def test_combined_score(self):
        # All factors contribute
        score = calculate_relevance_score(
            topic="富士山",
            alt_text="富士山の写真",
            filename="fujisan.jpg",
            context_text="美しい富士山の風景",
            domain="wikimedia.org",
        )
        # Should be close to 1.0 with all matches
        self.assertGreater(score, 0.5)

    def test_no_match(self):
        score = calculate_relevance_score(
            topic="富士山",
            alt_text="cat photo",
            filename="cat.jpg",
            context_text="A cute cat",
            domain="example.com",
        )
        self.assertEqual(score, 0.0)

    def test_score_clamped_to_max(self):
        # Score should never exceed 1.0
        score = calculate_relevance_score(
            topic="test",
            alt_text="test test test test",
            filename="test.jpg",
            context_text="test test test",
            domain="pixabay.com",
        )
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
