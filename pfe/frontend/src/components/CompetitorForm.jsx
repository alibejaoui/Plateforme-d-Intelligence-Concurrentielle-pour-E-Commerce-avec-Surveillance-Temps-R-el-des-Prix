import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function CompetitorForm({ onSubmit, loading }) {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [rateLimitPerMinute, setRateLimitPerMinute] = useState(10);
  const [description, setDescription] = useState('');
  const [scrapingConfig, setScrapingConfig] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      name,
      website_url: websiteUrl,
      base_url: baseUrl,
      is_active: Boolean(isActive),
      rate_limit_per_minute: Number(rateLimitPerMinute),
      description: description || null,
      scraping_config: scrapingConfig || null,
    });
    setName('');
    setWebsiteUrl('');
    setBaseUrl('');
    setIsActive(true);
    setRateLimitPerMinute(10);
    setDescription('');
    setScrapingConfig('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-card border border-border bg-white p-4 shadow-card"
    >
      <h2 className="text-sm font-semibold text-text-primary">{t('competitors.newCompetitor')}</h2>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('competitors.name')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('competitors.websiteUrl')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('competitors.baseUrl')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('competitors.descriptionOptional')}</label>
        <textarea
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
        />
      </div>
      <div className="flex items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-xs font-medium text-text-secondary">
          <input
            type="checkbox"
            className="h-3 w-3 rounded border border-border"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          {t('competitors.active')}
        </label>
        <div className="flex flex-1 items-center justify-end gap-2">
          <label className="text-xs font-medium text-text-secondary">
            {t('competitors.rateLimit')}
          </label>
          <input
            type="number"
            min={1}
            className="w-20 rounded-md border border-border px-2 py-1 text-xs"
            value={rateLimitPerMinute}
            onChange={(e) => setRateLimitPerMinute(e.target.value)}
            required
          />
        </div>
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">
          {t('competitors.scrapingConfig')}
        </label>
        <textarea
          className="w-full rounded-md border border-border px-3 py-2 text-xs"
          value={scrapingConfig}
          onChange={(e) => setScrapingConfig(e.target.value)}
          rows={2}
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="rounded-md bg-primary px-3 py-2 text-xs font-semibold text-black hover:bg-blue-500 disabled:opacity-60"
      >
        {loading ? t('competitors.saving') : t('competitors.createCompetitor')}
      </button>
    </form>
  );
}

