import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function ProductForm({ onSubmit, loading }) {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sku, setSku] = useState('');
  const [category, setCategory] = useState('');
  const [brand, setBrand] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [targetPrice, setTargetPrice] = useState('');
  const [minPriceThreshold, setMinPriceThreshold] = useState('');
  const [maxPriceThreshold, setMaxPriceThreshold] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      name,
      description: description || null,
      sku: sku || null,
      category: category || null,
      brand: brand || null,
      image_url: imageUrl || null,
      target_price: targetPrice === '' ? null : Number(targetPrice),
      min_price_threshold: minPriceThreshold === '' ? null : Number(minPriceThreshold),
      max_price_threshold: maxPriceThreshold === '' ? null : Number(maxPriceThreshold),
    });
    setName('');
    setDescription('');
    setSku('');
    setCategory('');
    setBrand('');
    setImageUrl('');
    setTargetPrice('');
    setMinPriceThreshold('');
    setMaxPriceThreshold('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-card border border-border bg-white p-4 shadow-card"
    >
      <h2 className="text-sm font-semibold text-text-primary">{t('products.newProduct')}</h2>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('products.name')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">
          {t('products.descriptionOptional')}
        </label>
        <textarea
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('products.skuOptional')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={sku}
          onChange={(e) => setSku(e.target.value)}
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('products.categoryOptional')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">{t('products.brandOptional')}</label>
        <input
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={brand}
          onChange={(e) => setBrand(e.target.value)}
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-text-secondary">
          {t('products.imageUrlOptional')}
        </label>
        <input
          type="url"
          className="w-full rounded-md border border-border px-3 py-2 text-sm"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
        />
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <div className="space-y-1">
          <label className="block text-xs font-medium text-text-secondary">
            {t('products.targetPriceOptional')}
          </label>
          <input
            type="number"
            step="0.01"
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-medium text-text-secondary">
            {t('products.minPriceOptional')}
          </label>
          <input
            type="number"
            step="0.01"
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={minPriceThreshold}
            onChange={(e) => setMinPriceThreshold(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-medium text-text-secondary">
            {t('products.maxPriceOptional')}
          </label>
          <input
            type="number"
            step="0.01"
            className="w-full rounded-md border border-border px-3 py-2 text-sm"
            value={maxPriceThreshold}
            onChange={(e) => setMaxPriceThreshold(e.target.value)}
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={loading}
        className="rounded-md bg-primary px-3 py-2 text-xs font-semibold text-black hover:bg-blue-500 disabled:opacity-60"
      >
        {loading ? t('products.saving') : t('products.createProduct')}
      </button>
    </form>
  );
}

