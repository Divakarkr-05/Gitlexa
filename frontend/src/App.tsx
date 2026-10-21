import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity,
  Bot,
  ChevronDown,
  CircleHelp,
  Github,
  LayoutDashboard,
  LogOut,
  Settings as SettingsIcon,
  Sparkles,
  UserRound,
} from 'lucide-react';
import Analysis from './pages/Analysis';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Profile from './pages/Profile';
import Project from './pages/Project';
import Settings from './pages/Settings';
import AssistantExperience from './components/AssistantExperience';
import type { ProjectResponse } from './types';

type Page = 'dashboard' | 'project' | 'analysis' | 'settings' | 'profile';

const navigation: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'project', label: 'Project', icon: Github },
  { id: 'analysis', label: 'Analysis', icon: Activity },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
];

export default function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [demoSessionActive, setDemoSessionActive] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [registeredProject, setRegisteredProject] = useState<ProjectResponse | null>(null);
  const assistantTriggerRef = useRef<HTMLButtonElement>(null);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const profileTriggerRef = useRef<HTMLButtonElement>(null);
  const profileMenuItemsRef = useRef<Array<HTMLButtonElement | null>>([]);
  const assistantWasOpen = useRef(false);
  const closeAssistant = useCallback(() => setAssistantOpen(false), []);
  const startDemoSession = useCallback(() => {
    setDemoSessionActive(true);
    setPage('dashboard');
  }, []);
  const signOut = useCallback(() => {
    setDemoSessionActive(false);
    setAssistantOpen(false);
    setProfileMenuOpen(false);
    setPage('dashboard');
  }, []);

  useEffect(() => {
    if (!assistantOpen && assistantWasOpen.current) {
      assistantTriggerRef.current?.focus();
    }
    assistantWasOpen.current = assistantOpen;
  }, [assistantOpen]);

  useEffect(() => {
    if (!profileMenuOpen) return;

    profileMenuItemsRef.current[0]?.focus();

    const handlePointerDown = (event: PointerEvent) => {
      if (event.target instanceof Node && !profileMenuRef.current?.contains(event.target)) {
        setProfileMenuOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setProfileMenuOpen(false);
        profileTriggerRef.current?.focus();
        return;
      }
      const menu = profileMenuRef.current?.querySelector('[role="menu"]');
      if (!(event.target instanceof Node) || !menu?.contains(event.target)) return;

      const menuItems = profileMenuItemsRef.current.filter(
        (item): item is HTMLButtonElement => item !== null,
      );
      const currentIndex = menuItems.findIndex((item) => item === document.activeElement);
      if (currentIndex < 0) return;

      let nextIndex: number | null = null;
      if (event.key === 'ArrowDown') nextIndex = (currentIndex + 1) % menuItems.length;
      if (event.key === 'ArrowUp') nextIndex = (currentIndex - 1 + menuItems.length) % menuItems.length;
      if (event.key === 'Home') nextIndex = 0;
      if (event.key === 'End') nextIndex = menuItems.length - 1;
      if (nextIndex !== null) {
        event.preventDefault();
        menuItems[nextIndex]?.focus();
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [profileMenuOpen]);

  if (!demoSessionActive) {
    return <Login onDemoAccess={startDemoSession} />;
  }

  if (assistantOpen) {
    return <AssistantExperience onClose={closeAssistant} />;
  }

  return (
    <div className="app-container">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="topbar">
        <div className="topbar-inner">
          <button className="brand" type="button" onClick={() => setPage('dashboard')} aria-label="Gitlexa home">
            <span className="brand-mark" aria-hidden="true"><Activity size={18} strokeWidth={2.4} /></span>
            <span className="brand-name">git<span>lexa</span></span>
            <span className="brand-divider" aria-hidden="true" />
            <span className="brand-workspace">WORKSPACE</span>
          </button>

          <nav className="top-navigation" aria-label="Main navigation">
            {navigation.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                className={`nav-link${page === id ? ' is-active' : ''}`}
                aria-current={page === id ? 'page' : undefined}
                onClick={() => setPage(id)}
              >
                <Icon size={15} aria-hidden="true" />
                <span>{label}</span>
              </button>
            ))}
          </nav>

          <div className="topbar-actions">
            <button className="help-button" type="button" onClick={() => setPage('settings')} aria-label="Help and settings">
              <CircleHelp size={17} />
            </button>
            <span className="topbar-divider" aria-hidden="true" />
            <button
              className="alexa-launch"
              type="button"
              ref={assistantTriggerRef}
              onClick={() => setAssistantOpen(true)}
            >
              <Sparkles size={16} aria-hidden="true" />
              <span>Alexa<span className="alexa-plus">+</span></span>
              <ChevronDown className="launch-chevron" size={13} aria-hidden="true" />
            </button>
            <div className="profile-menu-wrap" ref={profileMenuRef}>
              <button
                className="profile-trigger"
                type="button"
                ref={profileTriggerRef}
                aria-label="Open demo profile menu"
                aria-haspopup="menu"
                aria-expanded={profileMenuOpen}
                aria-controls="profile-menu"
                onClick={() => setProfileMenuOpen((open) => !open)}
                onKeyDown={(event) => {
                  if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    setProfileMenuOpen(true);
                  }
                }}
              >
                <span className="profile-avatar-small" aria-hidden="true">DU</span>
                <ChevronDown size={12} aria-hidden="true" />
              </button>
              {profileMenuOpen && (
                <div className="profile-menu" id="profile-menu" role="menu" aria-label="Demo account">
                  <div className="profile-menu-heading" role="presentation">
                    <strong>Demo User</strong>
                    <span>DEMO SESSION</span>
                  </div>
                  <button
                    ref={(element) => { profileMenuItemsRef.current[0] = element; }}
                    type="button"
                    role="menuitem"
                    onClick={() => { setPage('profile'); setProfileMenuOpen(false); }}
                  >
                    <UserRound size={15} aria-hidden="true" /> Profile
                  </button>
                  <button
                    ref={(element) => { profileMenuItemsRef.current[1] = element; }}
                    type="button"
                    role="menuitem"
                    onClick={() => { setPage('settings'); setProfileMenuOpen(false); }}
                  >
                    <SettingsIcon size={15} aria-hidden="true" /> Settings
                  </button>
                  <button
                    ref={(element) => { profileMenuItemsRef.current[2] = element; }}
                    type="button"
                    role="menuitem"
                    onClick={signOut}
                  >
                    <LogOut size={15} aria-hidden="true" /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main id="main-content" className="main-content">
        {page === 'dashboard' && <Dashboard onOpenAssistant={() => setAssistantOpen(true)} onNavigate={setPage} />}
        {page === 'project' && (
          <Project
            registeredProject={registeredProject}
            onProjectRegistered={setRegisteredProject}
          />
        )}
        {page === 'analysis' && (
          <Analysis registeredProject={registeredProject} onNavigateToProject={() => setPage('project')} />
        )}
        {page === 'settings' && <Settings />}
        {page === 'profile' && <Profile />}
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          <span><span className="footer-pulse" aria-hidden="true" /> Gitlexa workspace</span>
          <span className="footer-separator" aria-hidden="true">/</span>
          <span>Built for the signal in your repo</span>
          <span className="footer-version">PREVIEW <Bot size={12} aria-hidden="true" /></span>
        </div>
      </footer>
    </div>
  );
}
