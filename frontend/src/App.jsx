import { AlertCircle, ShoppingBag } from 'lucide-react';
import { useEffect, useState } from 'react';
import './App.css';
// import GoogleMerchantIntel from './components/GoogleMerchantIntel';

function App() {
  const [data, setData] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [activeTab, setActiveTab] = useState('products');
  const [comparisonModal, setComparisonModal] = useState({ open: false, data: null, loading: false });
  const [modalFilter, setModalFilter] = useState('all'); // 'all', 'before', 'during'
  
  const HeaderWithInfo = ({ label, info }) => (
    <th className="has-tooltip text-left px-4 py-3">
      <div className="flex items-center gap-1">
        {label} <AlertCircle size={14} className="info-icon" />
      </div>
      <div className="tooltip-text">
        {label === "Recommendation" ? (
          <div className="recommendation-legend">
            <p className="font-bold mb-2">AI Performance Logic:</p>
            <div className="space-y-1">
              <p>🔴 <strong>STOP:</strong> Losing money (Loss {'>'} Spend)</p>
              <p>⚠️ <strong>OPTIMIZE:</strong> Marginal returns. Needs adjustments.</p>
              <p>✅ <strong>SCALE:</strong> Profitable. Ready for 20% increases.</p>
              <p>🚀 <strong>AGGRESSIVE:</strong> Exceptional ROI. Scale rapidly.</p>
            </div>
          </div>
        ) : info}
      </div>
    </th>
  );

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      // Use fixed dates or let backend handle defaults by removing them from the URL if needed
      const [analyticsRes, productsRes] = await Promise.all([
        fetch(`${baseUrl}/api/v1/analytics/overview`),
        fetch(`${baseUrl}/api/v1/woocommerce/products`)
      ]);

      if (!analyticsRes.ok) {
        const errorData = await analyticsRes.json();
        throw new Error(errorData.detail || 'Analytics fetch failed');
      }
      const analyticsData = await analyticsRes.json();
      setData(analyticsData);

      if (productsRes.ok) {
        const prodData = await productsRes.json();
        setProducts(prodData || []);
      }

      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchComparison = async (campaignId, productId) => {
    setComparisonModal({ open: true, data: null, loading: true });
    setModalFilter('all'); // Reset filter when opening new comparison
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const prodId = productId || 'default';
      const response = await fetch(`${baseUrl}/api/v1/analytics/comparison?campaign_id=${campaignId}&product_id=${prodId}`);
      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Failed to fetch comparison: ${errText}`);
      }
      const result = await response.json();
      setComparisonModal({ open: true, data: result, loading: false });
    } catch (err) {
      console.error('Comparison Fetch Error:', err);
      setComparisonModal({ open: true, data: null, loading: false, error: err.message });
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) return (
    <div className="loader-container">
      <div className="spinner"></div>
      <p style={{ color: 'var(--text-secondary)' }}>Crunching WooCommerce Data...</p>
    </div>
  );

  if (error) return (
    <div className="app-container">
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <AlertCircle size={48} color="var(--danger)" style={{ margin: '0 auto 1rem' }} />
        <h2>Connection Error</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Could not connect to Analytics Engine: {error}</p>
        <p style={{ fontSize: '0.85rem', marginTop: '1rem', color: 'var(--text-muted)' }}>Make sure uvicorn main:app --reload is running on port 8000.</p>
      </div>
    </div>
  );

  if (!data) return null;

  const { overview = {}, campaigns = [], shopify_daily = [], top_orders = [] } = data || {};

  const formatCurrency = (value) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

  const getBadgeClass = (recLevel) => {
    const level = recLevel?.toLowerCase() || '';
    if (level.includes('scale')) return 'badge-success';
    if (level.includes('optimize')) return 'badge-warning';
    if (level.includes('stop')) return 'badge-danger';
    return 'badge-pending';
  };

  // Chart Colors (PowerBI Palette)
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <div className="dashboard-container animate-fade-in">
      {/* Sidebar / Navigation (Simulated PowerBI Sidebar) */}
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">MI</div>
          <span>Market Intel</span>
        </div>
        <nav className="sidebar-nav">
          {/* <div className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}><LayoutDashboard size={20} /> <span>Overview</span></div> */}
          {/* <div className={`nav-item ${activeTab === 'campaigns' ? 'active' : ''}`} onClick={() => setActiveTab('campaigns')}><BarChart3 size={20} /> <span>Campaigns</span></div> */}
          {/* <div className={`nav-item ${activeTab === 'sales' ? 'active' : ''}`} onClick={() => setActiveTab('sales')}><ShoppingBag size={20} /> <span>Sales</span></div> */}
          <div className={`nav-item ${activeTab === 'products' ? 'active' : ''}`} onClick={() => setActiveTab('products')}><ShoppingBag size={20} /> <span>WooCommerce</span></div>
          {/* <div className={`nav-item ${activeTab === 'google' ? 'active' : ''}`} onClick={() => setActiveTab('google')}><ShieldCheck size={20} /> <span>Google Intel</span></div> */}
        </nav>
      </aside>

      <main className="main-content">
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="dashboard-title">
              {activeTab === 'products' ? 'WooCommerce Products' : 'WooCommerce Store Overview'}
            </h1>
            <p className="dashboard-subtitle">WooCommerce Analytics Dashboard</p>
          </div>
          <div className="header-actions">
            <button className="refresh-btn" onClick={fetchAnalytics}>Refresh</button>
          </div>
        </header>

        {/* {activeTab === 'overview' && (
          <>
            {/* KPI Row * /}
            <div className="kpi-grid">
              <div className="kpi-card glass-panel">
                <div className="kpi-header">
                  <span className="kpi-label">TOTAL REVENUE</span>
                  <DollarSign size={18} className="icon-blue" />
                </div>
                <div className="kpi-value">{formatCurrency(overview.total_revenue)}</div>
                <div className="kpi-footer text-success"><ArrowUpRight size={14} /> 12% vs last month</div>
              </div>
              
              <div className="kpi-card glass-panel">
                <div className="kpi-header">
                  <span className="kpi-label">AD SPEND</span>
                  <Activity size={18} className="icon-warning" />
                </div>
                <div className="kpi-value">{formatCurrency(overview.total_ad_spend)}</div>
                <div className="kpi-footer text-warning"><ArrowUpRight size={14} /> 5% vs last month</div>
              </div>

              <div className="kpi-card glass-panel">
                <div className="kpi-header">
                  <span className="kpi-label">NET PROFIT</span>
                  <TrendingUp size={18} className="icon-success" />
                </div>
                <div className="kpi-value">{formatCurrency(overview.total_profit)}</div>
                <div className="kpi-footer text-success"><ArrowUpRight size={14} /> 8.4% growth</div>
              </div>

              <div className="kpi-card glass-panel">
                <div className="kpi-header">
                  <span className="kpi-label">ROAS</span>
                  <LayoutDashboard size={18} className="icon-purple" />
                </div>
                <div className="kpi-value">{overview.blended_roas.toFixed(2)}x</div>
                <div className="kpi-footer text-danger"><ArrowDownRight size={14} /> -0.2 drop</div>
              </div>

              <div className="kpi-card glass-panel">
                <div className="kpi-header">
                  <span className="kpi-label">TOTAL COGS</span>
                  <ShoppingBag size={18} className="icon-warning" />
                </div>
                <div className="kpi-value">{formatCurrency(overview.total_cogs || 0)}</div>
                <div className="kpi-footer text-muted">Cost of Goods Sold</div>
              </div>

              <div className="kpi-card glass-panel">
                <div className="kpi-header">
                  <span className="kpi-label">CAC</span>
                  <Activity size={18} className="icon-blue" />
                </div>
                <div className="kpi-value">{formatCurrency(overview.cac || 0)}</div>
                <div className="kpi-footer text-muted">Customer Acquisition Cost</div>
              </div>
            </div>

            {/* Charts Section * /}
            <div className="charts-layout">
              <div className="chart-container glass-panel lg-span">
                <h3 className="chart-title">Revenue & Ad Spend Trend</h3>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer>
                    <AreaChart data={shopify_daily.length > 0 ? shopify_daily : [{date: startDate, revenue: 0}, {date: endDate, revenue: 0}]}>
                      <defs>
                        <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8884d8" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3f" vertical={false} />
                      <XAxis dataKey="date" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#1a1c24', border: '1px solid #3b3f4e' }} />
                      <Area type="monotone" dataKey="revenue" stroke="#8884d8" fillOpacity={1} fill="url(#colorRev)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-container glass-panel sm-span">
                <h3 className="chart-title">Campaign Spend vs Revenue</h3>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer>
                    <BarChart data={campaigns.slice(0, 5)}>
                      <XAxis dataKey="campaign_name" hide />
                      <Tooltip contentStyle={{ backgroundColor: '#1a1c24', border: '1px solid #3b3f4e' }} />
                      <Bar dataKey="ad_spend" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="revenue" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            </>
          )} */}

        {/* {activeTab === 'google' && (
          <div className="animate-slide-up">
            <GoogleMerchantIntel baseUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000'} />
          </div>
        )} */}

        {activeTab === 'products' && (
          <div className="table-container glass-panel animate-slide-up">
            <div className="table-header-flex">
              <h3 className="chart-title">Current Inventory</h3>
              <div className="legend-pills">
                <span className="legend-item"><span className="status-dot"></span> {products.length} Products</span>
              </div>
            </div>
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Vendor</th>
                  <th>Type</th>
                  <th>Price</th>
                  <th>Cost</th>
                  <th>Stock</th>
                </tr>
              </thead>
              <tbody>
                {products.length > 0 ? products.map((p) => (
                  <tr key={p.id}>
                    <td className="font-bold">{p.title}</td>
                    <td>{p.vendor}</td>
                    <td>{p.product_type}</td>
                    <td className="text-accent">{formatCurrency(p.selling_price)}</td>
                    <td>{formatCurrency(p.cost_price)}</td>
                    <td className={p.stock < 10 ? 'text-danger' : ''}>{p.stock}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No products found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab-specific Tables */}
        {/* {activeTab === 'overview' ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div className="table-container glass-panel">
              <div className="table-header-flex">
                <h3 className="chart-title">Top Campaign Performance</h3>
              </div>
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Campaign Name</th>
                    <th>Spend</th>
                    <th>Revenue</th>
                    <th>True ROAS</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.slice(0, 5).map((camp) => (
                    <tr key={camp.campaign_id}>
                      <td className="font-bold">{camp.campaign_name}</td>
                      <td>{formatCurrency(camp.ad_spend)}</td>
                      <td>{formatCurrency(camp.revenue)}</td>
                      <td className="text-accent">{camp.true_roas.toFixed(2)}x</td>
                      <td>
                        <button className="table-btn" 
                          onClick={() => fetchComparison(camp.campaign_id, camp.product_id)}>
                          Compare
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="table-container glass-panel">
              <div className="table-header-flex">
                <h3 className="chart-title">Top Orders</h3>
              </div>
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Qty Sold</th>
                    <th>Revenue</th>
                    <th>Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {top_orders && top_orders.length > 0 ? top_orders.map((p, i) => (
                    <tr key={i}>
                      <td className="font-bold">{p.product_title}</td>
                      <td>{p.total_quantity}</td>
                      <td>{formatCurrency(p.total_revenue || 0)}</td>
                      <td className={(p.total_profit || 0) >= 0 ? 'text-success' : 'text-danger'}>{formatCurrency(p.total_profit || 0)}</td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)' }}>
                        No orders currently loading for this period.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="table-container glass-panel">
            <div className="table-header-flex">
              <h3 className="chart-title">
                {activeTab === 'campaigns' ? 'Campaign Detailed Analysis' : 'Product Sales Performance'}
              </h3>
              
              {activeTab !== 'sales' && (
                <div className="legend-pills">
                  <span className="legend-item"><span className="status-dot"></span> Active</span>
                  <span className="legend-item"><span className="pill badge-success">SCALE</span></span>
                  <span className="legend-item"><span className="pill badge-warning">OPTIMIZE</span></span>
                  <span className="legend-item"><span className="pill badge-danger">STOP</span></span>
                </div>
              )}
            </div>
            
            <table className="dashboard-table">
              <thead>
                {activeTab !== 'sales' ? (
                  <tr>
                    <th>Campaign Name</th>
                    <HeaderWithInfo label="Status" info="Current delivery state from Meta Ads Manager." />
                    <HeaderWithInfo label="Recommendation" info="AI advice based on your ROAS vs Product Costs." />
                    <th>Spend</th>
                    <th>Revenue</th>
                    <th>True ROAS</th>
                    <th>Actions</th>
                  </tr>
                ) : (
                  <tr>
                    <th>Product</th>
                    <th>Units Sold</th>
                    <th>Total Revenue</th>
                    <th>Order Count</th>
                  </tr>
                )}
              </thead>
              <tbody>
                {activeTab !== 'sales' ? 
                  campaigns.map((camp) => (
                    <tr key={camp.campaign_id}>
                      <td className="font-bold">{camp.campaign_name}</td>
                      <td><span className={`status-pill ${camp.status?.toLowerCase()}`}>
                        <span className="status-dot"></span> {camp.status}
                      </span></td>
                      <td><span className={`pill ${getBadgeClass(camp.recommendation_level)}`}>{camp.recommendation_level}</span></td>
                      <td>{formatCurrency(camp.ad_spend)}</td>
                      <td>{formatCurrency(camp.revenue)}</td>
                      <td className="text-accent">{camp.true_roas.toFixed(2)}x</td>
                      <td>
                        <button className="table-btn" 
                          onClick={() => fetchComparison(camp.campaign_id, camp.product_id)}>
                          Compare Impact
                        </button>
                      </td>
                    </tr>
                  )) : 
                  // Product Sales Rows
                  shopify_daily.map((p, i) => (
                    <tr key={i}>
                      <td className="font-bold">{p.date}</td>
                      <td>{p.units_sold}</td>
                      <td>{formatCurrency(p.revenue)}</td>
                      <td>Orders Managed</td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
          </div>
        )} */}

        {/* Modal for Comparison */}
        {/* {comparisonModal.open && (
          <div className="modal-overlay" onClick={() => setComparisonModal({ open: false, data: null })}>
            <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Campaign Incrementality Analysis</h2>
                <button className="close-btn" onClick={() => setComparisonModal({ open: false, data: null })}>×</button>
              </div>
              
              {comparisonModal.loading ? (
                <div className="modal-loader">Analysing incrementality...</div>
              ) : comparisonModal.data ? (
                <div className="modal-body animate-fade-in">
                  <div className="comparison-meta">
                    <p><strong>Campaign:</strong> {comparisonModal.data.campaign}</p>
                    <p><strong>Window:</strong> {comparisonModal.data.window_days} Days</p>
                  </div>

                  <div className="modal-tabs" style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid #2a2e3f', paddingBottom: '10px' }}>
                    <button 
                      className={`tab-btn ${modalFilter === 'all' ? 'active' : ''}`}
                      onClick={() => setModalFilter('all')}
                      style={{ 
                        background: modalFilter === 'all' ? 'rgba(139, 92, 246, 0.1)' : 'transparent', 
                        color: modalFilter === 'all' ? '#8b5cf6' : '#9ca3af', 
                        border: modalFilter === 'all' ? '1px solid #8b5cf6' : '1px solid #3b3f4e', 
                        padding: '8px 20px', 
                        borderRadius: '6px',
                        cursor: 'pointer', 
                        fontWeight: '600',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      Compare All
                    </button>
                    <button 
                      className={`tab-btn ${modalFilter === 'before' ? 'active' : ''}`}
                      onClick={() => setModalFilter('before')}
                      style={{ 
                        background: modalFilter === 'before' ? 'rgba(107, 114, 128, 0.1)' : 'transparent', 
                        color: modalFilter === 'before' ? '#fff' : '#9ca3af', 
                        border: modalFilter === 'before' ? '1px solid #6b7280' : '1px solid #3b3f4e', 
                        padding: '8px 20px', 
                        borderRadius: '6px',
                        cursor: 'pointer', 
                        fontWeight: '600',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      Before Ad
                    </button>
                    <button 
                      className={`tab-btn ${modalFilter === 'during' ? 'active' : ''}`}
                      onClick={() => setModalFilter('during')}
                      style={{ 
                        background: modalFilter === 'during' ? 'rgba(139, 92, 246, 0.1)' : 'transparent', 
                        color: modalFilter === 'during' ? '#a78bfa' : '#9ca3af', 
                        border: modalFilter === 'during' ? '1px solid #8b5cf6' : '1px solid #3b3f4e', 
                        padding: '8px 20px', 
                        borderRadius: '6px',
                        cursor: 'pointer', 
                        fontWeight: '600',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      After Ad (During)
                    </button>
                  </div>

                  <div className="comparison-metrics-row">
                    {(modalFilter === 'all' || modalFilter === 'before') && (
                      <div className="comp-metric">
                        <span className="comp-label">Exact Amount of Products Sold (Before)</span>
                        <span className="comp-val">{comparisonModal.data.stats.total_before}</span>
                      </div>
                    )}
                    {(modalFilter === 'all' || modalFilter === 'during') && (
                      <div className="comp-metric highlight">
                        <span className="comp-label">Exact Amount of Products Sold (During)</span>
                        <span className="comp-val">{comparisonModal.data.stats.total_during}</span>
                      </div>
                    )}
                    {modalFilter === 'all' && (
                      <div className={`comp-metric ${comparisonModal.data.stats.sales_lift_pct >= 0 ? 'text-success' : 'text-danger'}`}>
                        <span className="comp-label">Sales Lift</span>
                        <span className="comp-val">{comparisonModal.data.stats.sales_lift_pct > 0 ? '+' : ''}{comparisonModal.data.stats.sales_lift_pct.toFixed(1)}%</span>
                      </div>
                    )}
                  </div>

                  <h3 className="chart-title small">
                    {modalFilter === 'all' ? 'Full Historical Comparison' : 
                     modalFilter === 'before' ? 'Performance Before Ad' : 
                     'Performance During Ad'}
                  </h3>
                  <div style={{ width: '100%', minWidth: '400px', height: 250 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={[
                        ...(modalFilter === 'all' || modalFilter === 'before' ? (comparisonModal.data.raw_data.before || []).map(d => ({ ...d, period: 'Before' })) : []),
                        ...(modalFilter === 'all' || modalFilter === 'during' ? (comparisonModal.data.raw_data.during || []).map(d => ({ ...d, period: 'During' })) : [])
                      ]}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3f" vertical={false} />
                        <XAxis dataKey="date" stroke="#6b7280" fontSize= {10} tickLine={false} />
                        <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1a1c24', border: '1px solid #3b3f4e' }}
                          itemStyle={{ color: '#fff' }}
                        />
                        <Bar dataKey="units_sold">
                          {[
                            ...(modalFilter === 'all' || modalFilter === 'before' ? (comparisonModal.data.raw_data.before || []).map(() => '#3b3f4e') : []),
                            ...(modalFilter === 'all' || modalFilter === 'during' ? (comparisonModal.data.raw_data.during || []).map(() => '#8b5cf6') : [])
                          ].map((entry, index) => (
                            <ReCell key={`cell-${index}`} fill={entry} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="chart-legend" style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '10px' }}>
                      <span className="legend-item" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <div style={{ width: '12px', height: '12px', backgroundColor: '#3b3f4e', borderRadius: '2px' }}></div> 
                        <span style={{ fontSize: '12px', color: '#9ca3af' }}>Before Ad</span>
                      </span>
                      <span className="legend-item" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <div style={{ width: '12px', height: '12px', backgroundColor: '#8b5cf6', borderRadius: '2px' }}></div> 
                        <span style={{ fontSize: '12px', color: '#9ca3af' }}>During Ad</span>
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="error-text">{comparisonModal.error || "No data available for this campaign."}</div>
              )}
            </div>
          </div>
        )} */}
      </main>
    </div>
  );
}

export default App;
