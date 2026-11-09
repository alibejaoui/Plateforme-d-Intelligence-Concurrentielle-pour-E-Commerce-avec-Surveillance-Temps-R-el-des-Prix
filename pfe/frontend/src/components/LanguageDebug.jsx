import { useTranslation } from 'react-i18next';

export default function LanguageDebug() {
  const { i18n, t } = useTranslation();
  const current = (i18n.language || 'en').slice(0, 2).toUpperCase();

  return (
    <span
      className="hidden rounded-full border border-border bg-bg-soft px-2 py-0.5 text-[10px] font-semibold text-text-secondary sm:inline-flex"
      title={`${t('navbar.language')}: ${i18n.language}`}
    >
      {current}
    </span>
  );
}
