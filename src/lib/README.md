# src/lib - Core Library Modules

本ディレクトリには、image-saverのコアロジックが含まれています。

## アーキテクチャ

Clean Architectureに基づく3層構造を採用しています。

```
src/lib/
├── domain/                 # ドメイン層（ビジネスロジック）
│   ├── entities/           # エンティティ・値オブジェクト
│   ├── services/           # ドメインサービス
│   └── repositories/       # リポジトリインターフェース
├── infrastructure/         # インフラ層（外部依存）
│   ├── http/               # HTTP通信・robots.txt
│   ├── parsers/            # HTML解析
│   ├── storage/            # ファイルストレージ
│   └── search/             # 検索プロバイダ実装
├── application/            # アプリケーション層
│   ├── services/           # 横断的サービス（レート制限等）
│   └── use_cases/          # ユースケース（将来用）
└── [レガシーモジュール]     # 後方互換のため維持
```

### 依存方向

```
domain ← application ← infrastructure
   ↑          ↑             ↑
   └──────────┴─────────────┘
        presentation (ui/api/cli)
```

## レイヤー詳細

### Domain Layer（ドメイン層）

外部依存なし。純粋なビジネスロジック。

| モジュール | 役割 |
|-----------|------|
| `entities/provenance.py` | `ProvenanceEntry`, `QueryLogEntry`, `DownloadFilter`, `PreviewResult` |
| `services/relevance_scorer.py` | 画像の関連性スコア計算（alt/ファイル名/コンテキスト/ドメイン） |
| `repositories/search_repository.py` | 検索プロバイダの抽象インターフェース |

### Infrastructure Layer（インフラ層）

外部システムとの接続を担当。

| モジュール | 役割 |
|-----------|------|
| `http/http_client.py` | HTTP取得、リトライ、デフォルトヘッダー |
| `http/robots_checker.py` | robots.txtチェック |
| `parsers/html_parser.py` | BeautifulSoupによるHTML解析、画像抽出 |
| `storage/local_storage.py` | ローカルファイル保存、ハッシュ命名 |
| `search/duckduckgo_search.py` | DuckDuckGo検索の実装（SearchRepository） |

### Application Layer（アプリケーション層）

ユースケース調整と横断的関心事。

| モジュール | 役割 |
|-----------|------|
| `services/rate_limiter.py` | トークンバケット方式のレート制限 |
| `use_cases/` | 将来のユースケース実装用（現在は空） |

## レガシーモジュール（後方互換）

以下のモジュールは新しい場所から再エクスポートしており、既存コードとの互換性を維持しています。

| レガシー | 新しい場所 |
|----------|-----------|
| `models_discovery.py` | `domain/entities/provenance.py` |
| `relevance_scorer.py` | `domain/services/relevance_scorer.py` |
| `rate_limit.py` | `application/services/rate_limiter.py` |

**新規コードは新しい場所から直接インポートしてください。**

## 設計原則

- **Library-First**: 各モジュールは独立してテスト可能
- **依存性逆転**: domain層は外部に依存しない
- **外部境界の安全性**: ネットワーク/API境界にエラーハンドリング（タイムアウト、リトライ、ログ）
- **robots.txt尊重**: ページおよび画像URLの両方で厳密に尊重

## 関連性スコアリング

トピック検索で取得した画像の関連性を0.0〜1.0でスコアリング。

| 評価要素 | 重み | 説明 |
|----------|------|------|
| alt属性 | 0.4 | 画像の説明テキスト（最重要） |
| ファイル名 | 0.3 | URL末尾のファイル名 |
| 周囲テキスト | 0.2 | 親要素のテキスト（最大200文字） |
| ドメイン信頼度 | 0.1 | wikimedia, pixabay等は加点 |

**スコア分類:**
- 高（0.6以上）🟢
- 中（0.3-0.6）🟡
- 低（0.3未満）🔴

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
