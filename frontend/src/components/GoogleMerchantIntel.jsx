import { AlertCircle, ShieldCheck, ShoppingBag } from 'lucide-react';
import { useEffect, useState } from 'react';

const GoogleMerchantIntel = ({ baseUrl }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchBenchmarks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${baseUrl}/api/merchant/google/benchmarks`);
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to fetch Google Merchant benchmarks.");
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks();
  }, []);

  const formatCurrency = (value) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

  return (
    <div className="google-intel-panel glass-panel animate-fade-in" style={{ padding: '1.5rem' }}>
      <div className="panel-header" style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
            <ShieldCheck className="icon-blue" /> Google Merchant Intelligence
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Official market price benchmarks and competitiveness data from your Google Merchant Center account.
          </p>
        </div>
        <button 
          onClick={fetchBenchmarks}
          className="refresh-btn"
          disabled={loading}
        >
          {loading ? 'Syncing...' : 'Sync with GMC'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', borderRadius: '8px', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem' }}>
          <AlertCircle size={20} /> {error}
          <div style={{ fontSize: '0.8rem', marginLeft: 'auto' }}>Check .env (GMC_ID & JSON path)</div>
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
          <p style={{ color: 'var(--text-secondary)' }}>Connecting to Google Content API...</p>
        </div>
      )}

      {data && data.products && (
        <div className="results-area animate-slide-up">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
            <div className="kpi-card glass-panel" style={{ background: 'rgba(59, 130, 246, 0.05)' }}>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>TOTAL GMC PRODUCTS</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{data.products.length}</div>
            </div>
            <div className="kpi-card glass-panel" style={{ background: 'rgba(16, 185, 129, 0.05)' }}>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>TOP COMPETITIVE</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success)' }}>
                {data.products.filter(p => p.competitiveness === 'high').length}
              </div>
            </div>
            <div className="kpi-card glass-panel" style={{ background: 'rgba(245, 158, 11, 0.05)' }}>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>MARKET OUTLIERS</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--warning)' }}>
                {data.products.filter(p => p.competitiveness === 'low').length}
              </div>
            </div>
            <div className="kpi-card glass-panel" style={{ background: 'rgba(139, 92, 246, 0.05)' }}>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>API STATUS</span>
              <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#a78bfa', marginTop: '5px' }}>Connected (v2.1)</div>
            </div>
          </div>

          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Product Information</th>
                <th>Your Price</th>
                <th>Market Benchmark</th>
                <th>Position</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.products.map((res, i) => (
                <tr key={res.id || i}>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 600 }}>{res.title}</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>ID: {res.id}</span>
                    </div>
                  </td>
                  <td>{formatCurrency(res.price || 0)}</td>
                  <td>{res.market_benchmark ? formatCurrency(res.market_benchmark) : 'N/A'}</td>
                  <td>
                    {res.market_benchmark ? (
                      <span style={{ color: res.price < res.market_benchmark ? 'var(--success)' : 'var(--danger)' }}>
                        {res.price < res.market_benchmark ? 'Under Market' : 'Above Market'}
                      </span>
                    ) : '—'}
                  </td>
                  <td>
                    <span className={`pill ${res.competitiveness === 'high' ? 'badge-success' : res.competitiveness === 'medium' ? 'badge-warning' : 'badge-danger'}`}>
                      {res.competitiveness?.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !data && !error && (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
          <ShoppingBag size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
          <p>Click "Sync with GMC" to load global price intelligence.</p>
        </div>
      )}
    </div>
  );
};

export default GoogleMerchantIntel;
