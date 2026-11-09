import { useEffect, useMemo, useState, useCallback } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  IconButton,
  MenuItem,
  Paper,
  Radio,
  RadioGroup,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableFooter,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Pagination,
} from '@mui/material';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { useTranslation } from 'react-i18next';
import api from '../../api/api';

function isValidHttpUrl(value) {
  const s = String(value || '').trim();
  if (!s) return false;
  try {
    const u = new URL(s);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

function formatAxiosDetail(error, fallback) {
  const d = error?.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x?.msg || x?.message || JSON.stringify(x)).join(' ');
  return fallback;
}

/** Normalize API row (supports `type`/`status` or legacy `source_type`/`is_active`). */
function normalizeSourceRow(row) {
  if (!row || row.id == null) return null;
  const sourceType = String(row.type ?? row.source_type ?? 'web').toLowerCase();
  let active = row.is_active;
  if (typeof active !== 'boolean') {
    active = row.status === 'active';
  }
  return {
    id: row.id,
    name: row.name,
    url: row.url,
    source_type: sourceType,
    is_active: active,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

const TYPE_STYLES = {
  rss: { bgcolor: '#ede9fe', color: '#5b21b6' },
  api: { bgcolor: '#dbeafe', color: '#1d4ed8' },
  web: { bgcolor: '#fef3c7', color: '#b45309' },
};

export default function SourcesTable() {
  const { t } = useTranslation();
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [page, setPage] = useState(1);
  const rowsPerPage = 5;
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [sourceType, setSourceType] = useState('rss');
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [snack, setSnack] = useState({ open: false, message: '', severity: 'success' });

  const fetchSources = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    try {
      const { data } = await api.get('/sources/');
      const list = Array.isArray(data) ? data : data?.items || [];
      setSources(list.map(normalizeSourceRow).filter(Boolean));
    } catch (e) {
      setSources([]);
      setLoadError(formatAxiosDetail(e, t('admin.sourcesTable.fetchFailed')));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  useEffect(() => {
    const pc = Math.max(1, Math.ceil(sources.length / rowsPerPage) || 1);
    setPage((p) => Math.min(p, pc));
  }, [sources.length]);

  const pageCount = Math.max(1, Math.ceil(sources.length / rowsPerPage) || 1);
  const pageSafe = Math.min(page, pageCount);

  const pagedSources = useMemo(() => {
    const start = (pageSafe - 1) * rowsPerPage;
    return sources.slice(start, start + rowsPerPage);
  }, [sources, pageSafe]);

  const showingFrom = sources.length === 0 ? 0 : (pageSafe - 1) * rowsPerPage + 1;
  const showingTo = Math.min(pageSafe * rowsPerPage, sources.length);

  const resetFormFields = () => {
    setName('');
    setUrl('');
    setSourceType('rss');
    setIsActive(true);
    setSubmitError('');
    setFieldErrors({});
  };

  const handleCancel = () => {
    if (saving) return;
    setOpen(false);
    setEditing(null);
    resetFormFields();
  };

  const openCreate = () => {
    setEditing(null);
    resetFormFields();
    setOpen(true);
  };

  const openEdit = (row) => {
    setEditing(row);
    setName(row.name || '');
    setUrl(row.url || '');
    setSourceType((row.source_type || 'web').toLowerCase());
    setIsActive(Boolean(row.is_active));
    setSubmitError('');
    setFieldErrors({});
    setOpen(true);
  };

  const validateForm = () => {
    const errs = {};
    const trimmedName = String(name || '').trim();
    const trimmedUrl = String(url || '').trim();

    if (!trimmedName) errs.name = t('admin.sourcesTable.validation.nameRequired');
    if (!trimmedUrl) errs.url = t('admin.sourcesTable.validation.urlRequired');
    else if (!isValidHttpUrl(trimmedUrl)) errs.url = t('admin.sourcesTable.validation.urlInvalid');

    const st = String(sourceType || '').toLowerCase();
    if (!['rss', 'api', 'web'].includes(st)) errs.type = t('admin.sourcesTable.validation.typeRequired');

    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const submit = async () => {
    if (!validateForm()) return;
    setSaving(true);
    setSubmitError('');
    const trimmedName = String(name || '').trim();
    const trimmedUrl = String(url || '').trim();
    const body = {
      name: trimmedName,
      url: trimmedUrl,
      type: sourceType,
      status: isActive ? 'active' : 'inactive',
    };
    try {
      if (editing) {
        const { data } = await api.patch(`/sources/${editing.id}`, body, { timeout: 15000 });
        const normalized = normalizeSourceRow(data);
        if (normalized) {
          setSources((prev) => prev.map((row) => (row.id === editing.id ? normalized : row)));
        }
        setSnack({ open: true, message: t('admin.toast.sourceUpdated'), severity: 'success' });
      } else {
        const { data } = await api.post('/sources/', body, { timeout: 15000 });
        const normalized = normalizeSourceRow(data);
        if (normalized) {
          setSources((prev) => [normalized, ...prev]);
        }
        setSnack({ open: true, message: t('admin.toast.sourceCreated'), severity: 'success' });
        setPage(1);
      }
      setOpen(false);
      setEditing(null);
      resetFormFields();
      // Keep list fresh without blocking the modal closing UX.
      fetchSources();
    } catch (e) {
      setSubmitError(formatAxiosDetail(e, t('admin.toast.sourceSaveFailed')));
      setSnack({
        open: true,
        message: formatAxiosDetail(e, t('admin.toast.sourceSaveFailed')),
        severity: 'error',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    const ok = window.confirm(t('admin.sourcesTable.deleteConfirm'));
    if (!ok) return;
    try {
      await api.delete(`/sources/${row.id}`, { timeout: 15000 });
      setSources((prev) => prev.filter((x) => x.id !== row.id));
      setSnack({ open: true, message: t('admin.toast.sourceDeleted'), severity: 'success' });
      fetchSources();
    } catch (e) {
      setSnack({
        open: true,
        message: formatAxiosDetail(e, t('admin.toast.sourceDeleteFailed')),
        severity: 'error',
      });
    }
  };

  const typeLabel = (v) =>
    ({
      rss: t('admin.sourcesTable.typeRss'),
      api: t('admin.sourcesTable.typeApi'),
      web: t('admin.sourcesTable.typeWeb'),
    })[String(v || '').toLowerCase()] || v;

  const showBannerError = Boolean(!loading && loadError);

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 2,
          mb: 2,
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600, color: '#111827' }}>
          {t('admin.sources')}
        </Typography>
        <Button variant="contained" onClick={openCreate} sx={{ flexShrink: 0 }}>
          {t('admin.sourcesTable.addSource')}
        </Button>
      </Box>

      {showBannerError ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {loadError}
        </Alert>
      ) : null}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : !showBannerError ? (
        <TableContainer
          component={Paper}
          elevation={0}
          sx={{ border: '1px solid #e5e7eb', borderRadius: 2, boxShadow: '0 1px 3px rgba(0,0,0,.06)' }}
        >
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: '#fafafa' }}>
                <TableCell sx={{ fontWeight: 600 }}>{t('admin.sourcesTable.name')}</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>{t('admin.sourcesTable.url')}</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>{t('admin.sourcesTable.type')}</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>{t('admin.sourcesTable.status')}</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 100 }}>{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sources.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Typography variant="body2" color="text.secondary">
                      {t('admin.sourcesTable.emptyState')}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                pagedSources.map((row) => {
                  const tkey = String(row.source_type || '').toLowerCase();
                  const ts = TYPE_STYLES[tkey] || TYPE_STYLES.web;
                  return (
                    <TableRow key={row.id} hover>
                      <TableCell>{row.name}</TableCell>
                      <TableCell
                        sx={{ maxWidth: 360, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                        title={row.url}
                      >
                        {row.url}
                      </TableCell>
                      <TableCell>
                        <Chip label={typeLabel(row.source_type)} size="small" sx={{ fontWeight: 500, ...ts }} />
                      </TableCell>
                      <TableCell>
                        {row.is_active ? (
                          <Chip
                            label={t('admin.sourcesTable.statusActive')}
                            size="small"
                            sx={{ bgcolor: '#dcfce7', color: '#166534', fontWeight: 500 }}
                          />
                        ) : (
                          <Chip
                            label={t('admin.sourcesTable.statusInactive')}
                            size="small"
                            sx={{ bgcolor: '#f3f4f6', color: '#6b7280', fontWeight: 500 }}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <IconButton size="small" aria-label={t('admin.sourcesTable.edit')} onClick={() => openEdit(row)} color="primary">
                          <EditOutlinedIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" aria-label={t('common.delete')} color="error" onClick={() => handleDelete(row)}>
                          <DeleteOutlineIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
            {sources.length > 0 && (
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1, px: 0 }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('admin.sourcesTable.showing', { from: showingFrom, to: showingTo, total: sources.length })}
                      </Typography>
                      <Pagination
                        size="small"
                        count={pageCount}
                        page={pageSafe}
                        onChange={(_, v) => setPage(v)}
                        siblingCount={1}
                        boundaryCount={1}
                        color="primary"
                      />
                    </Box>
                  </TableCell>
                </TableRow>
              </TableFooter>
            )}
          </Table>
        </TableContainer>
      ) : null}

      <Dialog
        open={open}
        onClose={() => {
          if (saving) return;
          handleCancel();
        }}
        maxWidth="sm"
        fullWidth
        disableEscapeKeyDown={saving}
      >
        <DialogTitle>{editing ? t('admin.sourcesTable.dialogEditTitle') : t('admin.sourcesTable.dialogAddTitle')}</DialogTitle>
        <DialogContent
          sx={{ display: 'grid', gap: 2, pt: 1 }}
          component="form"
          id="admin-source-form"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          {submitError ? <Alert severity="error">{submitError}</Alert> : null}
          <TextField
            autoFocus
            label={t('admin.sourcesTable.name')}
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (fieldErrors.name) setFieldErrors((prev) => ({ ...prev, name: undefined }));
            }}
            required
            fullWidth
            error={Boolean(fieldErrors.name)}
            helperText={fieldErrors.name}
            placeholder={t('admin.sourcesTable.namePlaceholder')}
            inputProps={{ 'aria-required': true }}
          />
          <TextField
            label={t('admin.sourcesTable.url')}
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (fieldErrors.url) setFieldErrors((prev) => ({ ...prev, url: undefined }));
            }}
            required
            fullWidth
            error={Boolean(fieldErrors.url)}
            helperText={fieldErrors.url}
            placeholder={t('admin.sourcesTable.urlPlaceholder')}
            inputProps={{ 'aria-required': true }}
          />
          <TextField
            select
            label={t('admin.sourcesTable.type')}
            value={sourceType}
            required
            fullWidth
            error={Boolean(fieldErrors.type)}
            helperText={fieldErrors.type}
            onChange={(e) => {
              setSourceType(e.target.value);
              if (fieldErrors.type) setFieldErrors((prev) => ({ ...prev, type: undefined }));
            }}
          >
            <MenuItem value="rss">{t('admin.sourcesTable.typeRss')}</MenuItem>
            <MenuItem value="api">{t('admin.sourcesTable.typeApi')}</MenuItem>
            <MenuItem value="web">{t('admin.sourcesTable.typeWeb')}</MenuItem>
          </TextField>
          <FormControl component="fieldset" variant="standard" sx={{ m: 0 }}>
            <FormLabel component="legend" sx={{ typography: 'body2', color: 'text.primary', mb: 0.5 }} required>
              {t('admin.sourcesTable.status')}
            </FormLabel>
            <RadioGroup row name="source-status" value={isActive ? 'active' : 'inactive'} onChange={(e) => setIsActive(e.target.value === 'active')}>
              <FormControlLabel value="active" control={<Radio size="small" />} label={t('admin.sourcesTable.statusActive')} />
              <FormControlLabel value="inactive" control={<Radio size="small" />} label={t('admin.sourcesTable.statusInactive')} />
            </RadioGroup>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button type="button" variant="text" color="inherit" onClick={handleCancel} disabled={saving}>
            {t('common.cancel')}
          </Button>
          <Button type="button" onClick={submit} variant="contained" disabled={saving}>
            {saving ? t('admin.sourcesTable.saving') : t('admin.sourcesTable.save')}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snack.open} autoHideDuration={4000} onClose={() => setSnack((s) => ({ ...s, open: false }))} message={snack.message} />
    </>
  );
}
