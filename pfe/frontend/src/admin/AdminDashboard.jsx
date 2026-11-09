import { useEffect, useMemo, useState } from 'react';
import { Outlet, useLocation, useOutletContext } from 'react-router-dom';
import {
  Alert,
  Box,
  CircularProgress,
  Snackbar,
  Typography,
} from '@mui/material';
import PersonOutlineOutlined from '@mui/icons-material/PersonOutlineOutlined';
import PublicOutlined from '@mui/icons-material/PublicOutlined';
import ViewListOutlined from '@mui/icons-material/ViewListOutlined';
import NotificationsNoneOutlined from '@mui/icons-material/NotificationsNoneOutlined';
import BarChartOutlined from '@mui/icons-material/BarChartOutlined';
import { useTranslation } from 'react-i18next';
import api from '../api/api';
import UsersTable from './components/UsersTable';
import ScrapingJobsTable from './components/ScrapingJobsTable';
import AlertsTable from './components/AlertsTable';
import AnalyticsCards from './components/AnalyticsCards';
import SourcesTable from './components/SourcesTable';
import AdminLayout from './components/AdminLayout';

export function AdminRouteUsers() {
  const { t } = useTranslation();
  const { users, handleCreateUser, handleDeleteUser } = useOutletContext();
  return (
    <>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600, color: '#111827' }}>
        {t('admin.users')}
      </Typography>
      <UsersTable users={users} onCreateUser={handleCreateUser} onDeleteUser={handleDeleteUser} />
    </>
  );
}

export function AdminRouteSources() {
  return <SourcesTable />;
}

export function AdminRouteJobs() {
  const { t } = useTranslation();
  const { jobs } = useOutletContext();
  return (
    <>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600, color: '#111827' }}>
        {t('admin.jobs')}
      </Typography>
      <ScrapingJobsTable jobs={jobs} />
    </>
  );
}

export function AdminRouteAlerts() {
  const { t } = useTranslation();
  const { alerts } = useOutletContext();
  return (
    <>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600, color: '#111827' }}>
        {t('admin.alerts')}
      </Typography>
      <AlertsTable alerts={alerts} />
    </>
  );
}

export function AdminRouteAnalytics() {
  const { t } = useTranslation();
  const { stats } = useOutletContext();
  return (
    <>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600, color: '#111827' }}>
        {t('admin.analytics')}
      </Typography>
      <AnalyticsCards stats={stats} />
    </>
  );
}

/** Sidebar + outlet for /admin/*. */
export default function AdminDashboard() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [users, setUsers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [analytics, setAnalytics] = useState({
    total_users: 0,
    total_products: 0,
    total_alerts: 0,
    total_jobs: 0,
  });
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const stats = useMemo(
    () => ({
      totalUsers: analytics.total_users,
      totalProducts: analytics.total_products,
      totalAlerts: analytics.total_alerts,
      totalJobs: analytics.total_jobs,
    }),
    [analytics]
  );

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const loadAdminData = async () => {
    setLoading(true);
    setError('');
    try {
      const [usersRes, jobsRes, alertsRes, analyticsRes] = await Promise.all([
        api.get('/admin/users'),
        api.get('/admin/scraping-jobs'),
        api.get('/admin/alerts'),
        api.get('/admin/analytics'),
      ]);

      const usersData = Array.isArray(usersRes.data) ? usersRes.data : (usersRes.data?.items || []);
      const jobsData = Array.isArray(jobsRes.data) ? jobsRes.data : (jobsRes.data?.items || []);
      const alertsData = Array.isArray(alertsRes.data) ? alertsRes.data : (alertsRes.data?.items || []);
      setUsers(usersData);
      setJobs(jobsData);
      setAlerts(alertsData);
      setAnalytics(analyticsRes.data || {});
    } catch (e) {
      setError(e?.response?.data?.detail || t('admin.failedLoad'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleCreateUser = async (payload) => {
    try {
      await api.post('/admin/users', payload);
      showToast(t('admin.toast.userCreated'));
      await loadAdminData();
    } catch (e) {
      showToast(e?.response?.data?.detail || t('admin.toast.createFailed'), 'error');
      throw e;
    }
  };

  const handleDeleteUser = async (id) => {
    try {
      await api.delete(`/admin/users/${id}`);
      showToast(t('admin.toast.userDeleted'));
      await loadAdminData();
    } catch (e) {
      showToast(e?.response?.data?.detail || t('admin.toast.deleteFailed'), 'error');
    }
  };

  const menuItems = [
    { path: '/admin/users', label: t('admin.users'), Icon: PersonOutlineOutlined },
    { path: '/admin/sources', label: t('admin.sources'), Icon: PublicOutlined },
    { path: '/admin/scraping-jobs', label: t('admin.jobs'), Icon: ViewListOutlined },
    { path: '/admin/alerts', label: t('admin.alerts'), Icon: NotificationsNoneOutlined },
    { path: '/admin/analytics', label: t('admin.analytics'), Icon: BarChartOutlined },
  ];

  const isPathActive = (to) =>
    pathname === to || pathname.startsWith(`${to}/`);

  const outletContext = {
    users,
    jobs,
    alerts,
    stats,
    handleCreateUser,
    handleDeleteUser,
  };

  const isSourcesRoute = pathname === '/admin/sources' || pathname.startsWith('/admin/sources/');

  let mainChild;
  if (isSourcesRoute) {
    mainChild = (
      <>
        {!loading && error ? (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : null}
        <Outlet context={outletContext} />
      </>
    );
  } else if (loading) {
    mainChild = (
      <Box sx={{ display: 'flex', justifyContent: 'center', pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  } else if (error) {
    mainChild = <Alert severity="error">{error}</Alert>;
  } else {
    mainChild = <Outlet context={outletContext} />;
  }

  return (
    <AdminLayout title={t('admin.title')} menuItems={menuItems} isPathActive={isPathActive}>
      {mainChild}
      
      <Snackbar
        open={toast.open}
        autoHideDuration={3000}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
        message={toast.message}
      />
    </AdminLayout>
  );
}
