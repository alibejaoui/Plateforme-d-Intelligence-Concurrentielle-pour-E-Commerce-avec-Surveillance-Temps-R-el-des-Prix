import { useEffect, useMemo, useState } from 'react';
import api from '../api/api';

function downloadBlob(content, filename, mimeType = 'text/csv;charset=utf-8;') {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export default function ComparisonMatrix() {
  const [competitors, setCompetitors] = useState([]);
  const [selectedCompetitors, setSelectedCompetitors] = useState([]);
  const [category, setCategory] = useState('');
  const [brand, setBrand] = useState('');
  const [search, setSearch] = useState('');
  const [minConfidence, setMinConfidence] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState({ total: 0, competitors: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const skip = (page - 1) * pageSize;

  useEffect(() => {
    api
      .get('/competitors')
      .then(({ data }) => {
        const items = data?.items || [];
        setCompetitors(items);
        setSelectedCompetitors(items.slice(0, 4).map((c) => c.id));
      })
      .catch(() => {
        setCompetitors([]);
        setSelectedCompetitors([]);
        setError('Could not load competitors');
      });
  }, []);

  const buildParams = () => {
    const p = new URLSearchParams();
    if (selectedCompetitors.length) p.set('competitor_ids', selectedCompetitors.join(','));
    if (category.trim()) p.set('category', category.trim());
    if (brand.trim()) p.set('brand', brand.trim());
    if (search.trim()) p.set('search', search.trim());
    if (minConfidence !== '') p.set('min_confidence', String(minConfidence));
    p.set('skip', String(skip));
    p.set('limit', String(pageSize));
    p.set('sort_by', sortBy);
    p.set('sort_dir', sortDir);
    return p.toString();
  };

  const loadMatrix = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get(`/matrix?${buildParams()}`);
      setRows(data.items || []);
      setMeta({ total: data.total || 0, competitors: data.competitors || [] });
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load matrix');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!selectedCompetitors.length) return;
    loadMatrix();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompetitors, page, pageSize, sortBy, sortDir]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil((meta.total || 0) / pageSize)), [meta.total, pageSize]);

  const toggleCompetitor = (id) => {
    setPage(1);
    setSelectedCompetitors((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      return [...prev, id];
    });
  };

  const applyFilters = () => {
    setPage(1);
    loadMatrix();
  };

  const exportCsv = async () => {
    try {
      const params = new URLSearchParams(buildParams());
      params.delete('skip');
      params.delete('limit');
      const { data } = await api.get(`/matrix/export?${params.toString()}`, { responseType: 'text' });
      downloadBlob(data, `comparison-matrix-${new Date().toISOString().slice(0, 10)}.csv`);
    } catch (e) {
      setError('CSV export failed');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-text-primary">Comparison Matrix</h1>
        <button className="rounded-md border border-border bg-white px-3 py-2 text-sm hover:bg-bg-soft" onClick={exportCsv}>
          Export CSV
        </button>
      </div>

      {error && <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">{error}</div>}

      <div className="rounded-card border border-border bg-white p-4 shadow-card space-y-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-text-secondary mb-2">Competitors</div>
          <div className="flex flex-wrap gap-2">
            {competitors.map((c) => (
              <button
                key={c.id}
                onClick={() => toggleCompetitor(c.id)}
                className={`rounded-full px-3 py-1 text-xs border ${selectedCompetitors.includes(c.id) ? 'bg-primary-soft border-primary text-text-primary' : 'border-border text-text-secondary hover:bg-bg-soft'}`}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>
        <div className="grid gap-2 md:grid-cols-6">
          <input className="rounded-md border border-border px-2 py-1 text-sm" placeholder="Search product/SKU" value={search} onChange={(e) => setSearch(e.target.value)} />
          <input className="rounded-md border border-border px-2 py-1 text-sm" placeholder="Category" value={category} onChange={(e) => setCategory(e.target.value)} />
          <input className="rounded-md border border-border px-2 py-1 text-sm" placeholder="Brand" value={brand} onChange={(e) => setBrand(e.target.value)} />
          <input className="rounded-md border border-border px-2 py-1 text-sm" type="number" step="0.01" min="0" max="1" placeholder="Min confidence" value={minConfidence} onChange={(e) => setMinConfidence(e.target.value)} />
          <select className="rounded-md border border-border px-2 py-1 text-sm" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="name">Sort: Name</option>
            <option value="price">Sort: Our price</option>
            <option value="coverage">Sort: Coverage</option>
          </select>
          <div className="flex gap-2">
            <select className="rounded-md border border-border px-2 py-1 text-sm" value={sortDir} onChange={(e) => setSortDir(e.target.value)}>
              <option value="asc">Asc</option>
              <option value="desc">Desc</option>
            </select>
            <button className="rounded-md bg-primary px-3 py-1 text-sm font-medium text-white" onClick={applyFilters}>
              Apply
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-card border border-border bg-white shadow-card overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-bg-soft sticky top-0 z-10">
            <tr>
              <th className="px-3 py-2 text-left">Product</th>
              <th className="px-3 py-2 text-left">Brand</th>
              <th className="px-3 py-2 text-left">Category</th>
              <th className="px-3 py-2 text-left">Our price</th>
              <th className="px-3 py-2 text-left">Coverage</th>
              {meta.competitors.map((c) => (
                <th key={c.id} className="px-3 py-2 text-left min-w-[180px]">{c.name}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading ? (
              <tr><td colSpan={5 + meta.competitors.length} className="px-4 py-6 text-center text-text-secondary">Loading matrix...</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={5 + meta.competitors.length} className="px-4 py-6 text-center text-text-secondary">No rows</td></tr>
            ) : rows.map((r) => (
              <tr key={r.internal_product_id}>
                <td className="px-3 py-2">{r.internal_name}</td>
                <td className="px-3 py-2 text-text-secondary">{r.brand || '-'}</td>
                <td className="px-3 py-2 text-text-secondary">{r.category || '-'}</td>
                <td className="px-3 py-2">{r.our_price ?? '-'}</td>
                <td className="px-3 py-2 text-xs text-text-secondary">{r.matched_competitors}/{meta.competitors.length}</td>
                {meta.competitors.map((c) => {
                  const cell = r.cells?.[c.id];
                  if (!cell) return <td key={c.id} className="px-3 py-2 text-warning text-xs">Missing</td>;
                  const isCheapest = r.cheapest_competitor_price != null && cell.price === r.cheapest_competitor_price;
                  return (
                    <td key={c.id} className={`px-3 py-2 ${isCheapest ? 'bg-success/10' : ''}`}>
                      <div className="text-sm">{cell.price ?? '-'}</div>
                      <div className="text-[11px] text-text-secondary">{cell.availability || '-'}</div>
                      <div className="text-[11px] text-text-secondary">conf {Number(cell.confidence_score || 0).toFixed(2)}</div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-text-secondary">Total: {meta.total}</div>
        <div className="flex items-center gap-2">
          <button className="rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
          <span className="text-sm text-text-secondary">Page {page} / {totalPages}</span>
          <button className="rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
          <select className="rounded-md border border-border px-2 py-1 text-sm" value={pageSize} onChange={(e) => { setPage(1); setPageSize(Number(e.target.value)); }}>
            {[20, 50, 100].map((n) => <option key={n} value={n}>{n}/page</option>)}
          </select>
        </div>
      </div>
    </div>
  );
}

