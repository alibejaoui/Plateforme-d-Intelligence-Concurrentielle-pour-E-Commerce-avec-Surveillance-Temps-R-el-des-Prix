import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './translations/en.json';
import fr from './translations/fr.json';
import ar from './translations/ar.json';

const STORAGE_KEY = 'app_language';
const readSavedLanguage = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) || 'en';
  } catch {
    return 'en';
  }
};

const savedLanguage = readSavedLanguage();

const applyDocumentDirection = (lng) => {
  const direction = lng === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.setAttribute('lang', lng);
  document.documentElement.setAttribute('dir', direction);
};

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    fr: { translation: fr },
    ar: { translation: ar },
  },
  lng: savedLanguage,
  supportedLngs: ['en', 'fr', 'ar'],
  nonExplicitSupportedLngs: true,
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
  returnNull: false,
  parseMissingKeyHandler: (key) => key,
});

applyDocumentDirection(savedLanguage);

i18n.on('languageChanged', (lng) => {
  try {
    localStorage.setItem(STORAGE_KEY, lng);
  } catch {
    // Storage can be unavailable in privacy/file contexts; language still changes in memory.
  }
  applyDocumentDirection(lng);
});

export default i18n;
