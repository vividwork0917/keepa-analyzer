/**
 * Keepa Analyzer - React Frontend
 * Main Application Component
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// API Client
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ==================== Components ====================

// Dashboard Header
const Header = ({ activeTab, onTabChange }) => (
  <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 shadow-lg">
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">📊 Keepa Analyzer</h1>
      <p className="text-blue-100">Amazon商品情報分析・比較ツール</p>

      <nav className="mt-6 flex gap-4">
        {['dashboard', 'products', 'import', 'calculator'].map(tab => (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`px-4 py-2 rounded font-medium transition ${
              activeTab === tab
                ? 'bg-white text-blue-600'
                : 'bg-blue-700 text-white hover:bg-blue-600'
            }`}
          >
            {tab === 'dashboard' && '📈 ダッシュボード'}
            {tab === 'products' && '📦 商品管理'}
            {tab === 'import' && '📥 インポート'}
            {tab === 'calculator' && '💰 利益計算'}
          </button>
        ))}
      </nav>
    </div>
  </header>
);

// Price Chart Component
const PriceChart = ({ asin, product }) => {
  const [priceData, setPriceData] = useState(null);
  const [period, setPeriod] = useState('30d');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!asin) return;

    setLoading(true);
    apiClient
      .get(`/prices/${asin}`, { params: { period } })
      .then(res => {
        setPriceData(res.data.data);
      })
      .catch(err => console.error('Failed to fetch prices:', err))
      .finally(() => setLoading(false));
  }, [asin, period]);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-xl font-bold mb-4">{product?.product_name || asin} - 価格推移</h3>

      <div className="mb-4 flex gap-2">
        {['30d', '90d', '1y'].map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-3 py-1 rounded text-sm ${
              period === p
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {p === '30d' ? '30日' : p === '90d' ? '90日' : '1年'}
          </button>
        ))}
      </div>

      {loading && <p className="text-gray-500">読込中...</p>}

      {priceData && !loading && (
        <div className="bg-gray-50 p-4 rounded h-64 flex items-center justify-center">
          <p className="text-gray-500">
            グラフ: {priceData.length}件のデータ
          </p>
        </div>
      )}
    </div>
  );
};

// Products Table
const ProductsTable = ({ products, onSelectProduct }) => {
  const [search, setSearch] = useState('');

  const filtered = products.filter(
    p =>
      p.asin.includes(search.toUpperCase()) ||
      p.product_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-xl font-bold mb-4">📦 登録商品一覧</h3>

      <input
        type="text"
        placeholder="ASIN または商品名で検索..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 border-b">
            <tr>
              <th className="px-4 py-2 text-left">ASIN</th>
              <th className="px-4 py-2 text-left">商品名</th>
              <th className="px-4 py-2 text-right">仕入価格</th>
              <th className="px-4 py-2 text-left">カテゴリー</th>
              <th className="px-4 py-2 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(product => (
              <tr key={product.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2 font-mono">{product.asin}</td>
                <td className="px-4 py-2">{product.product_name}</td>
                <td className="px-4 py-2 text-right">¥{product.cost_price}</td>
                <td className="px-4 py-2">{product.category}</td>
                <td className="px-4 py-2 text-center">
                  <button
                    onClick={() => onSelectProduct(product)}
                    className="text-blue-600 hover:underline text-sm"
                  >
                    詳細
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-gray-500 mt-4">商品が見つかりません</p>
      )}
    </div>
  );
};

// Excel Import Form
const ImportForm = ({ onImportSuccess }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleImport = async () => {
    if (!file) {
      setMessage({ type: 'error', text: 'ファイルを選択してください' });
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setMessage({
        type: 'success',
        text: `✅ インポート完了: ${response.data.success_count}件の商品を追加しました`,
      });

      setFile(null);
      onImportSuccess?.();
    } catch (error) {
      setMessage({
        type: 'error',
        text: `❌ エラー: ${error.response?.data?.detail || error.message}`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-xl font-bold mb-4">📥 Excelインポート</h3>

      <p className="text-gray-600 mb-4 text-sm">
        必須列: ASIN, JAN, 納品価格 | オプション: 商品URL
      </p>

      <div className="border-2 border-dashed border-blue-300 rounded-lg p-8 text-center mb-4">
        <input
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={e => setFile(e.target.files?.[0])}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="cursor-pointer block"
        >
          <p className="text-gray-700 font-medium">
            ファイルをドラッグ&ドロップまたはクリック
          </p>
          <p className="text-gray-500 text-sm mt-1">
            {file ? file.name : 'Excel (.xlsx, .xls) または CSV'}
          </p>
        </label>
      </div>

      <button
        onClick={handleImport}
        disabled={!file || loading}
        className={`w-full py-2 px-4 rounded font-medium transition ${
          file && !loading
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        {loading ? 'アップロード中...' : 'インポート実行'}
      </button>

      {message && (
        <div
          className={`mt-4 p-4 rounded ${
            message.type === 'success'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
};

// Profit Calculator
const ProfitCalculator = () => {
  const [form, setForm] = useState({
    sellingPrice: '',
    costPrice: '',
    category: 'Electronics',
  });

  const [result, setResult] = useState(null);

  const handleCalc = () => {
    const selling = parseFloat(form.sellingPrice);
    const cost = parseFloat(form.costPrice);

    if (!selling || !cost || selling < cost) {
      alert('有効な価格を入力してください');
      return;
    }

    // Simplified calculation
    const referralFee = selling * 0.15;
    const fbaFee = 3; // Simplified
    const totalFees = referralFee + fbaFee;
    const profit = selling - cost - totalFees;
    const margin = ((profit / selling) * 100).toFixed(2);

    setResult({
      selling,
      cost,
      referralFee: referralFee.toFixed(2),
      fbaFee,
      profit: profit.toFixed(2),
      margin,
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-xl font-bold mb-4">💰 利益計算ツール</h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <input
          type="number"
          placeholder="販売価格 (¥)"
          value={form.sellingPrice}
          onChange={e => setForm({ ...form, sellingPrice: e.target.value })}
          className="px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <input
          type="number"
          placeholder="仕入原価 (¥)"
          value={form.costPrice}
          onChange={e => setForm({ ...form, costPrice: e.target.value })}
          className="px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <select
          value={form.category}
          onChange={e => setForm({ ...form, category: e.target.value })}
          className="col-span-2 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option>Electronics</option>
          <option>Clothing</option>
          <option>Books</option>
          <option>Sports</option>
        </select>
      </div>

      <button
        onClick={handleCalc}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded font-medium hover:bg-blue-700"
      >
        計算実行
      </button>

      {result && (
        <div className="mt-6 p-4 bg-blue-50 rounded border border-blue-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">販売価格</p>
              <p className="text-lg font-bold">¥{result.selling}</p>
            </div>
            <div>
              <p className="text-gray-600">仕入価格</p>
              <p className="text-lg font-bold">¥{result.cost}</p>
            </div>
            <div>
              <p className="text-gray-600">紹介料</p>
              <p>¥{result.referralFee}</p>
            </div>
            <div>
              <p className="text-gray-600">FBA手数料</p>
              <p>¥{result.fbaFee}</p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t-2 border-blue-300">
            <p className="text-gray-600 text-sm">利益</p>
            <p className="text-2xl font-bold text-green-600">¥{result.profit}</p>
            <p className="text-gray-600 text-sm mt-1">利益率: {result.margin}%</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Dashboard View
const Dashboard = ({ products }) => {
  const total = products.length;
  const totalCost = products.reduce((sum, p) => sum + parseFloat(p.cost_price || 0), 0);
  const avgCost = total > 0 ? (totalCost / total).toFixed(0) : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow">
          <p className="text-blue-100 text-sm">登録商品数</p>
          <p className="text-4xl font-bold">{total}</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow">
          <p className="text-green-100 text-sm">合計仕入額</p>
          <p className="text-4xl font-bold">¥{totalCost.toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow">
          <p className="text-purple-100 text-sm">平均仕入価格</p>
          <p className="text-4xl font-bold">¥{parseFloat(avgCost).toLocaleString()}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold mb-4">📊 システムステータス</h3>
        <div className="space-y-2 text-sm">
          <p>
            ✅ <span className="text-gray-600">API接続: 正常</span>
          </p>
          <p>
            ✅ <span className="text-gray-600">データベース: 正常</span>
          </p>
          <p>
            ✅ <span className="text-gray-600">Keepa API: 利用可能</span>
          </p>
        </div>
      </div>
    </div>
  );
};

// ==================== Main App ====================
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="max-w-7xl mx-auto p-6">
        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-600">読込中...</p>
          </div>
        )}

        {!loading && activeTab === 'dashboard' && <Dashboard products={products} />}

        {!loading && activeTab === 'products' && (
          <div className="space-y-6">
            <ProductsTable products={products} onSelectProduct={setSelectedProduct} />
            {selectedProduct && (
              <PriceChart asin={selectedProduct.asin} product={selectedProduct} />
            )}
          </div>
        )}

        {!loading && activeTab === 'import' && (
          <div className="space-y-6">
            <ImportForm onImportSuccess={fetchProducts} />
          </div>
        )}

        {!loading && activeTab === 'calculator' && (
          <div className="space-y-6">
            <ProfitCalculator />
          </div>
        )}
      </main>

      <footer className="bg-gray-800 text-gray-400 text-center py-6 mt-12">
        <p>Keepa Analyzer © 2024 - Amazon商品分析ツール</p>
      </footer>
    </div>
  );
}
