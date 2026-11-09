import { useState } from 'react';
import api, { setAuthHeader } from '../api/api';
import { useTranslation } from 'react-i18next';

export default function Login({ onLogin, onSwitchToRegister }) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const extractErrorMessage = (err) => {
    const data = err?.response?.data;
    if (!data) return err?.message || t('auth.loginFailed');
    if (typeof data === 'string') return data;
    if (data?.detail) return data.detail;
    // FastAPI 422 often returns: { detail: [ { loc, msg, type }, ... ] }
    if (Array.isArray(data?.detail)) {
      return data.detail.map((e) => e?.msg || e?.type || t('auth.invalidValue')).join(', ');
    }
    try {
      return JSON.stringify(data);
    } catch {
      return t('auth.loginFailed');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { email, password });
      const raw = data?.access_token;
      const token = raw != null ? String(raw).trim() : null;
      if (!token) {
        setError(t('auth.invalidLoginResponse'));
        return;
      }
      try {
        localStorage.setItem('token', token);
        localStorage.setItem('access_token', token);
      } catch {
        // Continue with axios in-memory auth header when browser storage is unavailable.
      }
      setAuthHeader(token);
      onLogin();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-soft px-4">
      <div className="w-full max-w-md rounded-card border border-border bg-white p-8 shadow-card">
        <h1 className="mb-6 text-center text-2xl font-semibold text-text-primary">
          {t('auth.adminLogin')}
        </h1>
        {error && (
          <div className="mb-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-primary">
              {t('auth.email')}
            </label>
            <input
              type="email"
              className="w-full rounded-md border border-border px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-text-primary">
              {t('auth.password')}
            </label>
            <input
              type="password"
              className="w-full rounded-md border border-border px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-black hover:bg-blue-500 disabled:opacity-60"
          >
            {loading ? t('auth.signingIn') : t('auth.signIn')}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-text-secondary">
          {t('auth.noAccount')}{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="font-medium text-primary hover:underline"
          >
            {t('auth.register')}
          </button>
        </p>
      </div>
    </div>
  );
}
