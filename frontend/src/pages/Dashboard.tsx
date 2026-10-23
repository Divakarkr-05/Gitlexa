import { Activity, ArrowRight, CircleAlert, Github, Sparkles } from 'lucide-react';
import type { AnalysisResponse, ProjectResponse } from '../types';

type Page = 'dashboard' | 'project' | 'analysis' | 'settings';

interface DashboardProps {
  onOpenAssistant: () => void;
  onNavigate: (page: Page) => void;
  registeredProject: ProjectResponse | null;
  analysisResult: AnalysisResponse | null;
}

export default function Dashboard({
  onOpenAssistant,
  onNavigate,
  registeredProject,
  analysisResult,
}: DashboardProps) {
  return (
    <div className="page-shell dashboard-page">
      <section className="welcome-row" aria-labelledby="dashboard-title">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> REPOSITORY INTELLIGENCE</div>
          <h1 id="dashboard-title">Your codebase,<br className="mobile-break" /> <span>in focus.</span></h1>
          <p className="welcome-copy">A clear view of repository signals retrieved from GitHub.</p>
        </div>
        <button className="assistant-hero-button" type="button" onClick={onOpenAssistant}>
          <span className="assistant-button-icon"><Sparkles size={18} aria-hidden="true" /></span>
          <span className="assistant-button-text"><strong>Ask Alexa<span>+</span></strong><small>Ask about retrieved evidence</small></span>
          <ArrowRight size={17} aria-hidden="true" />
        </button>
      </section>

      <div className="dashboard-grid">
        <section className="panel blocker-panel" aria-labelledby="repository-status-title">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker"><span className="panel-kicker-line" /> REGISTERED REPOSITORY</div>
              <h2 id="repository-status-title">Project status</h2>
            </div>
            <button className="text-link" type="button" onClick={() => onNavigate('project')}>Project setup <ArrowRight size={14} /></button>
          </div>
          {registeredProject ? (
            <div className="registered-project">
              <span><Github size={15} /> Registered with backend</span>
              <strong>{registeredProject.name}</strong>
              <a href={registeredProject.repo_url} target="_blank" rel="noreferrer">{registeredProject.repo_url}</a>
              <code>Project ID: {registeredProject.id}</code>
            </div>
          ) : (
            <div className="analysis-empty-state">
              <span className="empty-state-icon"><Github size={20} /></span>
              <h3>No repository registered</h3>
              <p>Register a GitHub repository to retrieve live metadata and analysis evidence.</p>
              <button className="secondary-button" type="button" onClick={() => onNavigate('project')}>Register a repository <ArrowRight size={14} /></button>
            </div>
          )}
        </section>

        <section className="panel blocker-panel" aria-labelledby="analysis-status-title">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker"><span className="panel-kicker-line" /> LIVE ANALYSIS</div>
              <h2 id="analysis-status-title">Latest findings</h2>
            </div>
            <button className="text-link" type="button" onClick={() => onNavigate('analysis')}>Analysis <ArrowRight size={14} /></button>
          </div>
          {analysisResult && !analysisResult.simulated ? (
            <>
              <p>{analysisResult.summary}</p>
              <div className="dashboard-result-counts">
                <span><CircleAlert size={15} /> {analysisResult.blockers.length} blockers</span>
                <span><Activity size={15} /> {analysisResult.evidence.length} evidence items</span>
              </div>
              {analysisResult.blockers.slice(0, 3).map((blocker) => (
                <article className="analysis-blocker" key={blocker.id}>
                  <div className="analysis-blocker-heading">
                    <strong>{blocker.title}</strong>
                    <span className={`severity-tag ${blocker.severity}`}>{blocker.severity}</span>
                  </div>
                  <p>{blocker.explanation}</p>
                </article>
              ))}
              <small>Retrieved {new Date(analysisResult.analyzed_at).toLocaleString()} · source: GitHub REST API</small>
            </>
          ) : (
            <div className="analysis-empty-state">
              <span className="empty-state-icon"><Activity size={20} /></span>
              <h3>No live analysis yet</h3>
              <p>Run a live analysis to view current repository findings. No sample results are shown here.</p>
              <button className="secondary-button" type="button" onClick={() => onNavigate('analysis')}>Run live analysis <ArrowRight size={14} /></button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
