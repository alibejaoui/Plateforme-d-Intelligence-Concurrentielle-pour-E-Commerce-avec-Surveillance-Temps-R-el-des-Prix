import { useEffect, useMemo, useState } from 'react';
import { Alert, Snackbar } from '@mui/material';
import api from '../api/api';

const SOURCE_TYPES = [
  { key: 'sitemap', label: 'Sitemap XML' },
  { key: 'feed', label: 'Product feed (CSV/XML)' },
  { key: 'crawl', label: 'Category crawl (fallback)' },
];

export default function Intelligence({ currentUser }) {
  const [competitors, setCompetitors] = useState([]);
  const [loadingCompetitors, setLoadingCompetitors] = useState(true);
  const [selectedCompetitorId, setSelectedCompetitorId] = useState('');

  const [catalogSourceType, setCatalogSourceType] = useState('sitemap');
  const [catalogSourceUrl, setCatalogSourceUrl] = useState('');
  const [catalogUrlFilterRegex, setCatalogUrlFilterRegex] = useState('');
  const [catalogMaxItems, setCatalogMaxItems] = useState(5000);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  const [coverage, setCoverage] = useState(null);
  const [missing, setMissing] = useState({ items: [], total: 0, page: 1, page_size: 100 });
  const [missingLoading, setMissingLoading] = useState(false);
  const [priceGaps, setPriceGaps] = useState({ items: [], total: 0 });
  const [opportunities, setOpportunities] = useState({ items: [], total: 0 });
  const [aggressiveness, setAggressiveness] = useState({ items: [], total: 0 });
  const [riskProducts, setRiskProducts] = useState({ items: [], total: 0 });
  const [opportunityProducts, setOpportunityProducts] = useState({ items: [], total: 0 });
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [reviewQueue, setReviewQueue] = useState({ items: [], total: 0 });
  const [crawlMonitoring, setCrawlMonitoring] = useState({ items: [], total: 0 });
  const [ciAlerts, setCiAlerts] = useState({ items: [], total: 0 });

  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });
  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const competitorId = selectedCompetitorId ? Number(selectedCompetitorId) : null;

  const loadCompetitors = async () => {
    setLoadingCompetitors(true);
    try {
      const { data } = await api.get('/competitors');
      const items = data.items || [];
      setCompetitors(items);
      if (!selectedCompetitorId && items.length) setSelectedCompetitorId(String(items[0].id));
    } finally {
      setLoadingCompetitors(false);
    }
  };

  useEffect(() => {
    loadCompetitors().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runCatalogImport = async () => {
    setError(null);
    setLastResult(null);
    setBusy(true);
    try {
      const payload = {
        source: {
          source_type: catalogSourceType,
          source_url: catalogSourceUrl,
          name: 'Internal catalog source',
          config: {
            max_items: Number(catalogMaxItems) || 5000,
            url_filter_regex: catalogUrlFilterRegex || undefined,
          },
        },
      };
      const { data } = await api.post('/catalog/import', payload);
      setLastResult({ type: 'catalog_import', data });
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to import catalog');
    } finally {
      setBusy(false);
    }
  };

  const runCompetitorSync = async () => {
    if (!competitorId) return;
    setError(null);
    setLastResult(null);
    setBusy(true);
    try {
      const { data } = await api.post(`/competitors/${competitorId}/catalog/sync`, { seed_url: null });
      setLastResult({ type: 'competitor_sync', data });
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to sync competitor catalog');
    } finally {
      setBusy(false);
    }
  };

  const runMatching = async () => {
    if (!competitorId) return;
    setError(null);
    setLastResult(null);
    setBusy(true);
    try {
      const { data } = await api.post('/matching/run', { competitor_id: competitorId, min_confidence: 0.75 });
      setLastResult({ type: 'matching_run', data });
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to run matching');
    } finally {
      setBusy(false);
    }
  };

  const recomputeMissing = async () => {
    if (!competitorId) return;
    setError(null);
    setLastResult(null);
    setBusy(true);
    try {
      const { data } = await api.post(`/missing-products/recompute?competitor_id=${competitorId}`);
      setLastResult({ type: 'missing_recompute', data });
      await Promise.all([loadCoverage(), loadMissing()]);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to recompute missing products');
    } finally {
      setBusy(false);
    }
  };

  const loadCoverage = async () => {
    if (!competitorId) return;
    try {
      const { data } = await api.get(`/coverage?competitor_id=${competitorId}`);
      setCoverage(data);
    } catch {
      setCoverage(null);
    }
  };

  const loadMissing = async () => {
    if (!competitorId) return;
    setMissingLoading(true);
    try {
      const { data } = await api.get(`/missing-products?competitor_id=${competitorId}&skip=0&limit=100`);
      setMissing(data);
    } catch {
      setMissing({ items: [], total: 0, page: 1, page_size: 100 });
    } finally {
      setMissingLoading(false);
    }
  };

  const loadAnalytics = async () => {
    if (!competitorId) return;
    setAnalyticsLoading(true);
    try {
      const [gaps, opps, aggr, risks, strategicOpps] = await Promise.all([
        api.get(`/analytics/price-gaps?competitor_id=${competitorId}&limit=50`),
        api.get(`/analytics/opportunities?competitor_id=${competitorId}&limit=50`),
        api.get('/analytics/competitor-aggressiveness?limit=10'),
        api.get('/analytics/products-at-risk?days=30&limit=10'),
        api.get('/analytics/opportunity-products?days=30&limit=10'),
      ]);
      setPriceGaps(gaps.data);
      setOpportunities(opps.data);
      setAggressiveness(aggr.data);
      setRiskProducts(risks.data);
      setOpportunityProducts(strategicOpps.data);
    } catch {
      setPriceGaps({ items: [], total: 0 });
      setOpportunities({ items: [], total: 0 });
      setAggressiveness({ items: [], total: 0 });
      setRiskProducts({ items: [], total: 0 });
      setOpportunityProducts({ items: [], total: 0 });
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const loadOps = async () => {
    if (!competitorId) return;
    try {
      const [reviewRes, crawlRes, alertsRes] = await Promise.all([
        api.get(`/matches/review-queue?competitor_id=${competitorId}&skip=0&limit=10`),
        api.get('/monitoring/crawls?skip=0&limit=10'),
        api.get('/ci-alerts?skip=0&limit=10'),
      ]);
      setReviewQueue(reviewRes.data);
      setCrawlMonitoring(crawlRes.data);
      setCiAlerts(alertsRes.data);
    } catch {
      setReviewQueue({ items: [], total: 0 });
      setCrawlMonitoring({ items: [], total: 0 });
      setCiAlerts({ items: [], total: 0 });
    }
  };

  useEffect(() => {
    if (!competitorId) return;
    Promise.allSettled([loadCoverage(), loadMissing(), loadAnalytics(), loadOps()]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [competitorId]);

  const evaluateAlerts = async () => {
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post('/ci-alerts/evaluate');
      setLastResult({ type: 'alerts_evaluate', data });
      await loadOps();
      showToast('Alerts evaluated', 'success');
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to evaluate alerts');
      showToast(e?.response?.data?.detail || 'Alert evaluation failed', 'error');
    } finally {
      setBusy(false);
    }
  };

  const seedDemo = async () => {
    if (!currentUser?.role || currentUser.role !== 'admin') return;
    setBusy(true);
    setError(null);
    setLastResult(null);
    try {
      const { data } = await api.post('/admin/demo/seed', { reset: true });
      setLastResult({ type: 'demo_seed', data });
      await loadOps();
      showToast('Demo data seeded', 'success');
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Demo seed failed');
      showToast(e?.response?.data?.detail || 'Demo seed failed', 'error');
    } finally {
      setBusy(false);
    }
  };

  const reviewMatch = async (matchId, reviewStatus) => {
    try {
      await api.patch(`/matches/${matchId}/review`, { review_status: reviewStatus });
      await loadOps();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to review match');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold text-text-primary">Competitive Intelligence</h1>
        <p className="text-sm text-text-secondary">
          Import internal catalog, sync competitor catalogs, match products, and detect missing opportunities.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">1) Internal catalog import</h2>
          <div className="mt-3 grid gap-3">
            <div className="grid gap-2 md:grid-cols-3">
              <label className="text-xs font-medium text-text-secondary">Source type</label>
              <select
                className="md:col-span-2 rounded-md border border-border px-3 py-2 text-sm"
                value={catalogSourceType}
                onChange={(e) => setCatalogSourceType(e.target.value)}
              >
                {SOURCE_TYPES.map((o) => (
                  <option key={o.key} value={o.key}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              <label className="text-xs font-medium text-text-secondary">URL</label>
              <input
                className="md:col-span-2 rounded-md border border-border px-3 py-2 text-sm"
                value={catalogSourceUrl}
                onChange={(e) => setCatalogSourceUrl(e.target.value)}
                placeholder="https://shop.example.com/sitemap.xml"
              />
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              <label className="text-xs font-medium text-text-secondary">URL filter regex</label>
              <input
                className="md:col-span-2 rounded-md border border-border px-3 py-2 text-sm"
                value={catalogUrlFilterRegex}
                onChange={(e) => setCatalogUrlFilterRegex(e.target.value)}
                placeholder="Optional, e.g. /product/"
              />
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              <label className="text-xs font-medium text-text-secondary">Max items</label>
              <input
                type="number"
                className="md:col-span-2 rounded-md border border-border px-3 py-2 text-sm"
                value={catalogMaxItems}
                onChange={(e) => setCatalogMaxItems(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <button
                className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                onClick={runCatalogImport}
                disabled={busy || !catalogSourceUrl.trim()}
              >
                {busy ? 'Running...' : 'Run import'}
              </button>
            </div>
          </div>
        </section>

        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">2) Competitor catalog sync</h2>
          <div className="mt-3 grid gap-3">
            <div className="grid gap-2 md:grid-cols-3">
              <label className="text-xs font-medium text-text-secondary">Competitor</label>
              <select
                className="md:col-span-2 rounded-md border border-border px-3 py-2 text-sm"
                value={selectedCompetitorId}
                onChange={(e) => setSelectedCompetitorId(e.target.value)}
                disabled={loadingCompetitors}
              >
                {competitors.map((c) => (
                  <option key={c.id} value={String(c.id)}>
                    {c.name} (#{c.id})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-wrap justify-end gap-2">
              <button
                className="rounded-full border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-soft disabled:opacity-50"
                onClick={runCompetitorSync}
                disabled={busy || !competitorId}
              >
                Sync catalog
              </button>
              <button
                className="rounded-full border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-soft disabled:opacity-50"
                onClick={runMatching}
                disabled={busy || !competitorId}
              >
                Run matching
              </button>
              <button
                className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                onClick={recomputeMissing}
                disabled={busy || !competitorId}
              >
                Recompute missing
              </button>
              <button
                className="rounded-full border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-soft disabled:opacity-50"
                onClick={evaluateAlerts}
                disabled={busy}
              >
                Evaluate alerts
              </button>

              {currentUser?.role === 'admin' && (
                <button
                  className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                  onClick={seedDemo}
                  disabled={busy}
                  title="Seed deterministic demo data (admin only)"
                >
                  Seed demo
                </button>
              )}
            </div>
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-card border border-border bg-white p-4 shadow-card lg:col-span-1">
          <h2 className="text-sm font-semibold text-text-primary">Coverage</h2>
          {!coverage ? (
            <div className="mt-3 text-sm text-text-secondary">No data.</div>
          ) : (
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Internal products</span>
                <span className="font-medium text-text-primary">{coverage.internal_total}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Competitor products</span>
                <span className="font-medium text-text-primary">{coverage.competitor_total}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Matched internal</span>
                <span className="font-medium text-text-primary">{coverage.matched_internal}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Matched competitor</span>
                <span className="font-medium text-text-primary">{coverage.matched_competitor}</span>
              </div>
              <div className="mt-2 rounded-md bg-bg-soft px-3 py-2">
                <div className="text-xs font-medium text-text-secondary">Internal coverage</div>
                <div className="text-lg font-semibold text-text-primary">
                  {(Number(coverage.internal_coverage_pct) || 0).toFixed(1)}%
                </div>
              </div>
              <div className="rounded-md bg-bg-soft px-3 py-2">
                <div className="text-xs font-medium text-text-secondary">Competitor coverage</div>
                <div className="text-lg font-semibold text-text-primary">
                  {(Number(coverage.competitor_coverage_pct) || 0).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </section>

        <section className="rounded-card border border-border bg-white p-4 shadow-card lg:col-span-2">
          <h2 className="text-sm font-semibold text-text-primary">Missing products (competitor → internal)</h2>
          <div className="mt-3 overflow-hidden rounded-md border border-border">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="bg-bg-soft">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Title
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    SKU/GTIN
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Price
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Link
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {missingLoading ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-text-secondary">
                      Loading...
                    </td>
                  </tr>
                ) : (missing.items || []).length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-text-secondary">
                      No missing products detected.
                    </td>
                  </tr>
                ) : (
                  (missing.items || []).map((row) => (
                    <tr key={row.id}>
                      <td className="px-4 py-2 text-text-primary">{row.competitor_product?.title || '-'}</td>
                      <td className="px-4 py-2 text-text-secondary">
                        {row.competitor_product?.sku || '-'} / {row.competitor_product?.gtin || '-'}
                      </td>
                      <td className="px-4 py-2 text-text-secondary">
                        {row.competitor_product?.price != null
                          ? `${row.competitor_product.price} ${row.competitor_product?.currency || ''}`
                          : '-'}
                      </td>
                      <td className="px-4 py-2">
                        {row.competitor_product?.url ? (
                          <a
                            className="text-primary underline"
                            href={row.competitor_product.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            open
                          </a>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-2 text-xs text-text-secondary">
            Total: <span className="font-medium text-text-primary">{missing.total || 0}</span>
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-card border border-border bg-white p-4 shadow-card lg:col-span-2">
          <h2 className="text-sm font-semibold text-text-primary">Price gaps (matched products)</h2>
          <div className="mt-3 overflow-hidden rounded-md border border-border">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="bg-bg-soft">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Product
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Our / Their
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Δ%
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {analyticsLoading ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-center text-text-secondary">
                      Loading...
                    </td>
                  </tr>
                ) : (priceGaps.items || []).length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-center text-text-secondary">
                      No matched price gaps yet.
                    </td>
                  </tr>
                ) : (
                  (priceGaps.items || []).map((r) => (
                    <tr key={`${r.internal_product_id}-${r.competitor_product_id}`}>
                      <td className="px-4 py-2 text-text-primary">{r.internal_name}</td>
                      <td className="px-4 py-2 text-text-secondary">
                        {r.our_price} / {r.their_price}
                      </td>
                      <td className="px-4 py-2 text-text-secondary">
                        {r.delta_pct != null ? `${r.delta_pct.toFixed(1)}%` : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-card border border-border bg-white p-4 shadow-card lg:col-span-1">
          <h2 className="text-sm font-semibold text-text-primary">Aggressive competitors</h2>
          <div className="mt-3 space-y-2 text-sm">
            {analyticsLoading ? (
              <div className="text-text-secondary">Loading...</div>
            ) : (aggressiveness.items || []).length === 0 ? (
              <div className="text-text-secondary">No data.</div>
            ) : (
              aggressiveness.items.map((c) => (
                <div key={c.competitor_id} className="rounded-md bg-bg-soft px-3 py-2">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-text-primary">Competitor #{c.competitor_id}</div>
                    <div className="text-xs text-text-secondary">
                      score {Number(c.aggressiveness_score).toFixed(3)}
                    </div>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs text-text-secondary">
                    <span>undercut rate</span>
                    <span className="text-text-primary">{c.undercut_rate_pct.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-text-secondary">
                    <span>avg undercut</span>
                    <span className="text-text-primary">{c.avg_undercut_pct.toFixed(1)}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <section className="rounded-card border border-border bg-white p-4 shadow-card">
        <h2 className="text-sm font-semibold text-text-primary">Opportunities (missing products ranked)</h2>
        <div className="mt-3 overflow-hidden rounded-md border border-border">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-bg-soft">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  Title
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  Score
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  Price
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {analyticsLoading ? (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-text-secondary">
                    Loading...
                  </td>
                </tr>
              ) : (opportunities.items || []).length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-text-secondary">
                    No opportunities yet. Run missing recompute.
                  </td>
                </tr>
              ) : (
                opportunities.items.map((o) => (
                  <tr key={o.competitor_product_id}>
                    <td className="px-4 py-2 text-text-primary">
                      {o.url ? (
                        <a className="text-primary underline" href={o.url} target="_blank" rel="noreferrer">
                          {o.title}
                        </a>
                      ) : (
                        o.title
                      )}
                    </td>
                    <td className="px-4 py-2 text-text-secondary">{Number(o.opportunity_score).toFixed(3)}</td>
                    <td className="px-4 py-2 text-text-secondary">
                      {o.price != null ? `${o.price} ${o.currency || ''}` : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">Products at risk</h2>
          <div className="mt-3 space-y-2">
            {analyticsLoading ? (
              <div className="text-sm text-text-secondary">Loading...</div>
            ) : (riskProducts.items || []).length === 0 ? (
              <div className="text-sm text-text-secondary">No risk signals yet.</div>
            ) : (
              riskProducts.items.map((item) => (
                <div key={item.internal_product_id} className="rounded-md border border-border bg-bg-soft p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium text-text-primary">{item.name}</div>
                    <div className="text-xs text-warning">pressure {Number(item.competitor_pressure_score || 0).toFixed(3)}</div>
                  </div>
                  <div className="mt-1 text-xs text-text-secondary">
                    cheaper competitors {item.cheaper_competitors}/{item.competitor_count} - 30d {item.variation_30d_pct ?? '-'}%
                  </div>
                  <div className="mt-1 text-sm text-text-secondary">{item.strategic_recommendation}</div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">Strategic opportunities</h2>
          <div className="mt-3 space-y-2">
            {analyticsLoading ? (
              <div className="text-sm text-text-secondary">Loading...</div>
            ) : (opportunityProducts.items || []).length === 0 ? (
              <div className="text-sm text-text-secondary">No opportunity signals yet.</div>
            ) : (
              opportunityProducts.items.map((item) => (
                <div key={item.internal_product_id} className="rounded-md border border-border bg-bg-soft p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium text-text-primary">{item.name}</div>
                    <div className="text-xs text-success">score {Number(item.opportunity_score || 0).toFixed(3)}</div>
                  </div>
                  <div className="mt-1 text-xs text-text-secondary">
                    internal cheaper {item.internal_cheaper_count}/{item.matched_count} - unavailable {item.competitors_unavailable}
                  </div>
                  <div className="mt-1 text-sm text-text-secondary">{item.strategic_recommendation}</div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">Match review queue</h2>
          <div className="mt-3 space-y-2">
            {(reviewQueue.items || []).length === 0 ? (
              <div className="text-sm text-text-secondary">No pending reviews.</div>
            ) : (
              (reviewQueue.items || []).map((item) => (
                <div key={item.match_id} className="rounded-md border border-border bg-bg-soft p-3">
                  <div className="text-sm font-medium text-text-primary">{item.internal?.name}</div>
                  <div className="text-xs text-text-secondary">vs {item.competitor?.title}</div>
                  <div className="mt-1 text-xs text-text-secondary">
                    confidence {Number(item.confidence_score || 0).toFixed(2)} ({item.matching_method})
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button className="rounded-md border border-border px-2 py-1 text-xs hover:bg-white" onClick={() => reviewMatch(item.match_id, 'accepted')}>Accept</button>
                    <button className="rounded-md border border-border px-2 py-1 text-xs hover:bg-white" onClick={() => reviewMatch(item.match_id, 'rejected')}>Reject</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">Crawl monitoring</h2>
          <div className="mt-3 space-y-2">
            {(crawlMonitoring.items || []).length === 0 ? (
              <div className="text-sm text-text-secondary">No crawl sessions yet.</div>
            ) : (
              (crawlMonitoring.items || []).map((c) => (
                <div key={c.id} className="rounded-md border border-border bg-bg-soft p-3">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-text-primary">Session #{c.id}</div>
                    <div className="text-xs text-text-secondary">{c.status}</div>
                  </div>
                  <div className="mt-1 text-xs text-text-secondary">
                    competitor #{c.competitor_id} - errors {c.errors_count}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <section className="rounded-card border border-border bg-white p-4 shadow-card">
        <h2 className="text-sm font-semibold text-text-primary">Competitive alerts</h2>
        <div className="mt-3 space-y-2">
          {(ciAlerts.items || []).length === 0 ? (
            <div className="text-sm text-text-secondary">No competitive alerts generated yet.</div>
          ) : (
            (ciAlerts.items || []).map((a) => (
              <div key={a.id} className="rounded-md border border-border bg-bg-soft p-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-text-primary">{a.title}</div>
                  <div className="text-xs text-text-secondary">{a.status}</div>
                </div>
                <div className="mt-1 text-sm text-text-secondary">{a.message}</div>
                <div className="mt-1 text-xs text-text-secondary">{a.alert_type} - severity {a.severity}</div>
              </div>
            ))
          )}
        </div>
      </section>

      {lastResult && (
        <section className="rounded-card border border-border bg-white p-4 shadow-card">
          <h2 className="text-sm font-semibold text-text-primary">Last run</h2>
          <pre className="mt-3 overflow-auto rounded-md bg-bg-soft p-3 text-xs text-text-primary">
            {JSON.stringify(lastResult, null, 2)}
          </pre>
        </section>
      )}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
      >
        <Alert
          severity={toast.severity}
          variant="filled"
          sx={{ width: '100%' }}
          onClose={() => setToast((prev) => ({ ...prev, open: false }))}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </div>
  );
}

