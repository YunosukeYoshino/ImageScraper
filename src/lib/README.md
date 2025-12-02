# src/lib - Core Library Modules

本ディレクトリには、image-saverのコアロジックが含まれています。

## モジュール一覧

| モジュール | 役割 |
|-----------|------|
| `image_scraper.py` | ネットワーク取得、HTML解析（BeautifulSoup）、画像ダウンロード、Drive連携。UI向けヘルパー（`list_images`、`download_images`、`download_images_parallel`）も提供 |
| `topic_discovery.py` | トピック（検索ワード）から候補ページを自律的に探索し、プロベナンス記録を生成 |
| `search_provider.py` | 検索プロバイダ（DuckDuckGo等）のラッパー。レート制限と再試行を実装 |
| `rate_limit.py` | トークンバケット方式のレート制限（burst制御付き） |
| `models_discovery.py` | プロベナンスエントリ、クエリログ、プレビュー結果のデータモデル |
| `ui_helpers.py` | UI向けユーティリティ（JSON検証、URL構築、設定保存/読込） |

## 設計原則

- **Library-First**: 各モジュールは独立してテスト可能
- **外部境界の安全性**: ネットワーク/API境界にエラーハンドリング（タイムアウト、リトライ、ログ）
- **robots.txt尊重**: ページおよび画像URLの両方で厳密に尊重

## Topic Discovery & Provenance

トピックベースの探索では、以下のルールを厳守：

- **専用モジュール**: `topic_discovery.py`に実装
- **再現可能なクエリログ**: `discovery_logs/` に保存（トピック、検索クエリ、タイムスタンプ）
- **レート制限**: 検索プロバイダごとに`rate_limit.py`でバースト制御
- **robots.txt尊重**: 発見したすべてのページでスクレイピング前にチェック
- **プロベナンス記録**: 各画像に`source_page_url`、`image_url`、`discovery_method`、タイムスタンプを付与
- **テスト必須**: モック使用（CI中の実ネットワークアクセスなし）

## Google Drive Integration

- 追加依存グループ: `[drive]`（`google-api-python-client`、`google-auth`）
- サービスアカウントJSON（`GDRIVE_SA_JSON`環境変数または`--drive-sa-json`フラグ）が必要
- 対象フォルダに対するサービスアカウントの共有権限が必須

## Image Detection & Naming

- **画像検出**: 代表的な拡張子の正規表現（`.jpg|.jpeg|.png|.gif|.webp|.svg`）+ パス末尾チェックのフォールバック
- **ファイル命名**: URLのSHA-256ハッシュ + 推定拡張子（衝突回避）
