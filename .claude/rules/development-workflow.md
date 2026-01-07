---
description: 開発ワークフローとコード品質基準。コミット前チェック、テスト規約。
globs: ["*"]
---

# Development Workflow

## Command Reference

**`make help` で全コマンド一覧表示**

### セットアップ

```bash
make setup         # 初回セットアップ（依存関係 + pre-commit）
make sync          # 依存関係の同期
make sync-drive    # Google Drive機能付きで同期
```

### アプリケーション実行

```bash
make ui            # Streamlit UI起動
make api           # FastAPI サーバー起動（開発モード）
```

### CLI（画像スクレイピング）

```bash
# URLから画像取得
make scrape URL=https://example.com
make scrape URL=https://example.com LIMIT=10 OUT=downloads

# トピック探索
make topic KEYWORD="富士山"
make topic KEYWORD="富士山" LIMIT=100

# トピック探索 + ダウンロード
make topic-download KEYWORD="富士山" OUT=images
```

### 品質チェック

```bash
make check         # フォーマット + リント + テスト（コミット前推奨）
make format        # Ruff フォーマット
make lint          # Ruff リントチェック
make test          # ユニットテスト
make test-v        # ユニットテスト（詳細出力）
make clean         # キャッシュ・一時ファイル削除
```

### uv 直接実行（必要な場合のみ）

```bash
uv run image-scrape --help                    # CLIヘルプ
uv run image-scrape --url URL                 # URL指定
uv run image-scrape --topic "検索ワード"       # トピック探索
```

## Pre-commit Hooks

- 【MUST】`uv run pre-commit install`でフック有効化
- 【MUST】コミット前にruff check/formatが自動実行

## Git Workflow

```bash
# ブランチ作成
git checkout -b feature/xxx

# コミット（Conventional Commits推奨）
git commit -m "feat: 新機能の説明"
git commit -m "fix: バグ修正の説明"
git commit -m "refactor: リファクタリング内容"
```

## Testing Rules

- 【MUST】テストファースト: 実装前に`tests/unit/`にテスト追加
- 【MUST】モック使用: 実ネットワーク接続を避ける
- 【MUST】AAA構造: Arrange-Act-Assert

```python
def test_振る舞いを日本語で記述(self):
    # Arrange
    sut = TargetClass()

    # Act
    result = sut.method()

    # Assert
    assert result == expected
```

## Secrets

- 【MUST】サービスアカウントJSON等は絶対にコミットしない
- 【MUST】環境変数で参照（`.env`は`.gitignore`に追加）
