"""Unit tests for relevance scoring module.

t.wada流テスト哲学に基づき、公開APIの振る舞いのみをテスト。
private関数(_tokenize, _calculate_match_ratio, _score_domain)は
公開API経由で間接的に検証される。
"""
from __future__ import annotations
import unittest

from src.lib.domain.services import (
    calculate_relevance_score,
    extract_filename_from_url,
    extract_domain_from_url,
)


class TestCalculateRelevanceScore(unittest.TestCase):
    """関連性スコア計算の振る舞いテスト."""

    def test_空トピックの場合スコアは0(self):
        """空文字列やNoneのトピックは0を返す."""
        self.assertEqual(calculate_relevance_score("", alt_text="test"), 0.0)
        self.assertEqual(calculate_relevance_score("   ", alt_text="test"), 0.0)

    def test_トピックと完全一致しない場合スコアは0(self):
        """どのフィールドにもトピックが含まれない場合は0."""
        score = calculate_relevance_score(
            topic="富士山",
            alt_text="cat photo",
            filename="cat.jpg",
            context_text="A cute cat",
            domain="example.com",
        )
        self.assertEqual(score, 0.0)

    def test_alt属性のみ一致の場合適切なスコア(self):
        """alt属性の重みは0.4で、完全一致時は0.4以上."""
        score = calculate_relevance_score(
            topic="富士山",
            alt_text="富士山の美しい写真",
        )
        self.assertGreaterEqual(score, 0.4)

    def test_ファイル名のみ一致の場合適切なスコア(self):
        """ファイル名の重みは0.3で、完全一致時は0.3以上."""
        score = calculate_relevance_score(
            topic="fuji",
            filename="fuji_mountain.jpg",
        )
        self.assertGreaterEqual(score, 0.3)

    def test_コンテキストのみ一致の場合適切なスコア(self):
        """周辺テキストの重みは0.2で、完全一致時は0.2以上."""
        score = calculate_relevance_score(
            topic="富士山",
            context_text="富士山の風景写真集",
        )
        self.assertGreaterEqual(score, 0.2)

    def test_信頼ドメインのみの場合適切なスコア(self):
        """信頼ドメインの重みは0.1(他が不一致でも加算)."""
        score = calculate_relevance_score(
            topic="test",
            domain="wikimedia.org",
        )
        self.assertEqual(score, 0.1)

    def test_信頼ドメインのサブドメイン判定(self):
        """upload.wikimedia.orgなどのサブドメインも信頼される."""
        score = calculate_relevance_score(
            topic="test",
            domain="upload.wikimedia.org",
        )
        self.assertEqual(score, 0.1)

    def test_複数フィールド一致時のスコア合成(self):
        """すべてのフィールドが一致する場合、高スコアを返す."""
        score = calculate_relevance_score(
            topic="富士山",
            alt_text="富士山の写真",
            filename="fujisan.jpg",
            context_text="美しい富士山の風景",
            domain="wikimedia.org",
        )
        self.assertGreater(score, 0.5)

    def test_部分一致でも適切にスコアリング(self):
        """トピック「富士山 紅葉」のうち「富士山」のみ一致でも部分点."""
        score = calculate_relevance_score(
            topic="富士山 紅葉",
            alt_text="富士山の写真",
        )
        # 2トークンのうち1つ一致 = 0.5 * 0.4(alt weight) = 0.2
        self.assertGreater(score, 0.0)
        self.assertLess(score, 0.4)

    def test_英語と日本語の混在トピック(self):
        """「富士山 Mount Fuji」のような混在トピックも適切に処理."""
        score = calculate_relevance_score(
            topic="富士山 Mount Fuji",
            alt_text="富士山 Mount Fuji beautiful view",
        )
        self.assertGreater(score, 0.0)

    def test_大文字小文字を区別しない(self):
        """英語トピックは大文字小文字を区別しない."""
        score_lower = calculate_relevance_score(
            topic="fuji",
            alt_text="FUJI Mountain",
        )
        score_upper = calculate_relevance_score(
            topic="FUJI",
            alt_text="fuji mountain",
        )
        self.assertEqual(score_lower, score_upper)

    def test_単一文字トークンは無視される(self):
        """'a'や'I'などの単一文字はトークン化時にフィルタリング."""
        score = calculate_relevance_score(
            topic="a b c test",
            alt_text="test image",
        )
        # 'test'のみ有効トークン → 完全一致で0.4
        self.assertGreaterEqual(score, 0.4)

    def test_スコアは最大1_0に制限(self):
        """重み合計が1.0を超えることはない."""
        score = calculate_relevance_score(
            topic="test",
            alt_text="test test test test",
            filename="test.jpg",
            context_text="test test test",
            domain="pixabay.com",
        )
        self.assertLessEqual(score, 1.0)

    def test_すべてNoneの場合スコアは0(self):
        """トピック以外すべてNoneでもエラーにならず0を返す."""
        score = calculate_relevance_score(topic="test")
        self.assertEqual(score, 0.0)


class TestExtractFilenameFromUrl(unittest.TestCase):
    """URLからファイル名を抽出する振る舞いテスト."""

    def test_シンプルなURL(self):
        """通常のパス構造からファイル名を抽出."""
        url = "https://example.com/images/photo.jpg"
        self.assertEqual(extract_filename_from_url(url), "photo.jpg")

    def test_クエリパラメータ付きURL(self):
        """クエリパラメータは除去される."""
        url = "https://example.com/images/photo.jpg?width=100&height=200"
        self.assertEqual(extract_filename_from_url(url), "photo.jpg")

    def test_日本語ファイル名を含むURL(self):
        """URLエンコードされた日本語ファイル名も抽出可能."""
        url = "https://example.com/images/富士山.jpg"
        self.assertEqual(extract_filename_from_url(url), "富士山.jpg")

    def test_ネストされたパス(self):
        """深い階層のファイルも最後のセグメントを抽出."""
        url = "https://example.com/a/b/c/d/image.png"
        self.assertEqual(extract_filename_from_url(url), "image.png")

    def test_空URLはNoneを返す(self):
        """空文字列やNoneは安全にNoneを返す."""
        self.assertIsNone(extract_filename_from_url(""))
        self.assertIsNone(extract_filename_from_url(None))

    def test_パスがない場合はNone(self):
        """ドメインのみのURLはNoneを返す."""
        url = "https://example.com"
        self.assertIsNone(extract_filename_from_url(url))

    def test_パスがスラッシュのみの場合はNone(self):
        """パスが'/'のみの場合はNoneを返す."""
        url = "https://example.com/"
        self.assertIsNone(extract_filename_from_url(url))


class TestExtractDomainFromUrl(unittest.TestCase):
    """URLからドメインを抽出する振る舞いテスト."""

    def test_シンプルなURL(self):
        """通常のURLからドメインを抽出."""
        url = "https://example.com/path/to/resource"
        self.assertEqual(extract_domain_from_url(url), "example.com")

    def test_サブドメイン付きURL(self):
        """サブドメインを含むドメインを完全に抽出."""
        url = "https://upload.wikimedia.org/image.png"
        self.assertEqual(extract_domain_from_url(url), "upload.wikimedia.org")

    def test_ポート番号付きURL(self):
        """ポート番号もnetlocに含まれる."""
        url = "http://localhost:8000/api/test"
        self.assertEqual(extract_domain_from_url(url), "localhost:8000")

    def test_空URLはNoneを返す(self):
        """空文字列やNoneは安全にNoneを返す."""
        self.assertIsNone(extract_domain_from_url(""))
        self.assertIsNone(extract_domain_from_url(None))

    def test_不正なURLでもエラーにならない(self):
        """パース失敗時もエラーを投げずに結果を返す."""
        # urllibは寛容なので、スキームのない文字列もパースされる場合がある
        # 重要なのはエラーを投げないこと
        result = extract_domain_from_url("not-a-valid-url")
        # resultがNoneでもstrでもエラーにならないことを確認
        self.assertIn(type(result), [type(None), str])


if __name__ == "__main__":
    unittest.main()
