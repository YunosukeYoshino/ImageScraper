# TDD Patterns - よくあるテストパターン集

## Fixture Patterns（準備パターン）

### Setup/Teardown

```python
import pytest

class TestDatabase:
    @pytest.fixture(autouse=True)
    def setup(self):
        """各テスト前に実行"""
        self.db = create_test_database()
        yield
        """各テスト後に実行（クリーンアップ）"""
        self.db.cleanup()

    def test_insert(self):
        self.db.insert({"id": 1})
        assert self.db.count() == 1
```

### Shared Fixture

```python
@pytest.fixture
def sample_user():
    """テスト用ユーザーを作成"""
    return User(
        email="test@example.com",
        name="Test User",
        age=25
    )

def test_ユーザー名が取得できる(sample_user):
    assert sample_user.name == "Test User"

def test_成人判定(sample_user):
    assert sample_user.is_adult() == True
```

### Factory Fixture

```python
@pytest.fixture
def create_user():
    """ユーザー作成ファクトリ"""
    def _create(name="Test", age=20, **kwargs):
        return User(name=name, age=age, **kwargs)
    return _create

def test_未成年(create_user):
    user = create_user(age=17)
    assert user.is_adult() == False

def test_成人(create_user):
    user = create_user(age=20)
    assert user.is_adult() == True
```

---

## Assertion Patterns（検証パターン）

### 複数条件の検証

```python
# Bad: 1つ失敗すると後続が見えない
def test_user_creation():
    user = create_user()
    assert user.id is not None
    assert user.created_at is not None
    assert user.status == "active"

# Good: pytest-check で全て検証
from pytest_check import check

def test_user_creation():
    user = create_user()
    with check:
        assert user.id is not None
    with check:
        assert user.created_at is not None
    with check:
        assert user.status == "active"
```

### カスタムマッチャー

```python
def assert_valid_email(email: str):
    """メールアドレスの形式を検証"""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    assert re.match(pattern, email), f"無効なメール形式: {email}"

def test_ユーザー登録でメールが設定される():
    user = register_user("test@example.com")
    assert_valid_email(user.email)
```

### 近似値の検証

```python
import pytest

def test_浮動小数点の計算():
    result = calculate_pi()
    assert result == pytest.approx(3.14159, rel=1e-5)

def test_リストの近似値():
    result = normalize_vector([3, 4])
    assert result == pytest.approx([0.6, 0.8])
```

---

## Exception Patterns（例外パターン）

### 例外の型を検証

```python
def test_ゼロ除算で例外():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
```

### 例外メッセージを検証

```python
def test_無効な年齢でValueError():
    with pytest.raises(ValueError) as exc_info:
        validate_age(-1)
    assert "年齢は0以上" in str(exc_info.value)
```

### 例外が発生しないことを検証

```python
def test_有効な入力で例外なし():
    # 例外が発生しなければパス
    result = process_data(valid_input)
    assert result is not None
```

---

## Mock Patterns（モックパターン）

### 戻り値のモック

```python
from unittest.mock import Mock

def test_API成功時():
    mock_client = Mock()
    mock_client.fetch.return_value = {"status": "ok"}

    service = MyService(client=mock_client)
    result = service.process()

    assert result == "success"
```

### 例外のモック

```python
def test_API失敗時():
    mock_client = Mock()
    mock_client.fetch.side_effect = ConnectionError("timeout")

    service = MyService(client=mock_client)
    result = service.process()

    assert result == "error"
```

### 呼び出しの検証

```python
def test_正しい引数でAPI呼び出し():
    mock_client = Mock()
    service = MyService(client=mock_client)

    service.fetch_user(user_id=123)

    mock_client.fetch.assert_called_once_with(
        endpoint="/users/123",
        method="GET"
    )
```

### パッチデコレータ

```python
from unittest.mock import patch

@patch('mymodule.external_api')
def test_外部API呼び出し(mock_api):
    mock_api.return_value = {"data": "test"}

    result = my_function()

    assert result == "processed: test"
```

---

## Parameterized Tests（パラメータ化テスト）

### 複数入力パターン

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (0, "zero"),
    (1, "one"),
    (2, "two"),
    (-1, "negative"),
])
def test_number_to_word(input, expected):
    assert number_to_word(input) == expected
```

### 境界値テスト

```python
@pytest.mark.parametrize("age,is_adult", [
    (17, False),   # 境界値-1
    (18, True),    # 境界値
    (19, True),    # 境界値+1
    (0, False),    # 最小値
    (120, True),   # 最大値
])
def test_成人判定(age, is_adult):
    assert check_adult(age) == is_adult
```

### ID付きパラメータ

```python
@pytest.mark.parametrize("email,valid", [
    pytest.param("test@example.com", True, id="正常なメール"),
    pytest.param("invalid", False, id="@なし"),
    pytest.param("@example.com", False, id="ローカル部なし"),
    pytest.param("test@", False, id="ドメインなし"),
])
def test_メール検証(email, valid):
    assert validate_email(email) == valid
```

---

## Async Test Patterns（非同期テスト）

### pytest-asyncio

```python
import pytest

@pytest.mark.asyncio
async def test_非同期データ取得():
    result = await fetch_data_async()
    assert result is not None

@pytest.mark.asyncio
async def test_非同期例外():
    with pytest.raises(TimeoutError):
        await fetch_with_timeout(timeout=0.001)
```

---

## Test Organization（テスト構成）

### クラスによるグループ化

```python
class TestUserRegistration:
    """ユーザー登録の振る舞いテスト"""

    class Test正常系:
        def test_有効なデータで登録成功(self):
            ...

        def test_登録後に確認メール送信(self):
            ...

    class Test異常系:
        def test_重複メールで失敗(self):
            ...

        def test_無効なメール形式で失敗(self):
            ...

    class Test境界値:
        def test_名前が最大長(self):
            ...

        def test_名前が最大長プラス1で失敗(self):
            ...
```

### マーカーによる分類

```python
import pytest

@pytest.mark.slow
def test_大量データ処理():
    """実行に時間がかかるテスト"""
    ...

@pytest.mark.integration
def test_DB接続():
    """統合テスト"""
    ...

# 実行時: pytest -m "not slow"
```

---

## チェックリスト

テスト作成時の確認項目:

- [ ] テスト名が振る舞いを説明している
- [ ] AAA構造が明確
- [ ] 1テスト1アサーション（原則）
- [ ] 境界値をカバー
- [ ] 異常系をカバー
- [ ] 外部依存は適切にモック
- [ ] テスト間の依存がない
- [ ] 実行が高速（100ms以内が理想）
