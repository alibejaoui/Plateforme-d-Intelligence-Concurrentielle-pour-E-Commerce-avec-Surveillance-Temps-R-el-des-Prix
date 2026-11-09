import { Card, CardContent, Grid, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

function StatCard({ title, value }) {
  return (
    <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" sx={{ mt: 1 }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function AnalyticsCards({ stats }) {
  const { t } = useTranslation();
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={3}>
        <StatCard title={t('admin.stats.totalUsers')} value={stats.totalUsers} />
      </Grid>
      <Grid item xs={12} md={3}>
        <StatCard title={t('admin.stats.totalProducts')} value={stats.totalProducts} />
      </Grid>
      <Grid item xs={12} md={3}>
        <StatCard title={t('admin.stats.totalAlerts')} value={stats.totalAlerts} />
      </Grid>
      <Grid item xs={12} md={3}>
        <StatCard title={t('admin.stats.totalJobs')} value={stats.totalJobs} />
      </Grid>
    </Grid>
  );
}
