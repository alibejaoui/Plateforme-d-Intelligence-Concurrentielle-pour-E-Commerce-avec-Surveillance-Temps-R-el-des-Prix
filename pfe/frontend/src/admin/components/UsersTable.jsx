import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function UsersTable({ users = [], onCreateUser, onDeleteUser }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('analyst');
  const [fullName, setFullName] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    setSaving(true);
    try {
      await onCreateUser?.({
        email,
        password,
        role,
        full_name: fullName || null,
      });
      setOpen(false);
      setEmail('');
      setPassword('');
      setRole('analyst');
      setFullName('');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    const ok = window.confirm(t('admin.usersTable.deleteConfirm'));
    if (!ok) return;
    await onDeleteUser?.(id);
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" onClick={() => setOpen(true)}>
          {t('admin.usersTable.addUser')}
        </Button>
      </Box>

      <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('admin.usersTable.id')}</TableCell>
              <TableCell>{t('admin.usersTable.email')}</TableCell>
              <TableCell>{t('admin.usersTable.fullName')}</TableCell>
              <TableCell>{t('admin.usersTable.role')}</TableCell>
              <TableCell>{t('admin.usersTable.createdAt')}</TableCell>
              <TableCell>{t('admin.usersTable.active')}</TableCell>
              <TableCell>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>
                  <Typography variant="body2" color="text.secondary">
                    {t('admin.usersTable.noData')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell>{u.id}</TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>{u.full_name || '-'}</TableCell>
                  <TableCell>{u.role === 'admin' ? t('common.admin') : t('common.analyst')}</TableCell>
                  <TableCell>{u.created_at ? new Date(u.created_at).toLocaleString() : '-'}</TableCell>
                  <TableCell>{u.is_active ? t('common.yes') : t('common.no')}</TableCell>
                  <TableCell>
                    <Button color="error" size="small" onClick={() => handleDelete(u.id)}>
                      {t('common.delete')}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => !saving && setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('admin.usersTable.dialogTitle')}</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: 1 }}>
          <TextField label={t('admin.usersTable.email')} type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField label={t('auth.password')} type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <TextField label={t('admin.usersTable.fullNameOptional')} value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <TextField select label={t('admin.usersTable.roleLabel')} value={role} onChange={(e) => setRole(e.target.value)}>
            <MenuItem value="analyst">{t('common.analyst')}</MenuItem>
            <MenuItem value="admin">{t('common.admin')}</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={saving}>
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            onClick={submit}
            disabled={!email || !password || saving}
          >
            {saving ? t('admin.usersTable.creating') : t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
