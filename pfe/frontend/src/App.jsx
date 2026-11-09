import { useEffect, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import DashboardDynamic from './pages/DashboardDynamic';
import Products from './pages/Products';
import Competitors from './pages/Competitors';
import Intelligence from './pages/Intelligence';
import ComparisonMatrix from './pages/ComparisonMatrix';
import CompetitorCatalog from './pages/CompetitorCatalog';
import AdminDashboard, {
  AdminRouteUsers,
  AdminRouteSources,
  AdminRouteJobs,
  AdminRouteAlerts,
  AdminRouteAnalytics,
} from './admin/AdminDashboard';
import api from './api/api';

export default function App() {
  const { t } = useTranslation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authScreen, setAuthScreen] = useState('login');
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const resolveRole = async (user) => {
    if (user?.role) return user.role;
    try {
      await api.get('/admin/test', { timeout: 12000 });
      return 'admin';
    } catch {
      return 'analyst';
    }
  };

  useEffect(() => {
    let cancelled = false;
    let token = null;
    try {
      token = localStorage.getItem('access_token') || localStorage.getItem('token');
    } catch {
      token = null;
    }
    setIsAuthenticated(!!token);
    if (!token) {
      setCurrentUser(null);
      setAuthLoading(false);
      return undefined;
    }
    api
      .get('/auth/me')
      .then(async ({ data }) => {
        if (cancelled) return;
        const role = await resolveRole(data);
        if (!cancelled) setCurrentUser({ ...data, role });
      })
      .catch(() => {
        if (cancelled) return;
        try {
          localStorage.removeItem('token');
          localStorage.removeItem('access_token');
        } catch {
          // Storage may be unavailable; continue with in-memory auth reset.
        }
        setIsAuthenticated(false);
        setCurrentUser(null);
      })
      .finally(() => {
        if (!cancelled) setAuthLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
    setAuthLoading(true);
    api
      .get('/auth/me')
      .then(async ({ data }) => {
        const role = await resolveRole(data);
        setCurrentUser({ ...data, role });
        navigate(role === 'admin' ? '/admin/sources' : '/');
      })
      .catch(() => {
        try {
          localStorage.removeItem('token');
          localStorage.removeItem('access_token');
        } catch {
          // Storage may be unavailable; continue with in-memory auth reset.
        }
        setIsAuthenticated(false);
        setCurrentUser(null);
        navigate('/');
      })
      .finally(() => setAuthLoading(false));
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
    } catch {
      // Storage may be unavailable; continue with in-memory auth reset.
    }
    setIsAuthenticated(false);
    setCurrentUser(null);
    navigate('/');
  };

  useEffect(() => {
    if (!isAuthenticated || !currentUser) return;
    if (currentUser.role !== 'admin' && location.pathname.startsWith('/admin')) {
      navigate('/');
    }
  }, [isAuthenticated, currentUser, location.pathname, navigate]);

  if (authLoading) {
    return (
      <>
        <Navbar showNav={false} showAuthControls={false} />
        <div className="p-6 text-sm text-text-secondary">{t('common.loading')}</div>
      </>
    );
  }

  if (!isAuthenticated) {
    if (authScreen === 'register') {
      return (
        <>
          <Navbar showNav={false} showAuthControls={false} />
          <Register onSwitchToLogin={() => setAuthScreen('login')} />
        </>
      );
    }
    return (
      <>
        <Navbar showNav={false} showAuthControls={false} />
        <Login
          onLogin={handleLogin}
          onSwitchToRegister={() => setAuthScreen('register')}
        />
      </>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar
        onLogout={handleLogout}
        currentUser={currentUser}
        showNav={!location.pathname.startsWith('/admin')}
        showAuthControls
      />
      <main className={`flex-1 bg-bg-soft ${location.pathname.startsWith('/admin') ? '' : 'p-6'}`}>
        <Routes>
          <Route
            path="/admin"
            element={
              currentUser?.role === 'admin' ? (
                <AdminDashboard />
              ) : (
                <Navigate to="/" replace />
              )
            }
          >
            <Route index element={<Navigate to="sources" replace />} />
            <Route path="users" element={<AdminRouteUsers />} />
            <Route path="sources" element={<AdminRouteSources />} />
            <Route path="scraping-jobs" element={<AdminRouteJobs />} />
            <Route path="alerts" element={<AdminRouteAlerts />} />
            <Route path="analytics" element={<AdminRouteAnalytics />} />
            <Route path="*" element={<Navigate to="/admin/sources" replace />} />
          </Route>
          <Route path="/" element={<DashboardDynamic />} />
          <Route path="/products" element={<Products />} />
          <Route path="/competitors" element={<Competitors />} />
          <Route path="/intelligence" element={<Intelligence currentUser={currentUser} />} />
          <Route path="/comparison-matrix" element={<ComparisonMatrix />} />
          <Route path="/competitor-catalog" element={<CompetitorCatalog />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
