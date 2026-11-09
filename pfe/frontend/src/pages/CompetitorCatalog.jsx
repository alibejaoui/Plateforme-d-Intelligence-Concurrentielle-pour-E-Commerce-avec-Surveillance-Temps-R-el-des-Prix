import { useEffect, useMemo, useState } from 'react';
import { Drawer } from '@mui/material';
import api from '../api/api';

function csvEscape(value) {
  const raw = value == null ? '' : String(value);
  return `"${raw.replace(/"/g, '""')}"`;
}

function exportRows(rows) {
  const header = ['id', 'competitor', 'title', 'brand', 'sku', 'category', 'price', 'availability', 'matching_status', 'confidence', 'url'];
  const body = rows.map((r) =>
    [
      r.id,
      r.competitor_name,
      r.title,
      r.brand,
      r.sku,
      r.category,
      r.price,
      r.availability,
      r.matching_status,
      r.confidence_score,
      r.url,
    ]
      .map(csvEscape)
      .join(',')
  );
  const blob = new Blob([[header.join(','), ...body].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `competitor-catalog-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export default function CompetitorCatalog() {
  const [competitors, setCompetitors] = useState([]);
  const [selectedCompetitor, setSelectedCompetitor] = useState('');
  const [filters, setFilters] = useState({
    search: '',
    category: '',
    availability: '',
    min_price: '',
    max_price: '',
    matched: '',
    sort_by: 'updated_at',
    sort_dir: 'desc',
  });
  const [rows, setRows] = useState([]);
  const [facets, setFacets] = useState({ categories: [], availability: [] });
  const [meta, setMeta] = useState({ total: 0, page: 1, page_size: 25 });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    api.get('/competitors').then(({ data }) => {
      const items = data?.items || [];
      setCompetitors(items);
      if (items.length) setSelectedCompetitor(String(items[0].id));
    }).catch(() => setCompetitors([]));
  }, []);

  const params = useMemo(() => {
    const p = new URLSearchParams();
    if (selectedCompetitor) p.set('competitor_id', selectedCompetitor);
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '') p.set(key, value);
    });
    if (filters.matched === 'matched') p.set('matched', 'true');
    if (filters.matched === 'unmatched') p.set('matched', 'false');
    if (filters.matched === '') p.delete('matched');
    p.set('skip', String((page - 1) * pageSize));
    p.set('limit', String(pageSize));
    return p.toString();
  }, [selectedCompetitor, filters, page, pageSize]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get(`/competitor-catalog/products?${params}`);
      setRows(data.items || []);
      setFacets(data.facets || { categories: [], availability: [] });
      setMeta({ total: data.total || 0, page: data.page || 1, page_size: data.page_size || pageSize });
    } catch (e) {
      setError(e?.response?.data?.detail || 'Could not load competitor catalog');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!selectedCompetitor) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const totalPages = Math.max(1, Math.ceil((meta.total || 0) / pageSize));
  const updateFilter = (key, value) => {
    setPage(1);
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Catalogue concurrent</h1>
          <p className="text-sm text-text-secondary">Explore detected competitor products, matches, prices, and coverage gaps.</p>
        </div>
        <button
          className="rounded-md border border-border bg-white px-3 py-2 text-sm hover:bg-bg-soft"
          onClick={() => exportRows(rows)}
          disabled={!rows.length}
        >
          Export CSV
        </button>
      </div>

      {error && <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">{error}</div>}

      <section className="rounded-card border border-border bg-white p-4 shadow-card">
        <div className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
          <select className="rounded-md border border-border px-2 py-2 text-sm" value={selectedCompetitor} onChange={(e) => { setPage(1); setSelectedCompetitor(e.target.value); }}>
            {competitors.map((c) => <option key={c.id} value={String(c.id)}>{c.name}</option>)}
          </select>
          <input className="rounded-md border border-border px-2 py-2 text-sm xl:col-span-2" placeholder="Search title, SKU, GTIN, brand" value={filters.search} onChange={(e) => updateFilter('search', e.target.value)} />
          <select className="rounded-md border border-border px-2 py-2 text-sm" value={filters.category} onChange={(e) => updateFilter('category', e.target.value)}>
            <option value="">All categories</option>
            {(facets.categories || []).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="rounded-md border border-border px-2 py-2 text-sm" value={filters.availability} onChange={(e) => updateFilter('availability', e.target.value)}>
            <option value="">All availability</option>
            {(facets.availability || []).map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <input type="number" className="rounded-md border border-border px-2 py-2 text-sm" placeholder="Min price" value={filters.min_price} onChange={(e) => updateFilter('min_price', e.target.value)} />
          <input type="number" className="rounded-md border border-border px-2 py-2 text-sm" placeholder="Max price" value={filters.max_price} onChange={(e) => updateFilter('max_price', e.target.value)} />
          <select className="rounded-md border border-border px-2 py-2 text-sm" value={filters.matched} onChange={(e) => updateFilter('matched', e.target.value)}>
            <option value="">All matches</option>
            <option value="matched">Matched</option>
            <option value="unmatched">Unmatched</option>
          </select>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <select className="rounded-md border border-border px-2 py-1 text-sm" value={filters.sort_by} onChange={(e) => updateFilter('sort_by', e.target.value)}>
            <option value="updated_at">Sort by last seen</option>
            <option value="title">Sort by title</option>
            <option value="price">Sort by price</option>
            <option value="category">Sort by category</option>
            <option value="confidence">Sort by confidence</option>
          </select>
          <select className="rounded-md border border-border px-2 py-1 text-sm" value={filters.sort_dir} onChange={(e) => updateFilter('sort_dir', e.target.value)}>
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
          <button className="rounded-md border border-border px-3 py-1 text-sm hover:bg-bg-soft" onClick={load}>Refresh</button>
        </div>
      </section>

      <section className="overflow-hidden rounded-card border border-border bg-white shadow-card">
        <table className="min-w-full divide-y divide-border text-sm">
          <thead className="bg-bg-soft">
            <tr>
              <th className="px-3 py-2 text-left">Product</th>
              <th className="px-3 py-2 text-left">Competitor</th>
              <th className="px-3 py-2 text-left">Price</th>
              <th className="px-3 py-2 text-left">Availability</th>
              <th className="px-3 py-2 text-left">Match</th>
              <th className="px-3 py-2 text-left">Last seen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-text-secondary">Loading catalog...</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-text-secondary">No competitor products found.</td></tr>
            ) : rows.map((row) => (
              <tr key={row.id} className="cursor-pointer hover:bg-bg-soft/60" onClick={() => setSelectedProduct(row)}>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 shrink-0 overflow-hidden rounded-md bg-bg-soft">
                      {row.image_url ? <img src={row.image_url} alt="" className="h-full w-full object-cover" /> : null}
                    </div>
                    <div className="min-w-0">
                      <div className="truncate font-medium text-text-primary">{row.title}</div>
                      <div className="text-xs text-text-secondary">{row.brand || '-'} · {row.sku || row.gtin || '-'}</div>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2 text-text-secondary">{row.competitor_name}</td>
                <td className="px-3 py-2">{row.price != null ? `${row.price} ${row.currency || ''}` : '-'}</td>
                <td className="px-3 py-2 text-text-secondary">{row.availability || '-'}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${row.matching_status === 'matched' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                    {row.matching_status}
                  </span>
                  {row.confidence_score != null && <div className="mt-1 text-xs text-text-secondary">conf {Number(row.confidence_score).toFixed(2)}</div>}
                </td>
                <td className="px-3 py-2 text-xs text-text-secondary">{row.last_seen ? new Date(row.last_seen).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm text-text-secondary">Total: {meta.total}</div>
        <div className="flex items-center gap-2">
          <button className="rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
          <span className="text-sm text-text-secondary">Page {page} / {totalPages}</span>
          <button className="rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
          <select className="rounded-md border border-border px-2 py-1 text-sm" value={pageSize} onChange={(e) => { setPage(1); setPageSize(Number(e.target.value)); }}>
            {[25, 50, 100].map((n) => <option key={n} value={n}>{n}/page</option>)}
          </select>
        </div>
      </div>

      <Drawer anchor="right" open={!!selectedProduct} onClose={() => setSelectedProduct(null)}>
        <div className="w-screen max-w-xl p-5">
          {!selectedProduct ? null : (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-text-primary">{selectedProduct.title}</h2>
                <p className="text-sm text-text-secondary">{selectedProduct.competitor_name}</p>
              </div>
              {selectedProduct.image_url && <img src={selectedProduct.image_url} alt="" className="h-52 w-full rounded-md object-cover" />}
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-md bg-bg-soft p-3"><div className="text-xs text-text-secondary">Price</div><div className="font-semibold">{selectedProduct.price ?? '-'} {selectedProduct.currency || ''}</div></div>
                <div className="rounded-md bg-bg-soft p-3"><div className="text-xs text-text-secondary">Availability</div><div className="font-semibold">{selectedProduct.availability || '-'}</div></div>
                <div className="rounded-md bg-bg-soft p-3"><div className="text-xs text-text-secondary">Category</div><div className="font-semibold">{selectedProduct.category || '-'}</div></div>
                <div className="rounded-md bg-bg-soft p-3"><div className="text-xs text-text-secondary">Match confidence</div><div className="font-semibold">{selectedProduct.confidence_score != null ? Number(selectedProduct.confidence_score).toFixed(3) : '-'}</div></div>
              </div>
              {selectedProduct.matched_internal_product && (
                <div className="rounded-md border border-border p-3">
                  <div className="text-xs font-medium uppercase tracking-wide text-text-secondary">Matched internal product</div>
                  <div className="mt-1 font-medium text-text-primary">{selectedProduct.matched_internal_product.name}</div>
                  <div className="text-sm text-text-secondary">SKU {selectedProduct.matched_internal_product.sku || '-'}</div>
                </div>
              )}
              <div className="flex flex-wrap gap-2">
                {selectedProduct.url && <a className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-white" href={selectedProduct.url} target="_blank" rel="noreferrer">Open competitor page</a>}
                {selectedProduct.matched_internal_product?.id && (
                  <a className="rounded-md border border-border px-3 py-2 text-sm hover:bg-bg-soft" href="/comparison-matrix">Open comparison matrix</a>
                )}
              </div>
            </div>
          )}
        </div>
      </Drawer>
    </div>
  );
}
