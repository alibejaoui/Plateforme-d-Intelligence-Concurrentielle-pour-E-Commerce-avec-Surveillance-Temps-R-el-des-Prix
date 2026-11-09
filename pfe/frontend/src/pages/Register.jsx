import { useState } from 'react';
import api from '../api/api';
import { useTranslation } from 'react-i18next';

export default function Register({ onSwitchToLogin }) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const extractErrorMessage = (err) => {
    const data = err?.response?.data;
    if (!data) return err?.message || t('auth.registrationFailed');
    if (typeof data === 'string') return data;
    if (data?.detail) return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((e) => e?.msg || e?.type || t('auth.invalidValue')).join(', ');
    }
    try {
      return JSON.stringify(data);
    } catch {
      return t('auth.registrationFailed');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post('/auth/register', { email, password });
      onSwitchToLogin();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F5F7FA] px-4">
      <div className="w-full max-w-md rounded-xl border border-[#E5E7EB] bg-white p-8 shadow-lg">
        <h1 className="mb-6 text-center text-2xl font-semibold text-[#1F2937]">
          {t('auth.createAccount')}
        </h1>
        {error && (
          <div className="mb-4 rounded-md border border-[#F97316]/40 bg-[#F97316]/10 px-3 py-2 text-sm text-[#F97316]">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1F2937]">
              {t('auth.email')}
            </label>
            <input
              type="email"
              className="w-full rounded-md border border-[#E5E7EB] px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[#1F2937]">
              {t('auth.password')}
            </label>
            <input
              type="password"
              className="w-full rounded-md border border-[#E5E7EB] px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center rounded-md bg-[#3B82F6] px-3 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
          >
            {loading ? t('auth.creatingAccount') : t('auth.register')}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-[#6B7280]">
          {t('auth.alreadyHaveAccount')}{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-medium text-[#3B82F6] hover:underline"
          >
            {t('auth.signIn')}
          </button>
        </p>
      </div>
    </div>
  );
}
