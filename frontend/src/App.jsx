// Only WooCommerce-related imports are active; others commented out until needed
import { Activity, AlertCircle, Calendar, CreditCard, DollarSign, Lock, ShoppingCart, Link } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { usePlaidLink } from 'react-plaid-link';
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
  const [plaidData, setPlaidData] = useState({
    transactions: [],
    totalExpenses: 0,
    loading: false,
    error: null,
    linked: false
  });
  const [plaidUserId, setPlaidUserId] = useState("");
  const [plaidLinkToken, setPlaidLinkToken] = useState(null);
  const [plaidConnecting, setPlaidConnecting] = useState(false);

  const [qbData, setQbData] = useState({
    summary: null,
    loading: false,
    error: null,
    isConnected: false 
  });


  // Stripe Connect state
  const [stripeConnectData, setStripeConnectData] = useState({ transactions: [], loading: false, error: null, isConnected: false });
  const [currentUserId, setCurrentUserId] = useState("");

  // Check URL parameters on mount for Stripe Connect success
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('stripe_connected') === 'success') {
      // Get the ID from the URL or fallback to what we saved in localStorage before redirecting
      const connectedUserId = params.get('user_id') || localStorage.getItem('stripe_connect_temp_user_id');
      setCurrentUserId(connectedUserId);
      setStripeConnectData(prev => ({ ...prev, isConnected: true }));
      setActiveTab('stripe-connect');
      // Remove URL parameter without reloading
      window.history.replaceState({}, document.title, window.location.pathname);
      // Fetch the data immediately
      fetchStripeConnect(connectedUserId);
    }

    if (params.get('qb_connected') === 'success') {
      const qbUserId = params.get('user_id') || localStorage.getItem('qb_temp_user_id');
      localStorage.setItem('qb_temp_user_id', qbUserId);
      setQbData(prev => ({ ...prev, isConnected: true }));
      setActiveTab('quickbooks');
      window.history.replaceState({}, document.title, window.location.pathname);
      fetchQuickBooks(qbUserId);
    }
  }, []);

  const handleStripeConnectLogin = () => {
    // Generate a unique user ID behind the scenes so the user doesn't have to type anything
    const dynamicUserId = "user_" + Math.random().toString(36).substr(2, 9);
    setCurrentUserId(dynamicUserId);
    localStorage.setItem('stripe_connect_temp_user_id', dynamicUserId);

    // Generate OAuth URL
    const client_id = 'ca_UR4O1ElJxeIDF5JX2vNU8U9BkM7ZnIai'; // From backend
    const redirect_uri = 'http://localhost:8000/api/v1/stripe/callback';
    const authUrl = `https://connect.stripe.com/oauth/authorize?response_type=code&client_id=${client_id}&scope=read_write&redirect_uri=${redirect_uri}&state=${dynamicUserId}`;
    window.location.href = authUrl;
  };

  const fetchStripeConnect = async (userIdToFetch = null) => {
    const userId = userIdToFetch || currentUserId;
    if (!userId.trim()) {
      setStripeConnectData(prev => ({ ...prev, error: "Please enter a User ID", isConnected: false }));
      return;
    }

    setStripeConnectData(prev => ({ ...prev, loading: true, error: null }));
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${baseUrl}/api/v1/stripe/history/${userId}`);
      
      if (!res.ok) {
        if (res.status === 404 || res.status === 400) {
           throw new Error("STRIPE_NOT_CONNECTED");
        }
        throw new Error("Failed to fetch Stripe data");
      }
      
      const data = await res.json();
      setStripeConnectData({
        transactions: data.data || [],
        loading: false,
        error: null,
        isConnected: true
      });
    } catch (err) {
      setStripeConnectData(prev => ({
        ...prev,
        loading: false,
        error: err.message,
        isConnected: false
      }));
    }
  };


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
    if (!plaidUserId.trim()) {
      setPlaidData(prev => ({
        ...prev,
        error: "Please enter a User ID first.",
        linked: false
      }));
      return;
    }

    setPlaidData(prev => ({ ...prev, loading: true, error: null }));

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(
        `${baseUrl}/api/v1/plaid/transactions?start_date=${startDate}&end_date=${endDate}&user_id=${encodeURIComponent(plaidUserId)}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("PLAID_NOT_CONNECTED");
        }
        throw new Error(`Plaid API error: ${response.status}`);
      }

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

      setPlaidData(prev => ({
        ...prev,
        loading: false,
        error: msg,
        linked: false
      }));
    }
  };

  const handlePlaidConnect = async () => {
    if (!plaidUserId.trim()) {
      setPlaidData(prev => ({
        ...prev,
        error: "Please enter a User ID first."
      }));
      return;
    }

    setPlaidConnecting(true);
    setPlaidData(prev => ({ ...prev, error: null }));

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${baseUrl}/api/v1/plaid/link_token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: plaidUserId })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to create Plaid Link token: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      if (!data.link_token) {
        throw new Error("No link_token returned from backend.");
      }

      setPlaidLinkToken(data.link_token);
    } catch (err) {
      setPlaidData(prev => ({
        ...prev,
        error: err.message,
        linked: false
      }));
      setPlaidConnecting(false);
    }
  };

  const onPlaidSuccess = useCallback(async (publicToken) => {
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${baseUrl}/api/v1/plaid/exchange_token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: plaidUserId,
          public_token: publicToken
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Plaid token exchange failed: ${response.status} - ${errorText}`);
      }

      await response.json();

      setPlaidData(prev => ({
        ...prev,
        linked: true,
        error: null
      }));

      await fetchPlaid();
    } catch (err) {
      setPlaidData(prev => ({
        ...prev,
        error: err.message,
        linked: false
      }));
    } finally {
      setPlaidConnecting(false);
      setPlaidLinkToken(null);
    }
  }, [plaidUserId, startDate, endDate]);

  const { open, ready } = usePlaidLink({
    token: plaidLinkToken,
    onSuccess: onPlaidSuccess,
  });

  useEffect(() => {
    if (plaidLinkToken && ready) {
      open();
    }
  }, [plaidLinkToken, ready, open]);

  const handleQBLogin = async () => {
    try {
      const dynamicUserId = "qb_user_" + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('qb_temp_user_id', dynamicUserId);

      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${baseUrl}/api/v1/quickbooks/auth?user_id=${dynamicUserId}`);
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Failed to get QB auth URL", err);
    }
  };

  const handleQBDisconnect = () => {
    localStorage.removeItem('qb_temp_user_id');
    setQbData({ summary: null, loading: false, error: null, isConnected: false });
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
        ? 'Request timeout. Check WooCommerce site.'
        : err.message;
      setWooData(prev => ({ ...prev, loading: false, error: msg }));
    }
  };

  const fetchQuickBooks = async (userIdToFetch = null) => {
    const userId = userIdToFetch || localStorage.getItem('qb_temp_user_id');
    if (!userId) {
      setQbData(prev => ({ ...prev, error: "QB_NOT_CONNECTED", isConnected: false }));
      return;
    }

    setQbData(prev => ({ ...prev, loading: true, error: null }));

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      // Pass dates to QuickBooks as well
      const res = await fetch(`${baseUrl}/api/v1/quickbooks/profit-loss?start_date=${startDate}&end_date=${endDate}&user_id=${userId}`);

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        // If not connected, we should offer to connect
        if (res.status === 400 || res.status === 401) {
          throw new Error("QB_NOT_CONNECTED");
        }
        throw new Error(errorData.detail || "QuickBooks API failed");
      }

      const data = await res.json();

    const rows = data?.data?.Rows?.Row || [];

    let income = 0;
    let expenses = 0;
    let net = 0;

    rows.forEach(section => {
      const group = section.group;

      if (section.Summary?.ColData?.[1]?.value) {
        const value = parseFloat(section.Summary.ColData[1].value);

        if (group === "Income") income = value;
        if (group === "Expenses") expenses = value;
        if (group === "NetIncome") net = value;
      }
    });

    setQbData({
      summary: { income, expenses, net },
      loading: false,
      error: null,
      isConnected: true
    });

  } catch (err) {
    setQbData(prev => ({
      ...prev,
      loading: false,
      error: err.message,
      isConnected: false
    }));
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
            onClick={() => { setActiveTab('plaid'); }}
          >
            <CreditCard size={20} /> <span>Expenses</span>
          </div>

          {/* QuickBooks tab — fetches accounting data */}
          <div
            className={`nav-item ${activeTab === 'quickbooks' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('quickbooks'); fetchQuickBooks(); }}>
            <Activity size={20} /> <span>Accounting</span>
          </div>

          {/* Stripe Connect tab */}
          <div
            className={`nav-item ${activeTab === 'stripe-connect' ? 'active' : ''}`}
            onClick={() => { setActiveTab('stripe-connect'); fetchStripeConnect(); }}
          >
            <Link size={20} /> <span>Stripe Connect</span>
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
               activeTab === 'quickbooks' ? 'QuickBooks Accounting' : 
               'Market Intel Dashboard'}
            </h1>
            <p className="dashboard-subtitle">
              {activeTab === 'woocommerce' && 'WooCommerce Analytics Dashboard'}
              {activeTab === 'plaid' && 'Bank Transactions & Expenses'}
              {activeTab === 'quickbooks' && 'QuickBooks Profit & Loss'}
              {activeTab === 'stripe-connect' && 'Stripe Connected Account Transactions'}
              {!activeTab && 'Market Intel Dashboard'}
            </p>
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
            <button className="refresh-btn" onClick={
              activeTab === 'woocommerce' ? fetchWooCommerce : 
              activeTab === 'plaid' ? fetchPlaid : 
              activeTab === 'quickbooks' ? fetchQuickBooks : 
              fetchWooCommerce
            }>
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
              <div
                className="woo-center-state glass-panel woo-error-state"
                style={{
                  gap: '1.25rem',
                  padding: '2.5rem'
                }}
              >
                <AlertCircle size={44} color="var(--danger)" />

                <div style={{ textAlign: 'center' }}>
                  <p className="woo-state-title">
                    {plaidData.error === "PLAID_NOT_CONNECTED"
                      ? "Bank Not Connected"
                      : "Action Required"}
                  </p>

                  <p className="woo-state-label">
                    {plaidData.error === "Please enter a User ID first."
                      ? "Enter a user ID before connecting or loading transactions."
                      : plaidData.error === "PLAID_NOT_CONNECTED"
                      ? "No Plaid connection found for this user. Connect a bank account first."
                      : plaidData.error}
                  </p>
                </div>

                <div
                  style={{
                    width: '100%',
                    maxWidth: 520,
                    display: 'flex',
                    gap: '0.75rem',
                    alignItems: 'center'
                  }}
                >
                  <input
                    type="text"
                    value={plaidUserId}
                    onChange={(e) => setPlaidUserId(e.target.value)}
                    placeholder="Enter user id"
                    style={{
                      flex: 1,
                      padding: '0.95rem 1rem',
                      borderRadius: 14
                    }}
                  />

                  <button
                    className="woo-load-btn"
                    onClick={handlePlaidConnect}
                    disabled={plaidConnecting}
                  >
                    {plaidConnecting ? "Connecting..." : "Connect"}
                  </button>
                </div>

                <button className="refresh-btn" onClick={fetchPlaid}>
                  Load Transactions
                </button>
              </div>
            )}

            {/* Empty / initial state — shown before the user fetches for the first time */}
            {!plaidData.loading && !plaidData.error && plaidData.transactions.length === 0 && !plaidData.linked && (
              <div
                className="woo-center-state glass-panel"
                style={{
                  gap: '1.35rem',
                  padding: '2.75rem'
                }}
              >
                <div className="woo-store-icon">
                  <CreditCard size={36} />
                </div>

                <div style={{ textAlign: 'center' }}>
                  <p className="woo-state-title">Connect Bank Account</p>

                  <p className="woo-state-label">
                    Enter a user ID, connect Plaid, then load that user's transactions.
                  </p>
                </div>

                <div
                  style={{
                    width: '100%',
                    maxWidth: 560,
                    display: 'flex',
                    gap: '0.85rem',
                    alignItems: 'center'
                  }}
                >
                  <input
                    type="text"
                    value={plaidUserId}
                    onChange={(e) => setPlaidUserId(e.target.value)}
                    placeholder="Enter user id"
                    style={{
                      flex: 1,
                      padding: '1rem 1.1rem',
                      borderRadius: 14
                    }}
                  />

                  <button
                    className="woo-load-btn"
                    onClick={handlePlaidConnect}
                    disabled={plaidConnecting}
                  >
                    <CreditCard size={16} style={{ marginRight: 8 }} />
                    {plaidConnecting ? "Connecting..." : "Connect"}
                  </button>
                </div>

                <button className="refresh-btn" onClick={fetchPlaid}>
                  Load Transactions
                </button>
              </div>
            )}

            {/* ── KPI summary row + transactions table, shown once data is loaded ───────── */}
            {!plaidData.loading && !plaidData.error && plaidData.transactions.length > 0 && (() => {
              return (
                <>
                  <div
                    className="table-container glass-panel"
                    style={{
                      marginBottom: '1.5rem',
                      padding: '1.25rem'
                    }}
                  >
                    <div
                      className="table-header-flex"
                      style={{
                        gap: '1rem'
                      }}
                    >
                      <h3 className="chart-title">
                        <CreditCard
                          size={16}
                          style={{ display: 'inline', marginRight: 6 }}
                        />
                        Plaid User
                      </h3>

                      <button className="refresh-btn" onClick={fetchPlaid}>
                        Refresh
                      </button>
                    </div>

                    <div
                      style={{
                        marginTop: '1.25rem',
                        display: 'flex',
                        gap: '0.85rem',
                        alignItems: 'center',
                        maxWidth: 560
                      }}
                    >
                      <input
                        type="text"
                        value={plaidUserId}
                        onChange={(e) => setPlaidUserId(e.target.value)}
                        placeholder="Enter user id"
                        style={{
                          flex: 1,
                          padding: '1rem 1.1rem',
                          borderRadius: 14
                        }}
                      />

                      <button className="woo-load-btn" onClick={fetchPlaid}>
                        Load User
                      </button>

                      <button
                        className="refresh-btn"
                        onClick={handlePlaidConnect}
                        disabled={plaidConnecting}
                      >
                        Connect New Bank
                      </button>
                    </div>
                  </div>

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
        )}

        {/* ── QuickBooks/Accounting Tab Content ──────────────────────────────────────── */}
        {activeTab === 'quickbooks' && (
          <div className="animate-slide-up">

            {/* Step 1: Force Login if isConnected is false (even if tokens exist in .env) */}
            {!qbData.isConnected && !qbData.loading && (
              <div className="woo-center-state glass-panel">
                <div className="woo-store-icon" style={{ background: 'rgba(44, 160, 28, 0.1)' }}>
                  <Activity size={36} color="#2ca01c" />
                </div>
                <p className="woo-state-title">Connect QuickBooks</p>
                <p className="woo-state-label">To view your Profit & Loss, please authorize your account first.</p>
                <button className="woo-load-btn" onClick={handleQBLogin} style={{ background: '#2ca01c', padding: '1rem 2.5rem', fontSize: '1.1rem' }}>
                  <Activity size={18} style={{ marginRight: 10 }} />
                  Login with QuickBooks
                </button>
              </div>
            )}

            {/* Step 2: Spinner shown while data is being fetched */}
            {qbData.loading && (
              <div className="woo-center-state glass-panel">
                <div className="woo-spinner-ring"></div>
                <p className="woo-state-label">Fetching QuickBooks accounting data...</p>
              </div>
            )}

            {/* Error state */}
            {qbData.error && !qbData.loading && qbData.error !== "QB_NOT_CONNECTED" && (
              <div className="woo-center-state glass-panel woo-error-state">
                <AlertCircle size={44} color="var(--danger)" />
                <p className="woo-state-title">Connection Failed</p>
                <p className="woo-state-label">{qbData.error}</p>
                <button className="woo-load-btn" onClick={handleQBLogin}>Re-authenticate</button>
              </div>
            )}

            {/* Step 3: Show Data only after successful login/fetch */}
            {qbData.isConnected && qbData.summary && !qbData.loading && (
              <>
                <div className="woo-kpi-grid">
                  <div className="woo-kpi-card glass-panel">
                    <span className="woo-kpi-label">Total Income</span>
                    <span className="woo-kpi-value woo-kpi-highlight">{formatCurrency(qbData.summary.income)}</span>
                    <span className="woo-kpi-sub">Revenue</span>
                  </div>
                  <div className="woo-kpi-card glass-panel">
                    <span className="woo-kpi-label">Total Expenses</span>
                    <span className="woo-kpi-value" style={{ color: 'var(--danger)' }}>{formatCurrency(qbData.summary.expenses)}</span>
                    <span className="woo-kpi-sub">Costs</span>
                  </div>
                  <div className="woo-kpi-card glass-panel">
                    <span className="woo-kpi-label">Net Profit</span>
                    <span className="woo-kpi-value" style={{ color: qbData.summary.net >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                      {formatCurrency(qbData.summary.net)}
                    </span>
                    <span className="woo-kpi-sub">Bottom Line</span>
                  </div>
                  <div className="woo-kpi-card glass-panel" onClick={handleQBLogin} style={{ cursor: 'pointer' }}>
                    <span className="woo-kpi-label">Status</span>
                    <span className="woo-kpi-value" style={{ color: 'var(--success)' }}>Connected</span>
                    <span className="woo-kpi-sub">QuickBooks Online (Switch?)</span>
                  </div>
                </div>

                <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                  <button className="woo-load-btn" onClick={fetchQuickBooks} style={{ marginRight: '10px' }}>
                    <Activity size={16} style={{ marginRight: 8 }} />
                    Refresh Data
                  </button>
                  <button className="woo-load-btn" onClick={handleQBLogin} style={{ background: '#2ca01c', opacity: 0.8, marginRight: '10px' }}>
                    <Activity size={16} style={{ marginRight: 8 }} />
                    Switch Account
                  </button>
                  <button className="woo-load-btn" onClick={handleQBDisconnect} style={{ background: 'var(--danger)' }}>
                    Disconnect
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Stripe Connect Tab Content ──────────────────────────────────────── */}
        {activeTab === 'stripe-connect' && (
          <div className="animate-slide-up">
            {/* Step 1: Force Login if isConnected is false */}
            {!stripeConnectData.isConnected && !stripeConnectData.loading && (
              <div className="woo-center-state glass-panel">
                <div className="woo-store-icon" style={{ background: 'rgba(99, 91, 255, 0.1)' }}>
                  <Link size={36} color="#635BFF" />
                </div>
                <p className="woo-state-title">Connect your Stripe Account</p>
                <p className="woo-state-label">To view your payment history and receipts, please authorize Stripe Connect.</p>
                <button className="woo-load-btn" onClick={handleStripeConnectLogin} style={{ background: '#635BFF', padding: '1rem 2.5rem', fontSize: '1.1rem' }}>
                  <Link size={18} style={{ marginRight: 10 }} />
                  Connect with Stripe
                </button>
              </div>
            )}

            {/* Step 2: Spinner */}
            {stripeConnectData.loading && (
              <div className="woo-center-state glass-panel">
                <div className="woo-spinner-ring"></div>
                <p className="woo-state-label">Fetching Stripe transactions...</p>
              </div>
            )}

            {/* Error state */}
            {stripeConnectData.error && !stripeConnectData.loading && stripeConnectData.error !== "STRIPE_NOT_CONNECTED" && (
              <div className="woo-center-state glass-panel woo-error-state">
                <AlertCircle size={44} color="var(--danger)" />
                <p className="woo-state-title">Connection Failed</p>
                <p className="woo-state-label">{stripeConnectData.error}</p>
                <button className="woo-load-btn" onClick={handleStripeConnectLogin}>Re-authenticate</button>
              </div>
            )}

            {/* Step 3: Show Data only after successful login/fetch */}
            {stripeConnectData.isConnected && stripeConnectData.transactions && !stripeConnectData.loading && (
              <>
                <div className="woo-kpi-grid">
                  <div className="woo-kpi-card glass-panel">
                    <span className="woo-kpi-label">Total Transactions</span>
                    <span className="woo-kpi-value">{stripeConnectData.transactions.length}</span>
                    <span className="woo-kpi-sub">Total Payments</span>
                  </div>
                  <div className="woo-kpi-card glass-panel">
                    <span className="woo-kpi-label">Status</span>
                    <span className="woo-kpi-value" style={{ color: 'var(--success)' }}>Connected</span>
                    <span className="woo-kpi-sub">Stripe Connect</span>
                  </div>
                </div>

                <div className="table-container glass-panel" style={{ marginTop: '2rem' }}>
                  <div className="table-header-flex">
                    <h3 className="chart-title">
                      <DollarSign size={16} style={{ display: 'inline', marginRight: 6 }} />
                      Payment History
                    </h3>
                    <button className="refresh-btn" onClick={fetchStripeConnect}>Refresh</button>
                  </div>
                  <table className="dashboard-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Customer</th>
                        <th>Amount</th>
                        <th>Currency</th>
                        <th>Status</th>
                        <th>Receipt</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stripeConnectData.transactions.map((tx) => (
                        <tr key={tx.id} className="woo-table-row">
                          <td className="font-bold">{tx.id}</td>
                          <td>{tx.customer_name || 'Unknown'}</td>
                          <td className="woo-price-cell">{formatCurrency(tx.amount)}</td>
                          <td><span className="woo-type-pill">{tx.currency.toUpperCase()}</span></td>
                          <td>
                            <span className={`woo-order-status ${tx.status === 'succeeded' ? 'woo-status-completed' : 'woo-status-pending'}`}>
                              {tx.status}
                            </span>
                          </td>
                          <td>
                            {tx.receipt ? (
                              <a href={tx.receipt} target="_blank" rel="noreferrer" style={{ color: '#635BFF', textDecoration: 'none', fontWeight: 500 }}>
                                View Receipt
                              </a>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>No Receipt</span>
                            )}
                          </td>
                        </tr>
                      ))}
                      {stripeConnectData.transactions.length === 0 && (
                        <tr>
                          <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                            No transactions found for this account. Create test transactions in your Stripe Dashboard.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}



        {/* [COMMENTED OUT — campaign comparison modal for Meta ads incrementality analysis] */}
        {/* {comparisonModal.open && (
          <div className="modal-overlay" onClick={() => setComparisonModal({ open: false, data: null })}>
            <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
              ... modal with before/during/after filters and BarChart ...
            </div>
          </div>
        )} */}
      </main>
    </div>
  );
}

export default App;