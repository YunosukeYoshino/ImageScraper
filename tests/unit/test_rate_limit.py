import unittest
from unittest import mock

from src.lib.application.services.rate_limiter import TokenBucket


class TestTokenBucket(unittest.TestCase):
    """TokenBucket レートリミッターのテスト

    t.wada流テスト哲学に従い、時間依存を排除した確定的テストを実装。
    """

    def test_初期状態で容量分のトークンを取得できる(self):
        """
        Given: capacity=2 のTokenBucketを作成
        When: 2回連続でnon_blocking_try_acquire()を呼ぶ
        Then: 両方とも成功する
        """
        # Arrange
        tb = TokenBucket(capacity=2, fill_rate=10)

        # Act & Assert
        self.assertTrue(tb.non_blocking_try_acquire())
        self.assertTrue(tb.non_blocking_try_acquire())

    def test_容量を超えるとトークン取得に失敗する(self):
        """
        Given: capacity=2 のTokenBucketからトークンを2個取得済み
        When: 3個目のトークンを取得しようとする
        Then: 失敗する（False）
        """
        # Arrange
        tb = TokenBucket(capacity=2, fill_rate=10)
        tb.non_blocking_try_acquire()
        tb.non_blocking_try_acquire()

        # Act
        result = tb.non_blocking_try_acquire()

        # Assert
        self.assertFalse(result)

    @mock.patch('src.lib.application.services.rate_limiter.time')
    def test_時間経過でトークンが補充される(self, mock_time):
        """
        Given: capacity=2, fill_rate=10 のTokenBucketからトークンを2個取得済み
        When: 0.1秒経過する（10 tokens/sec なので1トークン補充される）
        Then: トークン取得に成功する
        """
        # Arrange: 時刻を固定し、初期状態でトークンを使い切る
        mock_time.monotonic.return_value = 0.0
        tb = TokenBucket(capacity=2, fill_rate=10)
        tb.non_blocking_try_acquire()
        tb.non_blocking_try_acquire()
        self.assertFalse(tb.non_blocking_try_acquire())  # 空を確認

        # Act: 0.1秒経過させてトークン取得を試みる
        mock_time.monotonic.return_value = 0.1  # +0.1秒 → 1トークン補充
        result = tb.non_blocking_try_acquire()

        # Assert
        self.assertTrue(result)

    @mock.patch('src.lib.application.services.rate_limiter.time')
    def test_補充レートを超える時間が経過しても容量以上には補充されない(self, mock_time):
        """
        Given: capacity=2, fill_rate=10 のTokenBucketからトークンを2個取得済み
        When: 1秒経過する（本来10トークン補充されるが、容量は2）
        Then: 2個までしか取得できない
        """
        # Arrange
        mock_time.monotonic.return_value = 0.0
        tb = TokenBucket(capacity=2, fill_rate=10)
        tb.non_blocking_try_acquire()
        tb.non_blocking_try_acquire()

        # Act: 1秒経過させる
        mock_time.monotonic.return_value = 1.0

        # Assert: 2個取得できるが、3個目は失敗
        self.assertTrue(tb.non_blocking_try_acquire())
        self.assertTrue(tb.non_blocking_try_acquire())
        self.assertFalse(tb.non_blocking_try_acquire())

    @mock.patch('src.lib.application.services.rate_limiter.time')
    def test_acquire_はトークンが利用可能になるまでポーリングする(self, mock_time):
        """
        Given: capacity=1, fill_rate=2 のTokenBucketからトークンを取得済み
        When: acquire()を呼び、time.sleep()が呼ばれるたびに時刻を進める
        Then: トークンが補充されたタイミングで正常に取得できる
        """
        # Arrange
        current_time = 0.0
        mock_time.monotonic.side_effect = lambda: current_time

        sleep_calls = []
        def mock_sleep(duration):
            nonlocal current_time
            sleep_calls.append(duration)
            # sleep()が呼ばれたら、トークンが補充される時刻まで進める
            current_time += 0.5  # fill_rate=2 なので0.5秒で1トークン補充

        mock_time.sleep = mock_sleep

        tb = TokenBucket(capacity=1, fill_rate=2)
        tb.non_blocking_try_acquire()  # 初期トークンを消費

        # Act: acquire()を呼ぶとポーリング＋sleepが発生する
        tb.acquire()

        # Assert: sleep()が少なくとも1回呼ばれ、取得に成功したこと
        self.assertGreater(len(sleep_calls), 0, "sleep()が呼ばれるべき")

    @mock.patch('src.lib.application.services.rate_limiter.time')
    def test_acquire_はタイムアウト時にTimeoutErrorを発生させる(self, mock_time):
        """
        Given: capacity=1 のTokenBucketからトークンを取得済み
        When: timeout=0.1秒でacquire()を呼び、時刻を0.2秒進める
        Then: TimeoutErrorが発生する
        """
        # Arrange
        current_time = 0.0
        mock_time.monotonic.side_effect = lambda: current_time

        def mock_sleep(duration):
            nonlocal current_time
            # タイムアウトを超える時刻まで進める
            current_time += 0.2

        mock_time.sleep = mock_sleep

        tb = TokenBucket(capacity=1, fill_rate=2)
        tb.non_blocking_try_acquire()  # 初期トークンを消費

        # Act & Assert
        with self.assertRaises(TimeoutError):
            tb.acquire(timeout=0.1)


if __name__ == "__main__":
    unittest.main()
