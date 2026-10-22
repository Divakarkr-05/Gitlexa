import { useRef, useState, type FormEvent } from 'react';
import { Activity, ArrowRight, CircleAlert, Eye, EyeOff, ShieldCheck, Sparkles } from 'lucide-react';

type AuthMode = 'login' | 'signup';

export default function Login() {
  const [mode, setMode] = useState<AuthMode>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const confirmationRef = useRef<HTMLInputElement>(null);

  function switchMode(nextMode: AuthMode) {
    setMode(nextMode);
    setError('');
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

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

    setError('Account sign-up and login are not available yet. The backend does not provide user authentication endpoints. Your credentials were not sent or saved.');
    password.value = '';
    if (confirmationRef.current) confirmationRef.current.value = '';
    password.focus();
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
            <span>Live repository analysis is available after the backend account service is configured.</span>
          </div>
        </section>

        <section className="login-card panel" aria-labelledby="login-card-title">
          <div className="login-card-kicker"><span className="panel-kicker-line" /> ACCOUNT ACCESS</div>
          <h2 id="login-card-title">{isSignup ? 'Create your account' : 'Welcome back'}</h2>
          <p className="login-card-copy">Choose an option below. Account authentication is not yet connected to the backend.</p>
          <div className="auth-mode-switch" aria-label="Account access mode">
            <button type="button" aria-pressed={!isSignup} className={!isSignup ? 'is-active' : ''} onClick={() => switchMode('login')}>Log In</button>
            <button type="button" aria-pressed={isSignup} className={isSignup ? 'is-active' : ''} onClick={() => switchMode('signup')}>Sign Up</button>
          </div>

          <form className="login-form" noValidate onSubmit={handleSubmit}>
            {isSignup && (
              <>
                <label htmlFor="signup-name">Name</label>
                <input id="signup-name" ref={nameRef} type="text" name="name" autoComplete="name" placeholder="Your name" />
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
                  aria-describedby={error ? 'login-error' : undefined}
                />
              </>
            )}
            {error && <p className="login-error" id="login-error" role="alert"><CircleAlert size={16} />{error}</p>}
            <button className="primary-button login-submit" type="submit">{isSignup ? 'Create account' : 'Log in'} <ArrowRight size={16} /></button>
          </form>

          <p className="login-auth-note"><ShieldCheck size={15} aria-hidden="true" /> No authentication request is sent. The backend currently exposes GitHub-token configuration status only, not user accounts or sessions.</p>
        </section>
      </div>
      <footer className="login-footer"><span>GITLEXA WORKSPACE</span><span>ACCOUNT SERVICE NOT CONFIGURED</span></footer>
    </main>
  );
}
