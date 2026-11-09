import { Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

export default function AlertsTable({ alerts = [] }) {
  const { t } = useTranslation();
  return (
    <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('admin.alertsTable.id')}</TableCell>
            <TableCell>{t('admin.alertsTable.user')}</TableCell>
            <TableCell>{t('admin.alertsTable.product')}</TableCell>
            <TableCell>{t('admin.alertsTable.price')}</TableCell>
            <TableCell>{t('admin.alertsTable.threshold')}</TableCell>
            <TableCell>{t('admin.alertsTable.type')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {alerts.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6}>
                <Typography variant="body2" color="text.secondary">
                  {t('admin.alertsTable.noData')}
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            alerts.map((alert) => (
              <TableRow key={alert.id}>
                <TableCell>{alert.id}</TableCell>
                <TableCell>{alert.user_email || alert.user_id || '-'}</TableCell>
                <TableCell>{alert.product_name || alert.product_id || '-'}</TableCell>
                <TableCell>{alert.new_price || alert.price || '-'}</TableCell>
                <TableCell>{alert.threshold || alert.old_price || '-'}</TableCell>
                <TableCell>{alert.alert_type || '-'}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
