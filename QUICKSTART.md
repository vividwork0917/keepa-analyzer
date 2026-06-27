# 🚀 Keepa Analyzer - クイックスタートガイド

5分で Keepa Analyzer を起動する手順。

## ✅ 前提条件

- Docker & Docker Compose がインストール済み
- Keepa Pro アカウント + API キー
- ポート 3000, 5432, 8000 が使用可能

## 📋 ステップバイステップ

### 1️⃣ ファイル構成

以下のファイルを同じディレクトリに配置：

```
keepa-analyzer/
├── main.py
├── config.py
├── database.py
├── models.py
├── schemas.py
├── keepa_service.py
├── fba_calculator.py
├── excel_handler.py
├── requirements.txt
├── App.jsx
├── package.json
├── docker-compose.yml
├── .env.example
├── 01_schema.sql
├── Dockerfile.backend
└── Dockerfile.frontend
```

### 2️⃣ 環境設定

```bash
# .env ファイルを作成
cat > .env << EOF
KEEPA_API_KEY=7j94dv0omf10s7q1qimr0poe29pv941qs7432pu6ibco03gjsh9r39117pta992q
DATABASE_URL=postgresql://keepa_user:keepa_password@postgres:5432/keepa_analyzer
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
EOF
```

### 3️⃣ Docker コンテナを起動

```bash
# バックエンド用の Dockerfile を配置
cp Dockerfile.backend backend/Dockerfile
cp Dockerfile.frontend frontend/Dockerfile

# コンテナ起動
docker-compose up -d

# ステータス確認
docker-compose ps
```

### 4️⃣ データベース初期化

```bash
# PostgreSQL コンテナに接続してスキーマを実行
docker exec -i keepa_postgres psql -U keepa_user -d keepa_analyzer < 01_schema.sql

# 確認
docker exec keepa_postgres psql -U keepa_user -d keepa_analyzer -c "\dt"
```

### 5️⃣ アプリにアクセス

ブラウザを開いて以下にアクセス：

| サービス | URL | 用途 |
|---------|-----|------|
| **フロントエンド** | http://localhost:3000 | アプリメイン画面 |
| **API ドキュメント** | http://localhost:8000/docs | API 仕様確認 |
| **ヘルスチェック** | http://localhost:8000/health | バックエンド状態確認 |

## 🎯 使用方法

### 1. 商品をインポート

1. **ダッシュボード** → **インポート** タブを開く
2. Excel ファイルをアップロード

**Excel 形式（必須）:**
```
| ASIN       | JAN          | 納品価格 | 商品URL                    |
|------------|--------------|---------|--------------------------|
| B123456789 | 4589123456789| 1500    | https://amazon.co.jp/... |
| B123456790 | 4589123456790| 2500    | https://amazon.co.jp/... |
```

### 2. Keepa データを同期

```bash
# APIで全商品を同期
curl -X POST http://localhost:8000/api/products/sync-all
```

レスポンス例：
```json
{
  "total": 100,
  "success": 98,
  "failed": 2,
  "details": {...}
}
```

### 3. 利益を計算

**方法 A: UI から計算**
- **計算** タブ → 販売価格を入力 → 計算実行

**方法 B: API から計算**
```bash
curl -X POST \
  http://localhost:8000/api/products/1/calculate-profit \
  -H "Content-Type: application/json" \
  -d '{"selling_price": 2500}'
```

### 4. 価格推移をチェック

- **商品管理** → 商品を選択 → グラフを表示
- 30日/90日/1年の期間を切り替え

## 📊 API 使用例

### 商品追加

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "jan": "4589123456789",
    "asin": "B123456789",
    "product_name": "サンプル商品",
    "cost_price": 1500,
    "category": "Electronics"
  }'
```

### 商品一覧取得

```bash
curl http://localhost:8000/api/products?limit=10
```

### 価格履歴取得（30日分）

```bash
curl http://localhost:8000/api/prices/B123456789?period=30d
```

### 逆算計算

**目標利益率 20% で必要な販売価格**

```bash
curl "http://localhost:8000/api/products/1/target-price?target_margin=20"
```

レスポンス例：
```json
{
  "product_id": 1,
  "cost_price": 1500,
  "target_margin_percent": 20,
  "required_selling_price": 2381.01
}
```

## 🔍 トラブルシューティング

### ❌ コンテナが起動しない

```bash
# ログを確認
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# 再起動
docker-compose restart
```

### ❌ Keepa API エラー

```bash
# API キーをテスト
curl "https://api.keepa.com/product?key=YOUR_KEY&asin=B001" 

# 結果が空の場合は API キーが無効
```

### ❌ ポートが使用中

```bash
# ポート 3000, 5432, 8000 を使用しているプロセスを確認
lsof -i :3000
lsof -i :5432
lsof -i :8000

# 別のポートで起動
# docker-compose.yml で ports を変更
```

## 📝 FBA 手数料の設定

カテゴリー別の手数料をカスタマイズ：

```bash
docker exec -i keepa_postgres psql -U keepa_user -d keepa_analyzer << EOF
UPDATE fba_categories 
SET fba_fee_rate = 12, shipping_cost = 0.80
WHERE category_name = 'Electronics';
EOF
```

## 🔌 API チェーン

複数の API を組み合わせた流れ：

```bash
# 1. 商品を追加
PRODUCT_ID=$(curl -s -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"jan":"4589123456789","asin":"B123456789",...}' | jq .id)

# 2. Keepa から同期
curl -X POST http://localhost:8000/api/products/$PRODUCT_ID/sync-keepa

# 3. 価格を取得
curl http://localhost:8000/api/prices/B123456789

# 4. 利益を計算
curl -X POST http://localhost:8000/api/products/$PRODUCT_ID/calculate-profit \
  -d '{"selling_price": 2500}'
```

## 📦 コンテナ管理

```bash
# ログ確認（リアルタイム）
docker-compose logs -f backend

# コンテナ停止
docker-compose down

# ボリュームも削除（DB初期化）
docker-compose down -v

# 再構築してから起動
docker-compose up --build
```

## 🚀 本番環境へのデプロイ

### Railway へのデプロイ

```bash
# Railway CLI をインストール
npm i -g @railway/cli

# ログイン
railway login

# プロジェクト作成
railway init

# デプロイ
railway up
```

### 環境変数を設定

```bash
railway variables set KEEPA_API_KEY=your_key
railway variables set DATABASE_URL=your_db_url
railway variables set DEBUG=False
```

## ✨ 次のステップ

- [ ] Excel テンプレートをダウンロード
- [ ] 最初の商品をインポート
- [ ] Keepa データを同期
- [ ] 利益計算機を試す
- [ ] 価格推移グラフを確認

---

**Need Help?** API ドキュメント: http://localhost:8000/docs
