import { useRef, useState, type FormEvent } from 'react';
import { Activity, ArrowRight, CircleAlert, Eye, EyeOff, ShieldCheck, Sparkles } from 'lucide-react';

interface LoginProps {
  onDemoAccess: () => void;
}

export default function Login({ onDemoAccess }: LoginProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    const email = emailRef.current;
    const password = passwordRef.current;
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

    setError('Email and password sign-in is not available. Your credentials were not sent or saved. Use demo access instead.');
    password.value = '';
    password.focus();
  }

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
            <p>A calm, clear view of what’s moving, what’s stuck, and what needs attention.</p>
          </div>
          <div className="login-preview-note">
            <Sparkles size={16} aria-hidden="true" />
            <span>Explore the workspace and Alexa+ in a labeled demo session.</span>
          </div>
        </section>

        <section className="login-card panel" aria-labelledby="login-card-title">
          <div className="login-card-kicker"><span className="panel-kicker-line" /> WORKSPACE ACCESS</div>
          <h2 id="login-card-title">Welcome back</h2>
          <p className="login-card-copy">Email/password sign-in is not configured. Preview the workspace using demo access.</p>

          <form className="login-form" noValidate onSubmit={handleSignIn}>
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              ref={emailRef}
              type="email"
              name="email"
              autoComplete="off"
              placeholder="you@example.com"
              aria-describedby={error ? 'login-error' : undefined}
            />
            <label htmlFor="login-password">Password</label>
            <div className="login-password-field">
              <input
                id="login-password"
                ref={passwordRef}
                type={showPassword ? 'text' : 'password'}
                name="password"
                autoComplete="off"
                placeholder="Enter your password"
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
            {error && <p className="login-error" id="login-error" role="alert"><CircleAlert size={16} />{error}</p>}
            <button className="primary-button login-submit" type="submit">Sign in <ArrowRight size={16} /></button>
          </form>

          <div className="login-separator"><span>OR</span></div>
          <button className="demo-access-button" type="button" onClick={onDemoAccess}>
            <span className="demo-access-icon"><Sparkles size={17} aria-hidden="true" /></span>
            <span><strong>Continue with demo access</strong><small>No account needed · simulated workspace</small></span>
            <ArrowRight size={16} aria-hidden="true" />
          </button>
          <p className="login-demo-warning"><ShieldCheck size={15} aria-hidden="true" /> Demo access is a temporary, browser-only preview. It is not secure authentication.</p>
          <p className="login-auth-note">Email/password authentication is not configured for this application. Credentials are never sent or stored.</p>
        </section>
      </div>
      <footer className="login-footer"><span>GITLEXA WORKSPACE</span><span>DEMO CONTENT IS CLEARLY LABELED</span></footer>
    </main>
  );
}
