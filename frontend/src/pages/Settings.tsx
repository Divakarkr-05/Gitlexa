import { useState } from 'react';
import { Activity, CheckCircle2, CircleAlert, RefreshCw, Server } from 'lucide-react';
import {
  API_BASE_URL,
  ApiError,
  fetchAuthStatus,
  fetchHealth,
  type AuthStatusResponse,
  type HealthResponse,
} from '../services/api';

export default function Settings() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [authStatus, setAuthStatus] = useState<AuthStatusResponse | null>(null);
  const [authError, setAuthError] = useState('');
  const [isCheckingAuth, setIsCheckingAuth] = useState(false);

  async function checkHealth() {
    setIsChecking(true);
    setError('');
    try {
      setHealth(await fetchHealth());
    } catch (requestError) {
      setHealth(null);
      setError(requestError instanceof ApiError
        ? requestError.message
        : 'The backend health check failed.');
    } finally {
      setIsChecking(false);
    }

  }

  async function checkAuthStatus() {
    setIsCheckingAuth(true);
    setAuthError('');
    try {
      setAuthStatus(await fetchAuthStatus());
    } catch (requestError) {
      setAuthStatus(null);
      setAuthError(requestError instanceof ApiError
        ? requestError.message
        : 'The GitHub token configuration check failed.');
    } finally {
      setIsCheckingAuth(false);
    }
  }

  return (
    <div className="page-shell inner-page">
      <div className="page-breadcrumb"><span>WORKSPACE</span><i>/</i><strong>SETTINGS</strong></div>
      <section className="inner-page-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" /> WORKSPACE CONFIGURATION</div><h1>Settings <span>& status.</span></h1><p>Review this frontend’s API target and check backend reachability.</p></div>
        <span className="outline-chip"><Activity size={13} /> LOCAL CONFIGURATION</span>
      </section>

      <div className="settings-layout">
        <section className="panel settings-card">
          <div className="settings-card-icon"><Server size={17} /></div>
          <div className="panel-kicker"><span className="panel-kicker-line" /> BACKEND API</div>
          <h2>Connection target</h2>
          <p>The frontend sends requests only to the configured Gitlexa API base URL.</p>
          <div className="setting-value-row"><span>API base URL</span><code>{API_BASE_URL}</code></div>
          <div className="setting-value-row"><span>Configuration</span><code>VITE_API_BASE_URL</code></div>
          <button className="secondary-button health-check-button" type="button" onClick={checkHealth} disabled={isChecking}>
            <RefreshCw className={isChecking ? 'spin-icon' : ''} size={14} /> {isChecking ? 'Checking backend…' : 'Check backend health'}
          </button>
          {health && <div className="settings-health success-health" role="status"><CheckCircle2 size={15} /><span><strong>Backend reports {health.status}</strong><small>{health.service ?? 'Gitlexa API'}{health.version ? ` · v${health.version}` : ''}</small></span></div>}
          {error && <div className="settings-health error-health" role="alert"><CircleAlert size={15} /><span><strong>Health check failed</strong><small>{error}</small></span></div>}
          {!health && !error && <p className="settings-health-hint">No health check has been run in this session.</p>}
          <button className="secondary-button health-check-button" type="button" onClick={checkAuthStatus} disabled={isCheckingAuth}>
            <RefreshCw className={isCheckingAuth ? 'spin-icon' : ''} size={14} /> {isCheckingAuth ? 'Checking token configuration…' : 'Check GitHub token configuration'}
          </button>
          {authStatus && <div className="settings-health success-health" role="status"><CheckCircle2 size={15} /><span><strong>{authStatus.configured ? 'GitHub token configured' : 'No GitHub token configured'}</strong><small>Backend configuration only; token validity and user authentication are not verified.</small></span></div>}
          {authError && <div className="settings-health error-health" role="alert"><CircleAlert size={15} /><span><strong>Token configuration check failed</strong><small>{authError}</small></span></div>}
        </section>

        <section className="panel settings-card">
          <div className="settings-card-icon privacy-icon"><Activity size={17} /></div>
          <div className="panel-kicker"><span className="panel-kicker-line" /> DATA & PRIVACY</div>
          <h2>Honest by default</h2>
          <p>Repository findings are shown only when returned by the backend analysis API.</p>
          <ul className="privacy-list">
            <li><CheckCircle2 size={14} /><span>Live analysis requests go through the Gitlexa backend.</span></li>
            <li><CheckCircle2 size={14} /><span>Unavailable GitHub sources are reported rather than filled with sample findings.</span></li>
            <li><CheckCircle2 size={14} /><span>No GitHub token or AWS credential is stored in the frontend.</span></li>
            <li><CheckCircle2 size={14} /><span>No direct browser connection to GitHub or AWS is made.</span></li>
          </ul>
          <p className="settings-health-hint">The backend exposes GitHub-token configuration status, but does not implement Gitlexa user registration or login.</p>
        </section>
      </div>
    </div>
  );
}
