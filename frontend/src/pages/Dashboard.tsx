import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CircleAlert,
  Clock3,
  Code2,
  GitBranch,
  GitCommitHorizontal,
  GitPullRequest,
  Github,
  Layers3,
  Sparkles,
  Terminal,
  TriangleAlert,
  Workflow,
} from 'lucide-react';

type Page = 'dashboard' | 'project' | 'analysis' | 'settings' | 'profile';

interface DashboardProps {
  onOpenAssistant: () => void;
  onNavigate: (page: Page) => void;
}

const activityItems = [
  { initials: 'MK', color: 'lavender', title: 'Maya Kim', action: 'opened a pull request', detail: 'refactor: simplify auth middleware', time: '18 min ago', kind: 'PR', number: '#128' },
  { initials: 'JL', color: 'mint', title: 'Jordan Lee', action: 'pushed to', detail: 'feature/cache-headers', time: '42 min ago', kind: 'COMMIT', number: 'a91f2c' },
  { initials: 'SR', color: 'peach', title: 'Sam Rivera', action: 'commented on', detail: 'Fix worker retry backoff', time: '1 hr ago', kind: 'ISSUE', number: '#84' },
];

const blockers = [
  { severity: 'critical', title: 'Release workflow failing', detail: 'test / node-20 · 2 runs failed', icon: Workflow },
  { severity: 'high', title: 'PR #128 needs review', detail: 'Waiting on 1 required reviewer', icon: GitPullRequest },
  { severity: 'medium', title: 'Dependency update is stale', detail: 'security patch · opened 6 days ago', icon: CircleAlert },
];

export default function Dashboard({ onOpenAssistant, onNavigate }: DashboardProps) {
  return (
    <div className="page-shell dashboard-page">
      <div className="demo-banner" role="note">
        <span className="demo-banner-icon"><Activity size={14} aria-hidden="true" /></span>
        <span><strong>DEMO DATA</strong><span className="demo-banner-divider">/</span>NOT LIVE GITHUB TELEMETRY</span>
        <span className="demo-banner-note">Sample workspace · interactions are simulated</span>
      </div>

      <section className="welcome-row" aria-labelledby="dashboard-title">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> REPOSITORY INTELLIGENCE</div>
          <h1 id="dashboard-title">Your codebase,<br className="mobile-break" /> <span>in focus.</span></h1>
          <p className="welcome-copy">A clear signal on what’s moving, what’s stuck, and what needs you next.</p>
        </div>
        <button className="assistant-hero-button" type="button" onClick={onOpenAssistant}>
          <span className="assistant-button-icon"><Sparkles size={18} aria-hidden="true" /></span>
          <span className="assistant-button-text"><strong>Ask Alexa<span>+</span></strong><small>Get a read on your repo</small></span>
          <ArrowRight size={17} aria-hidden="true" />
        </button>
      </section>

      <section className="repo-bar" aria-label="Selected demo repository">
        <div className="repo-identity">
          <span className="repo-github"><Github size={19} aria-hidden="true" /></span>
          <div>
            <div className="repo-name">northstar <span>/</span> platform-api <span className="repo-chevron">⌄</span></div>
            <div className="repo-subtitle">DEMO REPOSITORY <span className="repo-dot">·</span> Node.js <span className="language-dot" /> TypeScript</div>
          </div>
        </div>
        <div className="repo-bar-right">
          <span className="branch-chip"><GitBranch size={13} aria-hidden="true" /> main</span>
          <span className="repo-updated"><Clock3 size={13} aria-hidden="true" /> Updated 12 min ago</span>
          <button className="icon-button repo-menu-button" type="button" onClick={() => onNavigate('project')} aria-label="Open project details">•••</button>
        </div>
      </section>

      <section className="health-overview" aria-label="Repository health overview">
        <article className="health-card health-score-card">
          <div className="health-card-top">
            <span className="card-label">REPOSITORY HEALTH</span>
            <span className="health-status"><span className="status-dot status-warning" /> NEEDS ATTENTION</span>
          </div>
          <div className="health-score-row">
            <div className="health-score"><span>78</span><small>/ 100</small></div>
            <div className="health-trend"><ArrowDownRight size={15} aria-hidden="true" /><span>6 pts</span><small>vs last week</small></div>
            <div className="score-ring" aria-label="78 out of 100 health score"><span>78</span></div>
          </div>
          <div className="score-track" aria-hidden="true"><span /></div>
          <div className="health-card-foot"><span>3 signals need a closer look</span><button type="button" onClick={() => onNavigate('analysis')}>View analysis <ArrowRight size={13} /></button></div>
        </article>

        <article className="metric-card">
          <div className="metric-heading"><span className="metric-icon issue-icon"><CircleAlert size={15} aria-hidden="true" /></span><span>OPEN ISSUES</span><span className="metric-delta negative"><ArrowUpRight size={12} /> 2</span></div>
          <div className="metric-value">12</div>
          <div className="metric-foot"><span className="metric-bars issue-bars" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></span><span>2 need attention</span></div>
        </article>

        <article className="metric-card">
          <div className="metric-heading"><span className="metric-icon pr-icon"><GitPullRequest size={15} aria-hidden="true" /></span><span>OPEN PULL REQUESTS</span><span className="metric-delta positive"><ArrowDownRight size={12} /> 1</span></div>
          <div className="metric-value">4</div>
          <div className="metric-foot"><span className="review-avatars" aria-label="Three reviewers"><i>MK</i><i>JL</i><i>+1</i></span><span>1 awaiting review</span></div>
        </article>

        <article className="metric-card workflow-metric">
          <div className="metric-heading"><span className="metric-icon ci-icon"><Workflow size={15} aria-hidden="true" /></span><span>WORKFLOW HEALTH</span><span className="metric-delta negative"><ArrowDownRight size={12} /> 8%</span></div>
          <div className="metric-value">2 <small>failed</small></div>
          <div className="metric-foot"><span className="workflow-line" aria-label="Workflow checks show recent failures"><i /><i /><i /><i /><i /><i /><i /></span><span>of 14 recent runs</span></div>
        </article>
      </section>

      <div className="dashboard-grid">
        <section className="panel blocker-panel" aria-labelledby="blockers-title">
          <div className="panel-heading">
            <div><div className="panel-kicker"><span className="panel-kicker-line" /> PRIORITY SIGNALS</div><h2 id="blockers-title">What needs attention</h2></div>
            <button className="text-link" type="button" onClick={() => onNavigate('analysis')}>All signals <ArrowRight size={14} /></button>
          </div>
          <div className="blocker-list">
            {blockers.map(({ severity, title, detail, icon: Icon }, index) => (
              <button className="blocker-item" type="button" key={title} onClick={() => onNavigate('analysis')}>
                <span className={`severity-mark ${severity}`}><Icon size={15} aria-hidden="true" /></span>
                <span className="blocker-content"><strong>{title}</strong><small>{detail}</small></span>
                <span className={`severity-tag ${severity}`}>{severity.toUpperCase()}</span>
                <span className="blocker-arrow" aria-hidden="true"><ArrowRight size={15} /></span>
                {index < blockers.length - 1 && <span className="blocker-divider" aria-hidden="true" />}
              </button>
            ))}
          </div>
          <button className="blocker-footer" type="button" onClick={() => onNavigate('analysis')}>
            <span><TriangleAlert size={14} aria-hidden="true" /> 3 active blockers identified in demo data</span>
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        </section>

        <section className="panel workflow-panel" aria-labelledby="workflow-title">
          <div className="panel-heading compact-heading">
            <div><div className="panel-kicker"><span className="panel-kicker-line" /> CONTINUOUS INTEGRATION</div><h2 id="workflow-title">Workflow pulse</h2></div>
            <span className="live-indicator"><span /> DEMO</span>
          </div>
          <div className="workflow-summary">
            <div className="workflow-score"><span>86</span><small>%</small></div>
            <div className="workflow-summary-copy"><strong>Mostly steady</strong><span>12 passed <b>·</b> 2 failed</span></div>
          </div>
          <div className="workflow-chart" role="img" aria-label="Sample workflow success rate trend over seven days">
            <div className="chart-axis"><span>100%</span><span>50%</span><span>0%</span></div>
            <div className="chart-grid"><i /><i /><i /></div>
            <svg viewBox="0 0 440 104" preserveAspectRatio="none" aria-hidden="true">
              <defs><linearGradient id="chart-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#6686ff" stopOpacity=".22" /><stop offset="100%" stopColor="#6686ff" stopOpacity="0" /></linearGradient></defs>
              <path d="M0 29 C24 24 34 32 58 22 S96 16 118 24 S154 36 176 25 S209 19 235 28 S269 18 294 26 S325 42 352 31 S385 30 410 44 S430 53 440 49 L440 104 L0 104Z" fill="url(#chart-fill)" />
              <path d="M0 29 C24 24 34 32 58 22 S96 16 118 24 S154 36 176 25 S209 19 235 28 S269 18 294 26 S325 42 352 31 S385 30 410 44 S430 53 440 49" fill="none" stroke="#7792ff" strokeWidth="2" vectorEffect="non-scaling-stroke" />
              <circle cx="440" cy="49" r="4" fill="#f4a26e" stroke="#151a26" strokeWidth="3" vectorEffect="non-scaling-stroke" />
            </svg>
            <div className="chart-days"><span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span>SAT</span><span>SUN</span></div>
          </div>
          <div className="workflow-foot"><span><span className="workflow-foot-dot success" /> 12 successful</span><span><span className="workflow-foot-dot failed" /> 2 failed</span><button type="button" onClick={() => onNavigate('analysis')}>Inspect runs <ArrowRight size={13} /></button></div>
        </section>
      </div>

      <div className="dashboard-grid lower-grid">
        <section className="panel activity-panel" aria-labelledby="activity-title">
          <div className="panel-heading compact-heading">
            <div><div className="panel-kicker"><span className="panel-kicker-line" /> REPOSITORY STREAM</div><h2 id="activity-title">Recent activity</h2></div>
            <button className="text-link" type="button" onClick={() => onNavigate('project')}>View project <ArrowRight size={14} /></button>
          </div>
          <div className="activity-list">
            {activityItems.map((item) => (
              <article className="activity-item" key={item.number}>
                <span className={`activity-avatar ${item.color}`}>{item.initials}</span>
                <div className="activity-copy"><p><strong>{item.title}</strong> {item.action}</p><span className="activity-detail"><Code2 size={12} aria-hidden="true" /> {item.detail}</span></div>
                <div className="activity-meta"><span className="activity-kind">{item.kind}</span><span>{item.number}</span><small>{item.time}</small></div>
              </article>
            ))}
          </div>
          <button className="activity-footer" type="button" onClick={() => onNavigate('project')}>Explore repository activity <ArrowRight size={14} /></button>
        </section>

        <section className="panel commit-panel" aria-labelledby="commit-title">
          <div className="panel-heading compact-heading">
            <div><div className="panel-kicker"><span className="panel-kicker-line" /> SOURCE CONTROL</div><h2 id="commit-title">Latest commits</h2></div>
            <span className="commit-branch"><GitBranch size={12} aria-hidden="true" /> main</span>
          </div>
          <div className="commit-list">
            <article className="commit-item"><span className="commit-icon"><GitCommitHorizontal size={17} /></span><div><strong>fix: guard empty webhook payload</strong><span><span className="commit-hash">c4e81b7</span> · Maya Kim</span></div><time>24m</time></article>
            <article className="commit-item"><span className="commit-icon"><GitCommitHorizontal size={17} /></span><div><strong>chore: bump node runtime to 20</strong><span><span className="commit-hash">a91f2c0</span> · Jordan Lee</span></div><time>1h</time></article>
            <article className="commit-item"><span className="commit-icon"><GitCommitHorizontal size={17} /></span><div><strong>feat: add request tracing context</strong><span><span className="commit-hash">e70b91d</span> · Sam Rivera</span></div><time>3h</time></article>
          </div>
          <div className="commit-insight"><span><Layers3 size={14} aria-hidden="true" /> 8 commits this week</span><span><span className="commit-insight-dot" /> Steady pace</span></div>
        </section>
      </div>

      <section className="assistant-strip">
        <div className="assistant-strip-orb" aria-hidden="true"><Sparkles size={18} /></div>
        <div className="assistant-strip-copy"><span className="assistant-strip-label">YOUR REPO, EXPLAINED</span><p>There’s context behind every signal. Get the short version.</p></div>
        <button type="button" onClick={onOpenAssistant}>Talk through it <ArrowRight size={15} /></button>
        <span className="assistant-strip-disclaimer">SIMULATED ASSISTANT</span>
      </section>
      <div className="dashboard-bottom-note"><Terminal size={12} aria-hidden="true" /> Sample activity and metrics are illustrative; no live repository has been connected. <button type="button" onClick={() => onNavigate('project')}>Register a project <ArrowUpRight size={12} /></button></div>
    </div>
  );
}
