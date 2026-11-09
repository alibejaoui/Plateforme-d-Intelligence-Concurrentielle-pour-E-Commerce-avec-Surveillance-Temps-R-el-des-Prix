import { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import api from '../api/api';

const COLORS = ['#2563EB', '#16A34A', '#F97316', '#7C3AED', '#DC2626', '#0891B2'];

function normalizeSnapshots(data) {
  return (data?.historical_snapshots || []).map((row) => ({
    date: row.date,
    marketAverage: Number(row.market_average || 0),
    marketMin: Number(row.market_min || 0),
    marketMax: Number(row.market_max || 0),
    referencePrice: row.reference_price != null ? Number(row.reference_price) : null,
    referenceGap: row.reference_gap != null ? Number(row.reference_gap) : null,
  }));
}

function normalizeCompetitorSeries(data) {
  const byDate = new Map();
  (data?.historical_gap_evolution || []).forEach((series) => {
    (series.points || []).forEach((point) => {
      const date = point.date ? new Date(point.date).toLocaleDateString() : '';
      if (!date) return;
      if (!byDate.has(date)) byDate.set(date, { date });
      byDate.get(date)[series.competitor_name || `#${series.competitor_id}`] = point.price;
      byDate.get(date)[`${series.competitor_name || `#${series.competitor_id}`} gap`] = point.gap_pct;
    });
  });
  return Array.from(byDate.values());
}

export default function HistoricalMarketCharts({ productId }) {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!productId) return;
    setLoading(true);
    setError(null);
    api
      .get(`/analytics/comparison/${productId}?days=${days}`)
      .then(({ data: payload }) => setData(payload))
      .catch((e) => setError(e?.response?.data?.detail || 'Historical analytics unavailable'))
      .finally(() => setLoading(false));
  }, [productId, days]);

  const snapshots = useMemo(() => normalizeSnapshots(data), [data]);
  const competitorRows = useMemo(() => normalizeCompetitorSeries(data), [data]);
  const competitorNames = useMemo(
    () => (data?.historical_gap_evolution || []).map((s) => s.competitor_name || `#${s.competitor_id}`),
    [data]
  );

  if (!productId) {
    return null;
  }

  return (
    <section className="rounded-card border border-border bg-white p-4 shadow-card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">Historical competitive analytics</h2>
          <p className="text-xs text-text-secondary">Market average, competitor prices, volatility and gap evolution.</p>
        </div>
        <select
          className="rounded-md border border-border bg-white px-2 py-1 text-sm"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
        >
          <option value={7}>7 days</option>
          <option value={30}>30 days</option>
          <option value={90}>90 days</option>
        </select>
      </div>

      {loading ? (
        <div className="h-72 animate-pulse rounded-md bg-bg-soft" />
      ) : error ? (
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">{error}</div>
      ) : snapshots.length === 0 && competitorRows.length === 0 ? (
        <div className="rounded-md border border-border bg-bg-soft px-3 py-8 text-center text-sm text-text-secondary">
          No historical comparison data yet.
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={snapshots}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="marketAverage" name="Market average" stroke="#2563EB" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="referencePrice" name="Our reference" stroke="#16A34A" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="marketMin" name="Market min" stroke="#F97316" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={competitorRows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {competitorNames.slice(0, 6).map((name, idx) => (
                  <Line key={name} type="monotone" dataKey={name} stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="xl:col-span-2 grid gap-3 md:grid-cols-4">
            <div className="rounded-md bg-bg-soft p-3">
              <div className="text-xs text-text-secondary">Position</div>
              <div className="text-sm font-semibold text-text-primary">{data?.price_position || 'unknown'}</div>
            </div>
            <div className="rounded-md bg-bg-soft p-3">
              <div className="text-xs text-text-secondary">Volatility</div>
              <div className="text-sm font-semibold text-text-primary">{Number(data?.volatility_score || 0).toFixed(3)}</div>
            </div>
            <div className="rounded-md bg-bg-soft p-3">
              <div className="text-xs text-text-secondary">Trend</div>
              <div className="text-sm font-semibold text-text-primary">{data?.trend_direction || 'stable'}</div>
            </div>
            <div className="rounded-md bg-bg-soft p-3">
              <div className="text-xs text-text-secondary">Risk</div>
              <div className="text-sm font-semibold text-text-primary">
                {data?.gain_loss_estimation?.estimated_competitiveness_risk || 'unknown'}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
