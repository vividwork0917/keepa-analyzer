-- Keepa Analyzer Database Schema
-- PostgreSQL

-- テーブル1: 商品マスタ
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    jan VARCHAR(13) UNIQUE NOT NULL COMMENT 'JAN コード',
    asin VARCHAR(10) UNIQUE NOT NULL COMMENT 'Amazon ASIN',
    product_name VARCHAR(500) NOT NULL,
    product_url VARCHAR(1000),
    cost_price DECIMAL(10, 2) NOT NULL COMMENT '仕入価格（納品価格）',
    category VARCHAR(100) NOT NULL COMMENT 'Amazonカテゴリー',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_asin ON products(asin);
CREATE INDEX idx_jan ON products(jan);

-- テーブル2: 価格履歴（Keepa から取得）
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    asin VARCHAR(10),
    date DATE NOT NULL,
    amazon_price DECIMAL(10, 2) COMMENT 'Amazon出品価格',
    lowest_price DECIMAL(10, 2) COMMENT 'カテゴリー内最安値',
    new_offer_count INTEGER COMMENT '新品出品数',
    used_offer_count INTEGER COMMENT '中古出品数',
    bsr INTEGER COMMENT 'Best Seller Rank',
    bsr_category VARCHAR(100),
    rating DECIMAL(3, 2) COMMENT '評価値',
    review_count INTEGER COMMENT 'レビュー数',
    keepa_request_ts TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_date ON price_history(product_id, date);
CREATE INDEX idx_asin_date ON price_history(asin, date);

-- テーブル3: FBA手数料マスタ（カテゴリー別）
CREATE TABLE IF NOT EXISTS fba_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL COMMENT 'Amazonカテゴリー名',
    fba_fee_rate DECIMAL(5, 2) NOT NULL COMMENT 'FBA手数料率（%）',
    shipping_cost DECIMAL(10, 2) NOT NULL COMMENT '配送単価（送料）',
    storage_cost_small DECIMAL(10, 2) COMMENT '小型商品の保管料',
    storage_cost_large DECIMAL(10, 2) COMMENT '大型商品の保管料',
    weight_kg DECIMAL(10, 3) COMMENT '標準重量',
    note VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- テーブル4: 利益計算結果キャッシュ
CREATE TABLE IF NOT EXISTS profit_calculations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    selling_price DECIMAL(10, 2) NOT NULL COMMENT 'Amazon 販売価格',
    cost_price DECIMAL(10, 2) NOT NULL,
    fba_fee DECIMAL(10, 2) NOT NULL COMMENT 'FBA 手数料',
    referral_fee DECIMAL(10, 2) NOT NULL COMMENT '紹介料（通常15%）',
    variable_closing_fee DECIMAL(10, 2) NOT NULL COMMENT '変動手数料',
    shipping_cost DECIMAL(10, 2),
    profit DECIMAL(10, 2) COMMENT '実質利益',
    profit_margin DECIMAL(5, 2) COMMENT '利益率（%）',
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_calc_product_date ON profit_calculations(product_id, date);

-- テーブル5: インポート履歴
CREATE TABLE IF NOT EXISTS import_records (
    id SERIAL PRIMARY KEY,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_name VARCHAR(255),
    total_rows INTEGER,
    success_count INTEGER,
    error_count INTEGER,
    status VARCHAR(50) COMMENT 'success, partial, failed',
    error_log TEXT,
    processed_by VARCHAR(100)
);

-- テーブル6: ライバル商品比較
CREATE TABLE IF NOT EXISTS rival_comparison (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    rival_asin VARCHAR(10) NOT NULL COMMENT 'ライバル商品 ASIN',
    rival_product_name VARCHAR(500),
    comparison_date DATE,
    our_price DECIMAL(10, 2),
    rival_price DECIMAL(10, 2),
    our_bsr INTEGER,
    rival_bsr INTEGER,
    our_rating DECIMAL(3, 2),
    rival_rating DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- サンプルデータ：FBA手数料マスタ
INSERT INTO fba_categories (category_name, fba_fee_rate, shipping_cost) VALUES
('Books', 15, 0.50),
('Electronics', 8, 0.75),
('Clothing', 15, 0.50),
('Home & Kitchen', 15, 0.75),
('Sports & Outdoors', 15, 1.00),
('Toys & Games', 15, 0.75),
('Beauty', 15, 0.50),
('Music', 15, 0.50)
ON CONFLICT (category_name) DO NOTHING;
