# Keepa Analyzer - Amazon Product Intelligence Tool

Keepaの全機能を活用した、Amazon商品情報の分析・比較ツール。

## 機能一覧

### 📊 コア機能（実装済み）

1. **利益計算・FBA手数料シミュレーター**
   - 販売価格 + 仕入原価から自動利益計算
   - FBA手数料（カテゴリー別）を自動反映
   - 配送料、紹介料も含めた正確な利益率計算

2. **価格推移・トレンド分析**
   - Keepa APIで30日・90日・1年の価格データ取得
   - グラフ表示で価格トレンドを可視化
   - 最安値追跡機能

3. **ライバル商品との比較**
   - Excel（仕入データ）と Amazon出品商品を比較
   - 複数商品の一括分析
   - BSR・評価・レビュー数の自動取得

## プロジェクト構成

```
keepa-analyzer/
├── backend/                    # FastAPI バックエンド
│   ├── main.py                 # FastAPI メインアプリ
│   ├── config.py               # 設定ファイル
│   ├── database.py             # DB接続
│   ├── models.py               # SQLAlchemy ORM
│   ├── schemas.py              # Pydantic スキーマ
│   ├── keepa_service.py        # Keepa API連携
│   ├── fba_calculator.py       # FBA手数料計算
│   ├── excel_handler.py        # Excel処理
│   ├── requirements.txt        # Python依存関係
│   └── Dockerfile
│
├── frontend/                   # React フロントエンド
│   ├── src/
│   │   └── App.jsx             # メインコンポーネント
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml          # Docker構成
├── 01_schema.sql               # DB スキーマ
└── README.md                   # このファイル
```

## 必要な環境

- Docker & Docker Compose
- または以下をローカルインストール：
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 15+

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/keepa-analyzer.git
cd keepa-analyzer
```

### 2. 環境変数を設定

```bash
cp .env.example .env
```

`.env` ファイルを編集して、Keepa API キーを設定：

```env
KEEPA_API_KEY=7j94dv0omf10s7q1qimr0poe29pv941qs7432pu6ibco03gjsh9r39117pta992q
DATABASE_URL=postgresql://keepa_user:keepa_password@postgres:5432/keepa_analyzer
```

### 3. Docker で起動

```bash
docker-compose up -d
```

### 4. データベースを初期化

```bash
# PostgreSQL に接続してスキーマを実行
psql -h localhost -U keepa_user -d keepa_analyzer < 01_schema.sql
```

または FastAPI が自動初期化します（models.py で）

### 5. アプリにアクセス

- **フロントエンド**: http://localhost:3000
- **バックエンド API**: http://localhost:8000
- **Swagger API ドキュメント**: http://localhost:8000/docs

## ローカル開発（Docker なし）

### バックエンド

```bash
cd backend

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# FastAPI サーバー起動
uvicorn main:app --reload
```

### フロントエンド

```bash
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm start
```

## API エンドポイント

### 商品管理

- `POST /api/products` - 商品を追加
- `GET /api/products` - 商品一覧取得
- `GET /api/products/{id}` - 商品詳細取得
- `GET /api/products/asin/{asin}` - ASIN で検索

### 価格データ

- `GET /api/prices/{asin}?period=30d` - 価格履歴取得（30d/90d/1y）

### FBA 計算

- `GET /api/fba-categories` - FBA 手数料一覧
- `POST /api/calculate-profit` - 利益計算

### ファイルインポート

- `POST /api/import` - Excel ファイルアップロード
- `GET /api/import/template` - テンプレートダウンロード

## Excel インポート形式

必須列:
| 列名 | 形式 | 例 |
|------|------|-----|
| ASIN | 10文字 | B123456789 |
| JAN | 13文字 | 4589123456789 |
| 納品価格 | 数値 | 1500 |

オプション列:
| 列名 | 形式 |
|------|------|
| 商品URL | URL |

## FBA 手数料設定

カテゴリー別の手数料を FBA_categories テーブルで管理：

```sql
INSERT INTO fba_categories (category_name, fba_fee_rate, shipping_cost)
VALUES ('Electronics', 8, 0.75);
```

## 利益計算の流れ

```
販売価格
  ↓
- 仕入原価
- 紹介料（カテゴリー別、15%が標準）
- FBA手数料（重量・サイズ依存）
- 配送単価
- 変動手数料
  ↓
= 実質利益
```

## 開発ロードマップ

- [x] データベース設計
- [x] FastAPI バックエンド基盤
- [x] Keepa API 連携
- [x] FBA 手数料計算
- [x] Excel インポート機能
- [x] React フロントエンド UI
- [ ] グラフ表示（Chart.js 統合）
- [ ] 高度な分析機能（在庫回転率など）
- [ ] 自動監視・アラート機能
- [ ] マルチユーザー対応
- [ ] クラウドデプロイ

## デプロイ（本番環境）

### Railway への デプロイ

```bash
# Railway CLI インストール
npm i -g @railway/cli

# ログイン
railway login

# デプロイ
railway up
```

### Heroku への デプロイ

```bash
heroku create keepa-analyzer
git push heroku main
```

## トラブルシューティング

### Keepa API エラー

- API キーを確認
- トークンレート制限を確認（月5トークン）
- `python -c "import requests; print(requests.get('https://api.keepa.com/product?key=YOUR_KEY&asin=B001').json())"`

### データベース接続エラー

```bash
# PostgreSQL が起動しているか確認
docker ps | grep postgres

# ログ確認
docker logs keepa_postgres
```

### フロントエンド ビルドエラー

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

## セキュリティ

- `.env` ファイルは `.gitignore` に追加
- Keepa API キーは環境変数で管理
- 本番環境では `DEBUG=False` に設定
- HTTPS を使用

## ライセンス

MIT License

## サポート

問題が発生した場合は GitHub Issues で報告してください。

---

**Keepa Analyzer** - Amazon 商品情報分析ツール v1.0.0
