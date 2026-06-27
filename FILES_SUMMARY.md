# 📦 Keepa Analyzer - ファイル一覧

実装完了したすべてのファイルと、その役割。

## 🎯 構成図

```
Keepa Analyzer
│
├── 📂 バックエンド（FastAPI + Python）
│   ├── main.py                 [FastAPI メインアプリ]
│   ├── config.py               [設定管理（API キー、DB URL等）]
│   ├── database.py             [SQLAlchemy DB接続・セッション]
│   ├── models.py               [ORM モデル定義]
│   ├── schemas.py              [Pydantic リクエスト/レスポンススキーマ]
│   ├── keepa_service.py        [Keepa API連携サービス]
│   ├── fba_calculator.py       [FBA手数料・利益計算エンジン]
│   ├── excel_handler.py        [Excel/CSV インポート処理]
│   ├── routers_products.py     [商品管理 API ルーター]
│   ├── requirements.txt        [Python 依存関係]
│   └── Dockerfile.backend      [Docker イメージ定義]
│
├── 📂 フロントエンド（React）
│   ├── App.jsx                 [メインコンポーネント（ダッシュボード全体）]
│   ├── package.json            [Node.js 依存関係]
│   └── Dockerfile.frontend     [Docker イメージ定義]
│
├── 📂 インフラ・設定
│   ├── docker-compose.yml      [Docker コンテナ構成]
│   ├── .env.example            [環境変数テンプレート]
│   └── 01_schema.sql           [PostgreSQL スキーマ定義]
│
└── 📂 ドキュメント
    ├── README.md               [プロジェクト概要・セットアップ]
    ├── QUICKSTART.md           [5分クイックスタート]
    └── FILES_SUMMARY.md        [このファイル]
```

## 📋 ファイル詳細

### バックエンド

| ファイル | 説明 | 主要機能 |
|---------|------|---------|
| **main.py** | FastAPI アプリケーション本体 | ルーティング、CORS設定、スタートアップ処理 |
| **config.py** | 環境設定・定数管理 | API キー、DB URL、タイムアウト設定 |
| **database.py** | DB接続管理 | SQLAlchemy エンジン、セッションファクトリ |
| **models.py** | SQLAlchemy ORM モデル | Product, PriceHistory, FBACategory等7テーブル |
| **schemas.py** | Pydantic バリデーションスキーマ | リクエスト/レスポンス定義 |
| **keepa_service.py** | Keepa API 連携 | 商品データ取得、価格履歴抽出、バルク処理 |
| **fba_calculator.py** | FBA手数料・利益計算 | 紹介料、FBA手数料、利益率計算、逆算 |
| **excel_handler.py** | Excel/CSV インポート | ファイル読込、バリデーション、DB保存 |
| **routers_products.py** | API ルーター | 商品CRUD、同期、利益計算エンドポイント |
| **requirements.txt** | Python パッケージ一覧 | FastAPI, SQLAlchemy, pandas等 |
| **Dockerfile.backend** | バックエンド Docker イメージ | Python 3.11環境 |

### フロントエンド

| ファイル | 説明 | 主要機能 |
|---------|------|---------|
| **App.jsx** | React メインコンポーネント | ダッシュボード、商品管理、インポート、計算機 |
| **package.json** | Node.js 依存関係 | React, Axios, Chart.js |
| **Dockerfile.frontend** | フロントエンド Docker イメージ | Node 18 + React ビルド環境 |

### インフラ・設定

| ファイル | 説明 | 内容 |
|---------|------|------|
| **docker-compose.yml** | Docker Compose 構成 | PostgreSQL, FastAPI, React コンテナ定義 |
| **.env.example** | 環境変数テンプレート | API キー、DB URL サンプル |
| **01_schema.sql** | PostgreSQL スキーマ | テーブル定義、インデックス、サンプルデータ |

### ドキュメント

| ファイル | 説明 | 対象者 |
|---------|------|--------|
| **README.md** | 完全なセットアップガイド | 開発者・管理者 |
| **QUICKSTART.md** | 5分で起動するガイド | エンドユーザー |
| **FILES_SUMMARY.md** | ファイル構成説明 | 開発者 |

---

## 🔗 ファイル間の依存関係

```
App.jsx (React)
  ↓
  ├→ Axios API コール
  └→ http://localhost:8000/api/...

main.py (FastAPI)
  ├→ routers_products.py (API ルーター)
  │   ├→ models.py (DB操作)
  │   ├→ keepa_service.py (Keepa連携)
  │   └→ fba_calculator.py (計算)
  ├→ database.py (DB接続)
  └→ config.py (設定)

keepa_service.py
  ├→ models.py (DB保存)
  ├→ config.py (API キー取得)
  └→ requests ライブラリ（HTTP通信）

excel_handler.py
  ├→ pandas (Excel読込)
  ├→ models.py (DB保存)
  └→ config.py (ファイルサイズ設定）

docker-compose.yml
  ├→ Dockerfile.backend (イメージビルド)
  ├→ Dockerfile.frontend (イメージビルド)
  └→ 01_schema.sql (DB初期化)
```

## 📊 データベース テーブル一覧

| テーブル | 用途 | 主要カラム |
|---------|------|----------|
| **products** | 商品マスタ | id, jan, asin, product_name, cost_price, category |
| **price_history** | 価格履歴（Keepa連携） | id, product_id, date, amazon_price, bsr, rating |
| **fba_categories** | FBA手数料マスタ | id, category_name, fba_fee_rate, shipping_cost |
| **profit_calculations** | 利益計算結果 | id, product_id, date, profit, profit_margin |
| **import_records** | インポート履歴 | id, file_name, total_rows, success_count, status |
| **rival_comparison** | ライバル商品比較 | id, product_id, rival_asin, our_price, rival_price |

## 🚀 起動フロー

1. **docker-compose up** 実行
   ↓
2. PostgreSQL コンテナ起動 + `01_schema.sql` 実行
   ↓
3. FastAPI コンテナ起動
   - `main.py` → `database.py` で DB初期化
   - `config.py` から環境変数ロード
   - `routers_products.py` がエンドポイント登録
   ↓
4. React コンテナ起動 + `App.jsx` をビルド
   ↓
5. ブラウザで http://localhost:3000 にアクセス
   ↓
6. **App.jsx** が Axios で `http://localhost:8000/api/...` を呼び出し
   ↓
7. **routers_products.py** が リクエストを処理
   - `models.py` で DB操作
   - `keepa_service.py` で Keepa連携
   - `fba_calculator.py` で利益計算

## 💾 ファイルサイズ

| ファイル | サイズ | 行数 |
|---------|--------|------|
| main.py | ~8KB | ~200行 |
| models.py | ~7KB | ~160行 |
| keepa_service.py | ~10KB | ~280行 |
| fba_calculator.py | ~12KB | ~320行 |
| excel_handler.py | ~10KB | ~280行 |
| routers_products.py | ~12KB | ~290行 |
| App.jsx | ~15KB | ~400行 |
| docker-compose.yml | ~1.5KB | ~50行 |
| 01_schema.sql | ~3KB | ~100行 |
| **合計** | **~79KB** | **~2000行** |

## 🔐 セキュリティ設定

- ✅ `.env` で API キーを環境変数管理
- ✅ CORS ホワイトリスト設定
- ✅ データベースパスワード設定
- ✅ SQL インジェクション対策（ORM使用）
- ✅ 本番環境では DEBUG=False

## 📈 拡張ポイント

| 機能 | ファイル | 追加実装内容 |
|------|---------|-----------|
| メール通知 | main.py | メール送信ロジック追加 |
| WebSocket リアルタイム更新 | main.py | WebSocket ルーター追加 |
| 高度な分析 | fba_calculator.py | 在庫回転率、市場分析関数 |
| 多言語対応 | App.jsx | i18n ライブラリ統合 |
| 認証 | main.py, App.jsx | JWT 認証実装 |
| レポート生成 | excel_handler.py | PDF エクスポート機能 |

## 📞 サポート

- **API ドキュメント** → http://localhost:8000/docs（Swagger UI）
- **エラーログ** → `docker-compose logs backend`
- **DB接続確認** → `docker exec keepa_postgres psql -U keepa_user -d keepa_analyzer -c "SELECT * FROM products;"`

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-26  
**Status**: ✅ Ready for Deployment
