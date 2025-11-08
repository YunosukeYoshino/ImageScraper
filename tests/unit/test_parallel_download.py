import time
import unittest

from src.lib import image_scraper as mod


class TestParallelDownload(unittest.TestCase):
    def test_parallel_progress_and_output(self):
        urls = [f"https://example.com/{i}.jpg" for i in range(6)]
        calls = []
        def fake_download(u: str, dest: str):
            time.sleep(0.01)
            calls.append(u)
            return f"{dest}/x{i if (i:=len(calls)) else 0}.jpg"

        progresses = []
        def cb(done, total):
            progresses.append((done, total))

        old_dl = mod._download_image
        old_robot = mod._robots_allowed
        mod._download_image = fake_download
        mod._robots_allowed = lambda u, user_agent=mod.DEFAULT_HEADERS["User-Agent"]: True
        try:
            out = mod.download_images_parallel(urls, "./.tmp_test_out", max_workers=3, respect_robots=True, progress_cb=cb)
        finally:
            mod._download_image = old_dl
            mod._robots_allowed = old_robot

        self.assertEqual(len(out), len(urls))
        # progress should have advanced to total
        self.assertTrue(progresses)
        self.assertEqual(progresses[-1][0], len(urls))
        self.assertEqual(progresses[-1][1], len(urls))


if __name__ == "__main__":
    unittest.main()
