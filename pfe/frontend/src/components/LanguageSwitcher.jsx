import { useTranslation } from 'react-i18next';

const SUPPORTED_LANGUAGES = ['fr', 'en', 'ar'];

export default function LanguageSwitcher({ compact = false }) {
  const { i18n, t } = useTranslation();
  const current = (i18n.language || 'en').slice(0, 2).toLowerCase();

  const setLanguage = (lang) => {
    if (lang !== current) i18n.changeLanguage(lang);
  };

  return (
    <div className="inline-flex shrink-0 items-center gap-2">
      {!compact ? (
        <span className="hidden text-xs font-semibold text-text-primary sm:inline">
          {t('navbar.language')}
        </span>
      ) : null}
      <div className="inline-flex items-center rounded-full border border-gray-300 bg-white p-0.5 shadow-sm">
        {SUPPORTED_LANGUAGES.map((lang) => {
          const active = current === lang;
          return (
            <button
              key={lang}
              type="button"
              onClick={() => setLanguage(lang)}
              aria-pressed={active}
              className={`rounded-full px-2 py-1 text-xs font-semibold transition-colors ${
                active
                  ? 'bg-primary text-black'
                  : 'text-text-secondary hover:bg-bg-soft hover:text-text-primary'
              }`}
            >
              {t(`navbar.lang${lang[0].toUpperCase()}${lang.slice(1)}`)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
