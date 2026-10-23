import { useState } from 'react';
import {
  Activity,
  ArrowRight,
  CircleAlert,
  Clock3,
  LoaderCircle,
  ShieldAlert,
  Workflow,
} from 'lucide-react';
import { ApiError } from '../services/api';
import { runAnalysis } from '../services/analysis';
import type { AnalysisResponse, ProjectResponse } from '../types';

interface AnalysisProps {
  registeredProject: ProjectResponse | null;
  result: AnalysisResponse | null;
  onResultChange: (result: AnalysisResponse | null) => void;
  onAnalysisErrorChange: (error: string) => void;
  onNavigateToProject: () => void;
}

export default function Analysis({
  registeredProject,
  result,
  onResultChange,
  onAnalysisErrorChange,
  onNavigateToProject,
}: AnalysisProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleRunAnalysis() {
    if (!registeredProject || isSubmitting) return;
    setError('');
    onResultChange(null);
    onAnalysisErrorChange('');
    setIsSubmitting(true);
    try {
      const response = await runAnalysis(registeredProject.id);
      if (response.simulated || response.source !== 'live') {
        throw new Error('The backend did not return verified live GitHub data. No result was displayed.');
      }
      onResultChange(response);
    } catch (requestError) {
      const message = requestError instanceof ApiError
        ? requestError.message
        : requestError instanceof Error
          ? requestError.message
          : 'Could not run the live GitHub analysis. Please try again.';
      setError(message);
      onAnalysisErrorChange(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-shell inner-page">
      <div className="page-breadcrumb"><span>WORKSPACE</span><i>/</i><strong>ANALYSIS</strong></div>
      <section className="inner-page-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" /> BLOCKER INTELLIGENCE</div><h1>Analysis <span>room.</span></h1><p>Retrieve current repository data from GitHub through the backend.</p></div>
        <span className="outline-chip"><Activity size={13} /> LIVE GITHUB</span>
      </section>

      <div className="analysis-layout">
        <section className="panel analysis-queue-panel">
          <div className="panel-kicker"><span className="panel-kicker-line" /> BACKEND ANALYSIS</div>
          {registeredProject ? (
            <>
              <h2>Ready to analyze</h2>
              <div className="analysis-project-chip"><span className="project-avatar"><Activity size={15} /></span><span><strong>{registeredProject.name}</strong><small>{registeredProject.repo_url}</small></span></div>
              <p className="analysis-queue-copy">Live analysis retrieves repository data through the backend GitHub REST API. Public repositories need no token; private access requires a backend-only token.</p>
              <button className="primary-button" type="button" onClick={handleRunAnalysis} disabled={isSubmitting}>
                {isSubmitting ? <LoaderCircle className="spin-icon" size={15} /> : <Workflow size={15} />}
                {isSubmitting ? 'Running live analysis…' : 'Run live analysis'}
                {!isSubmitting && <ArrowRight size={15} />}
              </button>
            </>
          ) : (
            <div className="analysis-empty-state">
              <span className="empty-state-icon"><ShieldAlert size={20} /></span>
              <h2>No backend project yet</h2>
              <p>Register a repository first so the backend can identify which GitHub project to analyze.</p>
              <button className="secondary-button" type="button" onClick={onNavigateToProject}>Go to project setup <ArrowRight size={14} /></button>
            </div>
          )}
          {error && <p className="form-feedback error-feedback" role="alert"><CircleAlert size={14} />{error}</p>}
          {isSubmitting && <p className="analysis-loading" role="status"><LoaderCircle className="spin-icon" size={14} /> Retrieving live GitHub repository data…</p>}
          {result && (
            <div className="analysis-completed-result" aria-live="polite">
              <div className="analysis-source-banner live-result-banner">
                <CircleAlert size={15} />
                <strong>LIVE GITHUB RESULT</strong>
                <span>Retrieved from the GitHub REST API; unavailable sources are listed below.</span>
              </div>
              <div className="analysis-result">
                <span><Clock3 size={15} /> {result.source} analysis {result.status}</span>
                <small>Analysis ID: {result.analysis_id}</small>
                <small>Registered project: {result.repository}</small>
              </div>
              {result.repository_metadata && (
                <section className="analysis-result-section">
                  <h3>Repository metadata</h3>
                  <div className="analysis-repository-metadata">
                    <strong>{result.repository_metadata.full_name}</strong>
                    <span>{result.repository_metadata.visibility} · default branch {result.repository_metadata.default_branch}{result.repository_metadata.language ? ` · ${result.repository_metadata.language}` : ''}</span>
                    {(result.repository_metadata.is_fork || result.repository_metadata.is_archived) && <span>{result.repository_metadata.is_fork ? 'Fork' : ''}{result.repository_metadata.is_fork && result.repository_metadata.is_archived ? ' · ' : ''}{result.repository_metadata.is_archived ? 'Archived' : ''}</span>}
                    {result.repository_metadata.description && <p>{result.repository_metadata.description}</p>}
                    <small>{result.repository_metadata.stargazers_count} stars · {result.repository_metadata.forks_count} forks · {result.repository_metadata.open_issues_count} open issues/PRs</small>
                    <a href={result.repository_metadata.html_url} target="_blank" rel="noreferrer">View repository on GitHub</a>
                  </div>
                </section>
              )}
              <section className="analysis-result-section">
                <h3>Data availability</h3>
                <ul className="analysis-availability">
                  {Object.entries(result.data_availability).map(([source, status]) => (
                    <li key={source}><strong>{source.replace('_', ' ')}</strong><span>{status}</span></li>
                  ))}
                </ul>
              </section>
              <section className="analysis-result-section">
                <h3>Summary</h3>
                <p>{result.summary}</p>
              </section>
              <section className="analysis-result-section">
                <h3>Blockers <span>{result.blockers.length}</span></h3>
                {result.blockers.length ? result.blockers.map((blocker) => (
                  <article className="analysis-blocker" key={blocker.id}>
                    <div className="analysis-blocker-heading">
                      <strong>{blocker.title}</strong>
                      <span className={`severity-tag ${blocker.severity}`}>{blocker.severity}</span>
                    </div>
                    <p>{blocker.explanation}</p>
                    <p><b>Impact:</b> {blocker.impact}</p>
                    <p><b>Confidence:</b> {Math.round(blocker.confidence * 100)}%</p>
                    <p><b>Supporting evidence:</b> {blocker.evidence_ids.join(', ') || 'None'}</p>
                    <div className="analysis-recommendation"><b>Recommended next action</b>
                      <ul>{blocker.recommended_actions.map((action) => <li key={action}>{action}</li>)}</ul>
                    </div>
                  </article>
                )) : <p className="analysis-no-evidence">No blockers were returned for this analysis.</p>}
              </section>
              <section className="analysis-result-section">
                <h3>Evidence <span>{result.evidence.length}</span></h3>
                {result.evidence.length ? result.evidence.map((evidence) => (
                  <article className="analysis-evidence" key={evidence.id}>
                    <div className="analysis-blocker-heading">
                      <strong>{evidence.title}</strong>
                      <span className="source-tag">GITHUB</span>
                    </div>
                    <p>{evidence.description}</p>
                      <small>{evidence.type.replace('_', ' ')} · evidence score {Math.round(evidence.score * 100)}% · ID {evidence.id}{evidence.timestamp ? ` · ${new Date(evidence.timestamp).toLocaleString()}` : ''}</small>
                      {evidence.source_url && <a className="analysis-source-link" href={evidence.source_url} target="_blank" rel="noreferrer">Open source evidence</a>}
                  </article>
                )) : <p className="analysis-no-evidence">No evidence was returned.</p>}
              </section>
            </div>
          )}
        </section>

      </div>
    </div>
  );
}
