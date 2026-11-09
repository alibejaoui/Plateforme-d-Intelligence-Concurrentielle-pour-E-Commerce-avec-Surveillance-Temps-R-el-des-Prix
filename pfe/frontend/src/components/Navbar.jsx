import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LogoutOutlined from '@mui/icons-material/LogoutOutlined';
import LanguageSwitcher from './LanguageSwitcher';

function shortDisplayName(currentUser, fallback) {
  if (currentUser?.full_name?.trim()) return currentUser.full_name.trim();
  const email = currentUser?.email?.trim();
  if (email && email.includes('@')) return email.slice(0, email.indexOf('@'));
  return email || fallback;
}

export default function Navbar({ onLogout, currentUser, showNav = true, showAuthControls = true }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const items = [
    { key: '/', label: t('navbar.dashboard') },
    { key: '/products', label: t('navbar.products') },
    { key: '/competitors', label: t('navbar.competitors') },
    { key: '/intelligence', label: t('navbar.intelligence') },
    { key: '/competitor-catalog', label: t('navbar.catalog') },
    { key: '/comparison-matrix', label: t('navbar.matrix') },
  ];

  const isAdminRoute = location.pathname.startsWith('/admin');
  const headerTitle = isAdminRoute ? t('admin.title') : t('navbar.title');
  const roleKey = currentUser?.role === 'admin' ? 'common.admin' : 'common.analyst';
  const userLabel = currentUser
    ? `${shortDisplayName(currentUser, t('common.admin'))} · ${t(roleKey)}`
    : '';

  return (
    <header className="sticky top-0 z-40 flex min-h-14 flex-wrap items-center justify-between gap-x-3 gap-y-2 border-b border-border bg-white px-4 py-2 shadow-card sm:px-6 sm:py-0">
      <div className="min-w-0 shrink text-base font-semibold text-text-primary sm:text-lg">{headerTitle}</div>
      <nav className="flex shrink-0 flex-wrap items-center justify-end gap-2 text-sm text-text-secondary sm:gap-3">
        {showNav && (
          <div className="hidden items-center gap-2 md:flex">
            {items.map((item) => (
              <button
                key={item.key}
                onClick={() => navigate(item.key)}
                className={`rounded-full px-3 py-1 transition-colors ${
                  location.pathname === item.key ? 'bg-primary-soft/50 text-text-primary' : 'hover:bg-bg-soft'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        )}
        <LanguageSwitcher />
        {showAuthControls && currentUser && (
          <>
            <span className="hidden max-w-[220px] truncate text-xs font-medium text-text-primary sm:block">
              {userLabel}
            </span>
            <span className="text-xs font-medium text-text-primary sm:hidden">{t(roleKey)}</span>
            <button
              type="button"
              onClick={onLogout}
              className={`${
                isAdminRoute
                  ? 'inline-flex items-center justify-center rounded-full p-1.5 sm:p-2'
                  : 'rounded-full border border-border px-3 py-1 text-xs font-medium'
              } text-text-primary transition-colors hover:bg-bg-soft`}
              title={t('common.logout')}
              aria-label={t('common.logout')}
            >
              {isAdminRoute ? <LogoutOutlined sx={{ fontSize: 22 }} /> : t('common.logout')}
            </button>
          </>
        )}
      </nav>
    </header>
  );
}
