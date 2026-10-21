import { useState } from 'react';
import { Activity, ArrowRight, CircleAlert, Clock3, LoaderCircle, ShieldAlert, Workflow } from 'lucide-react';
import { ApiError } from '../services/api';
import { runAnalysis } from '../services/analysis';
import type { AnalysisResponse, ProjectResponse } from '../types';

interface AnalysisProps {
  registeredProject: ProjectResponse | null;
  onNavigateToProject: () => void;
}

export default function Analysis({ registeredProject, onNavigateToProject }: AnalysisProps) {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleRunAnalysis() {
    if (!registeredProject) return;
    setError('');
    setIsSubmitting(true);
    try {
      setResult(await runAnalysis(registeredProject.id));
    } catch (requestError) {
      setError(requestError instanceof ApiError
        ? requestError.message
        : 'Could not queue the analysis. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-shell inner-page">
      <div className="page-breadcrumb"><span>WORKSPACE</span><i>/</i><strong>ANALYSIS</strong></div>
      <section className="inner-page-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" /> BLOCKER INTELLIGENCE</div><h1>Analysis <span>room.</span></h1><p>Queue a backend analysis or explore the clearly labeled sample findings.</p></div>
        <span className="outline-chip"><Activity size={13} /> DEMO FINDINGS</span>
      </section>

      <div className="analysis-layout">
        <section className="panel analysis-queue-panel">
          <div className="panel-kicker"><span className="panel-kicker-line" /> BACKEND ANALYSIS</div>
          {registeredProject ? (
            <>
              <h2>Ready to analyze</h2>
              <div className="analysis-project-chip"><span className="project-avatar"><Activity size={15} /></span><span><strong>{registeredProject.name}</strong><small>{registeredProject.repo_url}</small></span></div>
              <p className="analysis-queue-copy">This action calls the existing analysis queue endpoint. It returns a queue status only; the backend does not currently expose analysis results.</p>
              <button className="primary-button" type="button" onClick={handleRunAnalysis} disabled={isSubmitting}>
                {isSubmitting ? <LoaderCircle className="spin-icon" size={15} /> : <Workflow size={15} />}
                {isSubmitting ? 'Queueing analysis…' : 'Queue analysis'}
                <ArrowRight size={15} />
              </button>
            </>
          ) : (
            <div className="analysis-empty-state">
              <span className="empty-state-icon"><ShieldAlert size={20} /></span>
              <h2>No backend project yet</h2>
              <p>Register a repository first. The sample dashboard is not a backend project and cannot be analyzed.</p>
              <button className="secondary-button" type="button" onClick={onNavigateToProject}>Go to project setup <ArrowRight size={14} /></button>
            </div>
          )}
          {error && <p className="form-feedback error-feedback" role="alert"><CircleAlert size={14} />{error}</p>}
          {result && <div className="analysis-result" role="status"><span><Clock3 size={15} /> Analysis {result.status}</span><small>Request ID: {result.analysis_id}</small><small>Project ID: {result.project_id}</small></div>}
        </section>

        <section className="panel sample-findings-panel">
          <div className="panel-heading compact-heading"><div><div className="panel-kicker"><span className="panel-kicker-line" /> ILLUSTRATIVE ONLY</div><h2>Sample findings</h2></div><span className="demo-tag">NOT LIVE</span></div>
          <div className="sample-finding critical-finding"><span><Workflow size={15} /></span><div><strong>Release workflow failing</strong><small>Two sample test runs failed on node-20</small></div><b>CRITICAL</b></div>
          <div className="sample-finding high-finding"><span><Activity size={15} /></span><div><strong>Pull request waiting for review</strong><small>PR #128 · one required reviewer</small></div><b>HIGH</b></div>
          <div className="sample-finding medium-finding"><span><Clock3 size={15} /></span><div><strong>Dependency update is stale</strong><small>Illustrative issue · opened 6 days ago</small></div><b>MEDIUM</b></div>
          <div className="sample-findings-note"><CircleAlert size={13} /> These sample findings are hard-coded examples, not analysis output.</div>
        </section>
      </div>
    </div>
  );
}
