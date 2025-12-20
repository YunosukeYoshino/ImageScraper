import time
import unittest
from unittest import mock

from src.lib import image_scraper as mod


class TestParallelDownload(unittest.TestCase):
    @mock.patch.object(mod, '_robots_allowed')
    @mock.patch.object(mod, '_download_image')
    def test_複数URLを並列ダウンロードし進捗コールバックが完了まで実行される(
        self,
        mock_download_image,
        mock_robots_allowed
    ):
        # Arrange: テスト対象データとモックを準備
        urls = [f"https://example.com/{i}.jpg" for i in range(6)]
        calls = []

        def fake_download(u: str, dest: str):
            time.sleep(0.01)
            calls.append(u)
            return f"{dest}/x{len(calls)}.jpg"

        mock_download_image.side_effect = fake_download
        mock_robots_allowed.return_value = True

        progresses = []
        def progress_callback(done, total):
            progresses.append((done, total))

        # Act: 並列ダウンロードを実行
        result = mod.download_images_parallel(
            urls,
            "./.tmp_test_out",
            max_workers=3,
            respect_robots=True,
            progress_cb=progress_callback
        )

        # Assert: 結果と進捗を検証
        self.assertEqual(len(result), len(urls), "ダウンロード結果の数がURLの数と一致すること")
        self.assertTrue(progresses, "進捗コールバックが少なくとも1回呼ばれること")
        self.assertEqual(progresses[-1][0], len(urls), "最終進捗の完了数が総数と一致すること")
        self.assertEqual(progresses[-1][1], len(urls), "最終進捗の総数が期待値と一致すること")


if __name__ == "__main__":
    unittest.main()
