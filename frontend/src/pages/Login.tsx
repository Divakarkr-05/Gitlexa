import { useRef, useState, type FormEvent } from 'react';
import { Activity, ArrowRight, CircleAlert, CheckCircle2, Eye, EyeOff, ShieldCheck, Sparkles } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '../services/supabase';

type AuthMode = 'login' | 'signup';

interface LoginProps {
  onAuthenticated?: () => void;
}

export default function Login({ onAuthenticated }: LoginProps) {
  const [mode, setMode] = useState<AuthMode>('signup');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const confirmationRef = useRef<HTMLInputElement>(null);

  function switchMode(nextMode: AuthMode) {
    setMode(nextMode);
    setError('');
    setMessage('');
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setMessage('');

    const email = emailRef.current;
    const password = passwordRef.current;
    if (mode === 'signup' && !nameRef.current?.value.trim()) {
      setError('Enter your name to continue.');
      nameRef.current?.focus();
      return;
    }
    if (!email?.value.trim()) {
      setError('Enter an email address to continue.');
      email?.focus();
      return;
    }
    if (!email.validity.valid) {
      setError('Enter a valid email address.');
      email.focus();
      return;
    }
    if (!password?.value) {
      setError('Enter a password to continue.');
      password?.focus();
      return;
    }
    if (mode === 'signup' && password.value !== confirmationRef.current?.value) {
      setError('The passwords do not match.');
      confirmationRef.current?.focus();
      return;
    }

    if (!isSupabaseConfigured) {
      setError('Supabase is not configured yet. Please check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env.');
      return;
    }

    setIsLoading(true);

    try {
      if (mode === 'signup') {
        const displayName = nameRef.current?.value.trim() || '';
        const { data, error: authError } = await supabase.auth.signUp({
          email: email.value.trim(),
          password: password.value,
          options: {
            data: {
              name: displayName,
              full_name: displayName,
            },
          },
        });

        if (authError) {
          setError(authError.message);
          return;
        }

        if (data.session) {
          onAuthenticated?.();
        } else if (data.user) {
          setMessage('Account created! Please check your email to confirm your account, then log in below.');
          setMode('login');
          if (passwordRef.current) passwordRef.current.value = '';
          if (confirmationRef.current) confirmationRef.current.value = '';
        }
      } else {
        const { data, error: authError } = await supabase.auth.signInWithPassword({
          email: email.value.trim(),
          password: password.value,
        });

        if (authError) {
          setError(authError.message);
          return;
        }

        if (data.session) {
          onAuthenticated?.();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred during authentication.');
    } finally {
      setIsLoading(false);
    }
  }

  const isSignup = mode === 'signup';

  return (
    <main className="login-screen">
      <div className="login-layout">
        <section className="login-intro" aria-labelledby="login-title">
          <div className="login-brand">
            <span className="brand-mark" aria-hidden="true"><Activity size={19} strokeWidth={2.4} /></span>
            <span className="brand-name">git<span>lexa</span></span>
          </div>
          <div className="login-intro-copy">
            <div className="eyebrow"><span className="eyebrow-line" /> REPOSITORY INTELLIGENCE</div>
            <h1 id="login-title">Your codebase,<br /><span>in focus.</span></h1>
            <p>Investigate GitHub issues, pull requests, commits, and workflow signals in one place.</p>
          </div>
          <div className="login-capability-note">
            <Sparkles size={16} aria-hidden="true" />
            <span>AI-assisted repository intelligence with Amazon Bedrock and Model Context Protocol.</span>
          </div>
        </section>

        <section className="login-card panel" aria-labelledby="login-card-title">
          <div className="login-card-kicker"><span className="panel-kicker-line" /> ACCOUNT ACCESS</div>
          <h2 id="login-card-title">{isSignup ? 'Create your account' : 'Welcome back'}</h2>
          <p className="login-card-copy">{isSignup ? 'Register your account with Supabase Auth.' : 'Sign in to your Gitlexa workspace.'}</p>
          <div className="auth-mode-switch" aria-label="Account access mode">
            <button type="button" aria-pressed={!isSignup} className={!isSignup ? 'is-active' : ''} onClick={() => switchMode('login')}>Log In</button>
            <button type="button" aria-pressed={isSignup} className={isSignup ? 'is-active' : ''} onClick={() => switchMode('signup')}>Sign Up</button>
          </div>

          <form className="login-form" noValidate onSubmit={handleSubmit}>
            {isSignup && (
              <>
                <label htmlFor="signup-name">Name</label>
                <input id="signup-name" ref={nameRef} type="text" name="name" autoComplete="name" placeholder="Your name" disabled={isLoading} />
              </>
            )}
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              ref={emailRef}
              type="email"
              name="email"
              autoComplete="email"
              placeholder="you@example.com"
              disabled={isLoading}
              aria-describedby={error ? 'login-error' : undefined}
            />
            <label htmlFor="login-password">Password</label>
            <div className="login-password-field">
              <input
                id="login-password"
                ref={passwordRef}
                type={showPassword ? 'text' : 'password'}
                name="password"
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                placeholder={isSignup ? 'Create a password' : 'Enter your password'}
                disabled={isLoading}
                aria-describedby={error ? 'login-error' : undefined}
              />
              <button
                className="password-visibility"
                type="button"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
                onClick={() => setShowPassword((visible) => !visible)}
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
            {isSignup && (
              <>
                <label htmlFor="signup-confirm-password">Confirm password</label>
                <input
                  id="signup-confirm-password"
                  ref={confirmationRef}
                  type={showPassword ? 'text' : 'password'}
                  name="confirm-password"
                  autoComplete="new-password"
                  placeholder="Enter your password again"
                  disabled={isLoading}
                  aria-describedby={error ? 'login-error' : undefined}
                />
              </>
            )}
            {message && <p className="login-message" style={{ color: 'var(--color-success, #22c55e)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }} role="status"><CheckCircle2 size={16} />{message}</p>}
            {error && <p className="login-error" id="login-error" role="alert"><CircleAlert size={16} />{error}</p>}
            <button className="primary-button login-submit" type="submit" disabled={isLoading}>
              {isLoading ? (isSignup ? 'Creating account…' : 'Logging in…') : (isSignup ? 'Create account' : 'Log in')} <ArrowRight size={16} />
            </button>
          </form>

          <p className="login-auth-note"><ShieldCheck size={15} aria-hidden="true" /> Secured by Supabase Authentication & PostgreSQL Row Level Security.</p>
        </section>
      </div>
      <footer className="login-footer"><span>GITLEXA WORKSPACE</span><span>SUPABASE AUTH CONNECTED</span></footer>
    </main>
  );
}
