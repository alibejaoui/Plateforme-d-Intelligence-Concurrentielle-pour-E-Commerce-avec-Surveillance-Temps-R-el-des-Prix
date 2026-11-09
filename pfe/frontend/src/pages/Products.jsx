import { useEffect, useState } from 'react';
import api, { getToken } from '../api/api';
import ProductForm from '../components/ProductForm';
import { useTranslation } from 'react-i18next';

export default function Products() {
  const { t } = useTranslation();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.get('/products');
      setItems(data.items || []);
    } catch (err) {
      setError(err?.response?.data?.detail || t('products.failedLoad'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = getToken();
    if (token) {
      load();
    } else {
      setItems([]);
      setLoading(false);
    }
  }, []);

  const handleCreate = async (payload) => {
    const token = getToken();
    if (!token) {
      setError(t('products.notAuthenticated'));
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post('/products', payload);
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || t('products.failedCreate'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-text-primary">{t('products.title')}</h1>
      {error && (
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
          {error}
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="overflow-hidden rounded-card border border-border bg-white shadow-card">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-bg-soft">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  {t('products.id')}
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  {t('products.name')}
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  {t('products.sku')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td
                    colSpan={3}
                    className="px-4 py-6 text-center text-text-secondary"
                  >
                    {t('common.loadingEllipsis')}
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td
                    colSpan={3}
                    className="px-4 py-6 text-center text-text-secondary"
                  >
                    {t('products.noData')}
                  </td>
                </tr>
              ) : (
                items.map((p) => (
                  <tr key={p.id}>
                    <td className="px-4 py-2 text-text-secondary">{p.id}</td>
                    <td className="px-4 py-2 text-text-primary">{p.name}</td>
                    <td className="px-4 py-2 text-text-secondary">
                      {p.sku || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <ProductForm onSubmit={handleCreate} loading={saving} />
      </div>
    </div>
  );
}

