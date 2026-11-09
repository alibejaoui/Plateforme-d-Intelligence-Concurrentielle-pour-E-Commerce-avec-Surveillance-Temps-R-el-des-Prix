import { Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

export default function ScrapingJobsTable({ jobs = [] }) {
  const { t } = useTranslation();
  return (
    <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('admin.jobsTable.id')}</TableCell>
            <TableCell>{t('admin.jobsTable.status')}</TableCell>
            <TableCell>{t('admin.jobsTable.jobType')}</TableCell>
            <TableCell>{t('admin.jobsTable.error')}</TableCell>
            <TableCell>{t('admin.jobsTable.created')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {jobs.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5}>
                <Typography variant="body2" color="text.secondary">
                  {t('admin.jobsTable.noData')}
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            jobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell>{job.id}</TableCell>
                <TableCell>{job.status || '-'}</TableCell>
                <TableCell>{job.job_type || '-'}</TableCell>
                <TableCell>{job.error_message || '-'}</TableCell>
                <TableCell>{job.created_at ? new Date(job.created_at).toLocaleString() : '-'}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
