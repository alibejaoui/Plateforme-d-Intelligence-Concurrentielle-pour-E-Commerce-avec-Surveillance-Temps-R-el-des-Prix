import { useEffect, useState } from 'react';
import api from '../api/api';
import CompetitorForm from '../components/CompetitorForm';
import { useTranslation } from 'react-i18next';

export default function Competitors() {
  const { t } = useTranslation();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.get('/competitors');
      setItems(data.items || []);
    } catch (err) {
      setError(err?.response?.data?.detail || t('competitors.failedLoad'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      load();
    } else {
      setItems([]);
      setLoading(false);
    }
  }, []);

  const handleCreate = async (payload) => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError(t('competitors.notAuthenticated'));
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post('/competitors', payload);
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || t('competitors.failedCreate'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-text-primary">{t('competitors.title')}</h1>
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
                  {t('competitors.id')}
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  {t('competitors.name')}
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-text-secondary">
                  {t('competitors.website')}
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
                    {t('competitors.noData')}
                  </td>
                </tr>
              ) : (
                items.map((c) => (
                  <tr key={c.id}>
                    <td className="px-4 py-2 text-text-secondary">{c.id}</td>
                    <td className="px-4 py-2 text-text-primary">{c.name}</td>
                    <td className="px-4 py-2 text-text-secondary">
                      {c.website_url}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <CompetitorForm onSubmit={handleCreate} loading={saving} />
      </div>
    </div>
  );
}

