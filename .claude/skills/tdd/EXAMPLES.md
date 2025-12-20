# TDD Examples - 具体的なテストパターン例

## Example 1: 計算ロジックのTDD

### 要件
税込価格を計算する関数を実装する。

### Step 1: テストリスト作成

```markdown
□ 100円の商品は110円（税率10%）
□ 0円は0円
□ 小数点以下は切り捨て
□ 負の価格は例外
```

### Step 2: 最初のテスト（RED）

```python
# tests/unit/test_tax_calculator.py
def test_100円の商品は110円():
    # Arrange
    price = 100
    tax_rate = 0.10

    # Act
    result = calculate_tax_included_price(price, tax_rate)

    # Assert
    assert result == 110
```

テスト実行 → 失敗（関数が存在しない）

### Step 3: 最小実装（GREEN）

```python
# src/tax_calculator.py
def calculate_tax_included_price(price: int, tax_rate: float) -> int:
    return 110  # 仮実装
```

テスト実行 → 成功

### Step 4: 次のテストを追加

```python
def test_0円は0円():
    result = calculate_tax_included_price(0, 0.10)
    assert result == 0
```

テスト実行 → 失敗（110を返してしまう）

### Step 5: 一般化（GREEN）

```python
def calculate_tax_included_price(price: int, tax_rate: float) -> int:
    return int(price * (1 + tax_rate))
```

### Step 6: 境界値テスト追加

```python
def test_小数点以下は切り捨て():
    # 99 * 1.10 = 108.9 → 108
    result = calculate_tax_included_price(99, 0.10)
    assert result == 108

def test_負の価格で例外():
    with pytest.raises(ValueError) as exc_info:
        calculate_tax_included_price(-100, 0.10)
    assert "価格は0以上" in str(exc_info.value)
```

### 最終実装

```python
def calculate_tax_included_price(price: int, tax_rate: float) -> int:
    """税込価格を計算する（小数点以下切り捨て）"""
    if price < 0:
        raise ValueError("価格は0以上である必要があります")
    return int(price * (1 + tax_rate))
```

---

## Example 2: クラスのTDD

### 要件
カウンターを実装する。

### テストリスト

```markdown
□ 初期値は0
□ incrementで1増える
□ decrementで1減る
□ 0未満にはならない（decrementで例外）
□ resetで0に戻る
```

### テストコード

```python
class TestCounter:
    """Counterの振る舞いテスト"""

    def test_初期値は0(self):
        counter = Counter()
        assert counter.value == 0

    def test_incrementで1増える(self):
        # Arrange
        counter = Counter()

        # Act
        counter.increment()

        # Assert
        assert counter.value == 1

    def test_複数回incrementで正しく増える(self):
        counter = Counter()
        counter.increment()
        counter.increment()
        counter.increment()
        assert counter.value == 3

    def test_decrementで1減る(self):
        counter = Counter()
        counter.increment()
        counter.increment()

        counter.decrement()

        assert counter.value == 1

    def test_0からdecrementで例外(self):
        counter = Counter()
        with pytest.raises(ValueError) as exc_info:
            counter.decrement()
        assert "0未満にはできません" in str(exc_info.value)

    def test_resetで0に戻る(self):
        counter = Counter()
        counter.increment()
        counter.increment()

        counter.reset()

        assert counter.value == 0
```

### 実装

```python
class Counter:
    """シンプルなカウンター"""

    def __init__(self):
        self._value = 0

    @property
    def value(self) -> int:
        return self._value

    def increment(self) -> None:
        self._value += 1

    def decrement(self) -> None:
        if self._value <= 0:
            raise ValueError("0未満にはできません")
        self._value -= 1

    def reset(self) -> None:
        self._value = 0
```

---

## Example 3: 外部依存のあるコードのTDD

### 要件
天気APIから気温を取得し、服装を提案する。

### テストリスト

```markdown
□ 25度以上は「Tシャツ」
□ 15度以上25度未満は「長袖」
□ 15度未満は「コート」
□ API失敗時は「取得できませんでした」
```

### テストコード（モック使用）

```python
from unittest.mock import Mock, patch

class TestClothingAdvisor:
    """ClothingAdvisorの振る舞いテスト"""

    def test_25度以上はTシャツ(self):
        # Arrange
        mock_api = Mock()
        mock_api.get_temperature.return_value = 28
        advisor = ClothingAdvisor(weather_api=mock_api)

        # Act
        result = advisor.suggest()

        # Assert
        assert result == "Tシャツ"

    def test_15度以上25度未満は長袖(self):
        mock_api = Mock()
        mock_api.get_temperature.return_value = 20
        advisor = ClothingAdvisor(weather_api=mock_api)

        result = advisor.suggest()

        assert result == "長袖"

    def test_15度未満はコート(self):
        mock_api = Mock()
        mock_api.get_temperature.return_value = 10
        advisor = ClothingAdvisor(weather_api=mock_api)

        result = advisor.suggest()

        assert result == "コート"

    def test_API失敗時のメッセージ(self):
        mock_api = Mock()
        mock_api.get_temperature.side_effect = ConnectionError("API error")
        advisor = ClothingAdvisor(weather_api=mock_api)

        result = advisor.suggest()

        assert result == "取得できませんでした"

    # 境界値テスト
    def test_ちょうど25度はTシャツ(self):
        mock_api = Mock()
        mock_api.get_temperature.return_value = 25
        advisor = ClothingAdvisor(weather_api=mock_api)

        assert advisor.suggest() == "Tシャツ"

    def test_ちょうど15度は長袖(self):
        mock_api = Mock()
        mock_api.get_temperature.return_value = 15
        advisor = ClothingAdvisor(weather_api=mock_api)

        assert advisor.suggest() == "長袖"
```

### 実装

```python
class ClothingAdvisor:
    """天気に基づいた服装アドバイザー"""

    def __init__(self, weather_api):
        self._api = weather_api

    def suggest(self) -> str:
        try:
            temp = self._api.get_temperature()
        except Exception:
            return "取得できませんでした"

        if temp >= 25:
            return "Tシャツ"
        elif temp >= 15:
            return "長袖"
        else:
            return "コート"
```

---

## ポイントまとめ

1. **最小のテストから始める** - 最も単純なケースを最初に
2. **仮実装でもOK** - まずはハードコードでグリーンに
3. **三角測量** - 複数のテストで実装を一般化
4. **境界値を忘れない** - ちょうど25度、ちょうど15度など
5. **外部依存はモック** - APIやDBはテストダブルを使用
