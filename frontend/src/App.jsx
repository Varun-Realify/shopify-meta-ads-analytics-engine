// Only WooCommerce-related imports are active; others commented out until needed
import { Activity, AlertCircle, Calendar, CreditCard, ShoppingCart } from 'lucide-react';
// import { Activity, AlertCircle, ArrowDownRight, ArrowUpRight, BarChart3, Calendar, DollarSign, LayoutDashboard, ShieldCheck, ShoppingBag, ShoppingCart, TrendingUp } from 'lucide-react';
import { useState } from 'react';
// import { useEffect, useState } from 'react'; // useEffect re-enable when analytics auto-fetch is needed
// import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell as ReCell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'; // charts used by overview/campaigns tabs
import './App.css';
// import GoogleMerchantIntel from './components/GoogleMerchantIntel';

function App() {
  // [COMMENTED OUT — analytics state, not used by WooCommerce tab]
  // const [data, setData] = useState(null);
  // const [loading, setLoading] = useState(true);
  // const [error, setError] = useState(null);

  // Default to WooCommerce tab — no analytics fetch on mount
  const [activeTab, setActiveTab] = useState('woocommerce');

  // [COMMENTED OUT — comparison modal is for Meta ads campaign analysis only]
  // const [comparisonModal, setComparisonModal] = useState({ open: false, data: null, loading: false });
  // const [modalFilter, setModalFilter] = useState('all'); // 'all', 'before', 'during'

  // WooCommerce: stores fetched products, orders and their fetch state
  const [wooData, setWooData] = useState({ products: [], orders: [], loading: false, error: null });

  // Plaid: stores fetched transactions and their fetch state
  const [plaidData, setPlaidData] = useState({ transactions: [], totalExpenses: 0, loading: false, error: null, linked: false });
  

  // [COMMENTED OUT — tooltip header used only in Campaigns table]
  // const HeaderWithInfo = ({ label, info }) => (
  //   <th className="has-tooltip text-left px-4 py-3">
  //     <div className="flex items-center gap-1">
  //       {label} <AlertCircle size={14} className="info-icon" />
  //     </div>
  //     <div className="tooltip-text">
  //       {label === "Recommendation" ? (
  //         <div className="recommendation-legend">
  //           <p className="font-bold mb-2">AI Performance Logic:</p>
  //           <div className="space-y-1">
  //             <p>🔴 <strong>STOP:</strong> Losing money (Loss {'>'} Spend)</p>
  //             <p>⚠️ <strong>OPTIMIZE:</strong> Marginal returns. Needs adjustments.</p>
  //             <p>✅ <strong>SCALE:</strong> Profitable. Ready for 20% increases.</p>
  //             <p>🚀 <strong>AGGRESSIVE:</strong> Exceptional ROI. Scale rapidly.</p>
  //           </div>
  //         </div>
  //       ) : info}
  //     </div>
  //   </th>
  // );

  // Date filters — used by both WooCommerce orders and (future) analytics endpoints
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  // Fetches Plaid transactions for the selected date range
  const fetchPlaid = async () => {
    setPlaidData(prev => ({ ...prev, loading: true, error: null }));

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${baseUrl}/api/v1/plaid/transactions?start_date=${startDate}&end_date=${endDate}&user_id=default`,
        { signal: controller.signal }
      );
      clearTimeout(timeoutId);

      if (!response.ok) throw new Error(`Plaid API error: ${response.status}`);

      const result = await response.json();
      setPlaidData({
        transactions: result.transactions || [],
        totalExpenses: result.total_expenses || 0,
        loading: false,
        error: null,
        linked: true
      });
    } catch (err) {
      clearTimeout(timeoutId);
      const msg = err.name === 'AbortError'
        ? 'Request timed out (15s). Check Plaid connection.'
        : err.message;
      setPlaidData(prev => ({ ...prev, loading: false, error: msg, linked: false }));
    }
  };

  // Fetches WooCommerce products and date-filtered orders from the backend in parallel.
  // Uses AbortController so the UI never hangs — aborts after 15s if the backend is slow.
  const fetchWooCommerce = async () => {
    setWooData(prev => ({ ...prev, loading: true, error: null }));

    // Abort both requests if they don't resolve within 15 seconds
    const controller = new AbortController();
    const timeoutId  = setTimeout(() => controller.abort(), 15000);

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const [productsRes, ordersRes] = await Promise.all([
        fetch(`${baseUrl}/api/v1/woocommerce/products`,
              { signal: controller.signal }),
        fetch(`${baseUrl}/api/v1/woocommerce/orders?start_date=${startDate}&end_date=${endDate}`,
              { signal: controller.signal })
      ]);
      clearTimeout(timeoutId);

      if (!productsRes.ok) throw new Error(`Products API error: ${productsRes.status}`);
      if (!ordersRes.ok)   throw new Error(`Orders API error: ${ordersRes.status}`);

      const products = await productsRes.json();
      const orders   = await ordersRes.json();
      setWooData({ products, orders, loading: false, error: null });
    } catch (err) {
      clearTimeout(timeoutId);
      // AbortError means the 15-second timeout fired — give a clear message
      const msg = err.name === 'AbortError'
        ? 'Request timed out (15s). Check that your WooCommerce site is reachable and credentials are correct.'
        : err.message;
      setWooData(prev => ({ ...prev, loading: false, error: msg }));
    }
  };

  // [COMMENTED OUT — fetches Shopify + Meta analytics overview; caused the infinite loading on mount]
  // const fetchAnalytics = async () => {
  //   setLoading(true);
  //   try {
  //     const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  //     const response = await fetch(`${baseUrl}/api/v1/analytics/overview?start_date=${startDate}&end_date=${endDate}`);
  //     if (!response.ok) throw new Error('Network response was not ok');
  //     const result = await response.json();
  //     setData(result);
  //     setError(null);
  //   } catch (err) {
  //     setError(err.message);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // [COMMENTED OUT — fetches before/after comparison for Meta campaign analysis]
  // const fetchComparison = async (campaignId, productId) => {
  //   setComparisonModal({ open: true, data: null, loading: true });
  //   setModalFilter('all');
  //   try {
  //     const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  //     const prodId = productId || 'default';
  //     const response = await fetch(`${baseUrl}/api/v1/analytics/comparison?campaign_id=${campaignId}&product_id=${prodId}`);
  //     if (!response.ok) {
  //       const errText = await response.text();
  //       throw new Error(`Failed to fetch comparison: ${errText}`);
  //     }
  //     const result = await response.json();
  //     setComparisonModal({ open: true, data: result, loading: false });
  //   } catch (err) {
  //     console.error('Comparison Fetch Error:', err);
  //     setComparisonModal({ open: true, data: null, loading: false, error: err.message });
  //   }
  // };

  // [COMMENTED OUT — was triggering fetchAnalytics on mount, blocking the page on loading spinner]
  // useEffect(() => {
  //   fetchAnalytics();
  // }, [startDate, endDate]);

  // [COMMENTED OUT — these guards blocked the entire render until analytics data arrived]
  // if (loading) return (
  //   <div className="loader-container">
  //     <div className="spinner"></div>
  //     <p style={{ color: 'var(--text-secondary)' }}>Crunching Shopify & Meta Data...</p>
  //   </div>
  // );
  // if (error) return (
  //   <div className="app-container">
  //     <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
  //       <AlertCircle size={48} color="var(--danger)" style={{ margin: '0 auto 1rem' }} />
  //       <h2>Connection Error</h2>
  //       <p style={{ color: 'var(--text-secondary)' }}>Could not connect to Analytics Engine: {error}</p>
  //       <p style={{ fontSize: '0.85rem', marginTop: '1rem', color: 'var(--text-muted)' }}>Make sure uvicorn main:app --reload is running on port 8000.</p>
  //     </div>
  //   </div>
  // );
  // if (!data) return null;

  // [COMMENTED OUT — analytics data destructuring; re-enable when overview tab is restored]
  // const { overview, campaigns, shopify_daily = [], top_orders = [] } = data;

  // Currency formatter — used in WooCommerce products and orders tables
  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

  // [COMMENTED OUT — badge classification for Meta ad recommendation levels]
  // const getBadgeClass = (recLevel) => {
  //   const level = recLevel?.toLowerCase() || '';
  //   if (level.includes('scale')) return 'badge-success';
  //   if (level.includes('optimize')) return 'badge-warning';
  //   if (level.includes('stop')) return 'badge-danger';
  //   return 'badge-pending';
  // };

  // [COMMENTED OUT — chart color palette, used only in overview/campaigns charts]
  // const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <div className="dashboard-container animate-fade-in">
      {/* Sidebar / Navigation */}
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">MI</div>
          <span>Market Intel</span>
        </div>
        <nav className="sidebar-nav">
          {/* [COMMENTED OUT — Overview/Campaigns/Sales tabs require Shopify + Meta analytics data] */}
          {/* <div className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}><LayoutDashboard size={20} /> <span>Overview</span></div> */}
          {/* <div className={`nav-item ${activeTab === 'campaigns' ? 'active' : ''}`} onClick={() => setActiveTab('campaigns')}><BarChart3 size={20} /> <span>Campaigns</span></div> */}
          {/* <div className={`nav-item ${activeTab === 'sales' ? 'active' : ''}`} onClick={() => setActiveTab('sales')}><ShoppingBag size={20} /> <span>Sales</span></div> */}

          {/* WooCommerce tab — fetches products + orders on click */}
          <div
            className={`nav-item ${activeTab === 'woocommerce' ? 'active' : ''}`}
            onClick={() => { setActiveTab('woocommerce'); fetchWooCommerce(); }}
          >
            <ShoppingCart size={20} /> <span>WooCommerce</span>
          </div>

          {/* Plaid tab — fetches bank transactions */}
          <div
            className={`nav-item ${activeTab === 'plaid' ? 'active' : ''}`}
            onClick={() => { setActiveTab('plaid'); fetchPlaid(); }}
          >
            <CreditCard size={20} /> <span>Expenses</span>
          </div>

          {/* <div className={`nav-item ${activeTab === 'google' ? 'active' : ''}`} onClick={() => setActiveTab('google')}><ShieldCheck size={20} /> <span>Google Intel</span></div> */}
        </nav>
      </aside>

      <main className="main-content">
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="dashboard-title">
              {activeTab === 'woocommerce' ? 'WooCommerce Store Overview' : 
               activeTab === 'plaid' ? 'Bank Transactions & Expenses' : 
               'Market Intel Dashboard'}
            </h1>
            <p className="dashboard-subtitle">WooCommerce Analytics Dashboard</p>
          </div>
          <div className="header-actions">
            {/* Date range used to filter WooCommerce orders and Plaid transactions */}
            <div className="date-filters">
              <div className="date-input-group">
                <Calendar size={14} />
                <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <span>→</span>
              <div className="date-input-group">
                <Calendar size={14} />
                <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
            </div>
            {/* Refresh re-fetches data based on active tab */}
            <button className="refresh-btn" onClick={activeTab === 'woocommerce' ? fetchWooCommerce : fetchPlaid}>
              Refresh
            </button>
          </div>
        </header>

        {/* [COMMENTED OUT — Overview KPI cards depend on Shopify + Meta analytics data] */}
        {/* {activeTab === 'overview' && (
          <>
            <div className="kpi-grid"> ... KPI cards (revenue, ad spend, profit, ROAS, COGS, CAC) ... </div>
            <div className="charts-layout"> ... AreaChart + BarChart ... </div>
          </>
        )} */}

        {/* [COMMENTED OUT — Overview/Campaigns/Sales tables all depend on analytics data] */}
        {/* {activeTab === 'overview' ? (
          <div>...Top Campaign Performance + Top Orders tables...</div>
        ) : (
          <div>...Campaign Detailed Analysis / Product Sales Performance tables...</div>
        )} */}

        {/* ── WooCommerce Tab Content ──────────────────────────────────────── */}
        {activeTab === 'woocommerce' && (
          <div className="animate-slide-up">

            {/* Spinner shown while products/orders are being fetched */}
            {wooData.loading && (
              <div className="woo-center-state glass-panel">
                <div className="woo-spinner-ring"></div>
                <p className="woo-state-label">Fetching WooCommerce store data...</p>
              </div>
            )}

            {/* Error state shown if the API call fails */}
            {wooData.error && !wooData.loading && (
              <div className="woo-center-state glass-panel woo-error-state">
                <AlertCircle size={44} color="var(--danger)" />
                <p className="woo-state-title">Connection Failed</p>
                <p className="woo-state-label">{wooData.error}</p>
                <button className="woo-load-btn" onClick={fetchWooCommerce}>Try Again</button>
              </div>
            )}

            {/* Empty / initial state — shown before the user fetches for the first time */}
            {!wooData.loading && !wooData.error && wooData.products.length === 0 && wooData.orders.length === 0 && (
              <div className="woo-center-state glass-panel">
                <div className="woo-store-icon"><ShoppingCart size={36} /></div>
                <p className="woo-state-title">WooCommerce Store</p>
                <p className="woo-state-label">Click below to pull live products and orders from your store.</p>
                <button className="woo-load-btn" onClick={fetchWooCommerce}>
                  <ShoppingCart size={16} style={{ marginRight: 8 }} />
                  Load Store Data
                </button>
              </div>
            )}

            {/* ── KPI summary row + tables, shown once data is loaded ───────── */}
            {!wooData.loading && !wooData.error && (wooData.products.length > 0 || wooData.orders.length > 0) && (() => {
              // Compute WooCommerce KPIs from fetched data
              const totalRevenue = wooData.orders.reduce((sum, o) => sum + (parseFloat(o.total) || 0), 0);
              const completedOrders = wooData.orders.filter(o => o.status === 'completed').length;
              const avgOrderValue = wooData.orders.length > 0 ? totalRevenue / wooData.orders.length : 0;
              const inStockProducts = wooData.products.filter(p => (p.stock ?? 1) > 0).length;

              return (
                <>
                  {/* KPI summary cards derived from WooCommerce API response */}
                  <div className="woo-kpi-grid">
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Total Products</span>
                      <span className="woo-kpi-value">{wooData.products.length}</span>
                      <span className="woo-kpi-sub">{inStockProducts} in stock</span>
                    </div>
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Orders in Period</span>
                      <span className="woo-kpi-value">{wooData.orders.length}</span>
                      <span className="woo-kpi-sub">{completedOrders} completed</span>
                    </div>
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Total Revenue</span>
                      <span className="woo-kpi-value woo-kpi-highlight">{formatCurrency(totalRevenue)}</span>
                      <span className="woo-kpi-sub">Selected date range</span>
                    </div>
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Avg. Order Value</span>
                      <span className="woo-kpi-value">{formatCurrency(avgOrderValue)}</span>
                      <span className="woo-kpi-sub">Per order</span>
                    </div>
                  </div>

                  {/* Products and Orders tables side-by-side */}
                  <div className="woo-tables-grid">

                    {/* Products table — data from /api/v1/woocommerce/products */}
                    <div className="table-container glass-panel">
                      <div className="table-header-flex">
                        <h3 className="chart-title">
                          <ShoppingCart size={16} style={{ display: 'inline', marginRight: 6 }} />
                          Products
                          <span className="woo-count-badge">{wooData.products.length}</span>
                        </h3>
                      </div>
                      <table className="dashboard-table">
                        <thead>
                          <tr>
                            <th>Product Name</th>
                            <th>Type</th>
                            <th>Price</th>
                            <th>Stock</th>
                          </tr>
                        </thead>
                        <tbody>
                          {wooData.products.map((p) => {
                            // Color-code stock level: out = red, low (<5) = yellow, ok = green
                            const stock = p.stock ?? null;
                            const stockClass = stock === 0 ? 'stock-out' : stock !== null && stock < 5 ? 'stock-low' : 'stock-ok';
                            const stockLabel = stock === null ? '—' : stock === 0 ? 'Out' : stock < 5 ? `Low (${stock})` : stock;
                            return (
                              <tr key={p.id} className="woo-table-row">
                                <td className="font-bold">{p.title}</td>
                                <td><span className="woo-type-pill">{p.product_type}</span></td>
                                {/* selling_price normalized to 0 by backend if WooCommerce returns null */}
                                <td className="woo-price-cell">{formatCurrency(p.selling_price || 0)}</td>
                                <td><span className={`woo-stock-badge ${stockClass}`}>{stockLabel}</span></td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Orders table — data from /api/v1/woocommerce/orders filtered by the date range */}
                    <div className="table-container glass-panel">
                      <div className="table-header-flex">
                        <h3 className="chart-title">
                          <Activity size={16} style={{ display: 'inline', marginRight: 6 }} />
                          Orders
                          <span className="woo-count-badge">{wooData.orders.length}</span>
                        </h3>
                      </div>
                      <table className="dashboard-table">
                        <thead>
                          <tr>
                            <th>Order #</th>
                            <th>Date</th>
                            <th>Status</th>
                            <th>Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {wooData.orders.length > 0 ? wooData.orders.map((o) => (
                            <tr key={o.id} className="woo-table-row">
                              <td className="font-bold">#{o.number || o.id}</td>
                              {/* WooCommerce returns ISO datetime — trim to date only */}
                              <td className="woo-date-cell">{(o.date_created || '').slice(0, 10)}</td>
                              {/* Status pill color depends on order lifecycle stage */}
                              <td><span className={`woo-order-status woo-status-${o.status}`}>{o.status}</span></td>
                              <td className="woo-price-cell">{formatCurrency(parseFloat(o.total) || 0)}</td>
                            </tr>
                          )) : (
                            <tr>
                              <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                                No orders found for this date range.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                  </div>
                </>
              );
            })()}
          </div>
        )}

        {/* ── Plaid/Expenses Tab Content ──────────────────────────────────────── */}
        {activeTab === 'plaid' && (
          <div className="animate-slide-up">

            {/* Spinner shown while transactions are being fetched */}
            {plaidData.loading && (
              <div className="woo-center-state glass-panel">
                <div className="woo-spinner-ring"></div>
                <p className="woo-state-label">Fetching bank transactions...</p>
              </div>
            )}

            {/* Error state shown if the API call fails */}
            {plaidData.error && !plaidData.loading && (
              <div className="woo-center-state glass-panel woo-error-state">
                <AlertCircle size={44} color="var(--danger)" />
                <p className="woo-state-title">Connection Failed</p>
                <p className="woo-state-label">{plaidData.error}</p>
                <button className="woo-load-btn" onClick={fetchPlaid}>Try Again</button>
              </div>
            )}

            {/* Empty / initial state — shown before the user fetches for the first time */}
            {!plaidData.loading && !plaidData.error && plaidData.transactions.length === 0 && !plaidData.linked && (
              <div className="woo-center-state glass-panel">
                <div className="woo-store-icon"><CreditCard size={36} /></div>
                <p className="woo-state-title">Bank Transactions</p>
                <p className="woo-state-label">Click below to pull transactions from your linked bank account.</p>
                <button className="woo-load-btn" onClick={fetchPlaid}>
                  <CreditCard size={16} style={{ marginRight: 8 }} />
                  Load Transactions
                </button>
              </div>
            )}

            {/* ── KPI summary row + transactions table, shown once data is loaded ───────── */}
            {!plaidData.loading && !plaidData.error && plaidData.transactions.length > 0 && (() => {
              return (
                <>
                  {/* KPI summary cards for expenses */}
                  <div className="woo-kpi-grid">
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Total Transactions</span>
                      <span className="woo-kpi-value">{plaidData.transactions.length}</span>
                      <span className="woo-kpi-sub">In selected period</span>
                    </div>
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Total Expenses</span>
                      <span className="woo-kpi-value woo-kpi-highlight">{formatCurrency(plaidData.totalExpenses)}</span>
                      <span className="woo-kpi-sub">All transactions</span>
                    </div>
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Avg. Transaction</span>
                      <span className="woo-kpi-value">{formatCurrency(plaidData.transactions.length > 0 ? plaidData.totalExpenses / plaidData.transactions.length : 0)}</span>
                      <span className="woo-kpi-sub">Per transaction</span>
                    </div>
                    <div className="woo-kpi-card glass-panel">
                      <span className="woo-kpi-label">Status</span>
                      <span className="woo-kpi-value" style={{ color: 'var(--success)' }}>Connected</span>
                      <span className="woo-kpi-sub">Plaid Sandbox</span>
                    </div>
                  </div>

                  {/* Transactions table */}
                  <div className="table-container glass-panel">
                    <div className="table-header-flex">
                      <h3 className="chart-title">
                        <CreditCard size={16} style={{ display: 'inline', marginRight: 6 }} />
                        Transactions
                        <span className="woo-count-badge">{plaidData.transactions.length}</span>
                      </h3>
                    </div>
                    <table className="dashboard-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Description</th>
                          <th>Merchant</th>
                          <th>Category</th>
                          <th>Amount</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {plaidData.transactions.map((tx) => (
                          <tr key={tx.transaction_id} className="woo-table-row">
                            <td className="woo-date-cell">{tx.date}</td>
                            <td className="font-bold">{tx.name}</td>
                            <td>{tx.merchant_name || '—'}</td>
                            <td><span className="woo-type-pill">{tx.category || 'Uncategorized'}</span></td>
                            <td className="woo-price-cell" style={{ color: tx.amount > 0 ? 'var(--danger)' : 'var(--success)' }}>
                              {formatCurrency(Math.abs(tx.amount))}
                            </td>
                            <td>
                              <span className={`woo-order-status ${tx.pending ? 'woo-status-pending' : 'woo-status-completed'}`}>
                                {tx.pending ? 'Pending' : 'Completed'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              );
            })()}
          </div>
        )} */}

        {/* [COMMENTED OUT — campaign comparison modal for Meta ads incrementality analysis] */}
        {/* {comparisonModal.open && (
          <div className="modal-overlay" onClick={() => setComparisonModal({ open: false, data: null })}>
            <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
              ... modal with before/during/after filters and BarChart ...
            </div>
          </div>
        )} */}
        )} */}
      </main>
    </div>
  );
}

export default App;