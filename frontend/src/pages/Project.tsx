import { FormEvent, useState } from 'react';
import { ArrowRight, CheckCircle2, CircleAlert, Github, Layers3, Plus } from 'lucide-react';
import { ApiError } from '../services/api';
import { createProject } from '../services/projects';
import type { ProjectResponse } from '../types';

interface ProjectProps {
  registeredProject: ProjectResponse | null;
  onProjectRegistered: (project: ProjectResponse) => void;
}

export default function Project({ registeredProject, onProjectRegistered }: ProjectProps) {
  const [name, setName] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [githubNotice, setGithubNotice] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSuccess('');
    setIsSubmitting(true);
    try {
      const project = await createProject({ name, repo_url: repoUrl });
      onProjectRegistered(project);
      setSuccess('Project registered with the backend. This does not connect GitHub or load telemetry.');
      setName('');
      setRepoUrl('');
    } catch (requestError) {
      setError(requestError instanceof ApiError
        ? requestError.message
        : 'Project registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-shell inner-page">
      <div className="page-breadcrumb"><span>WORKSPACE</span><i>/</i><strong>PROJECT</strong></div>
      <section className="inner-page-heading">
        <div><div className="eyebrow"><span className="eyebrow-line" /> REPOSITORY PROFILE</div><h1>Project <span>space.</span></h1><p>Register a repository with the backend, then retrieve live GitHub analysis.</p></div>
        <span className="outline-chip"><Layers3 size={13} /> BACKEND PROJECTS</span>
      </section>

      <div className="project-content-grid">
        <section className="panel project-profile-panel">
          <div className="panel-kicker"><span className="panel-kicker-line" /> GITHUB CONNECTION</div>
          <div style={{ margin: '14px 0 20px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px', fontSize: '15px', color: '#e7ecf9' }}>GitHub App Integration</h3>
                <p style={{ margin: 0, fontSize: '14px', color: '#929eb2' }}>Authorize repository telemetry via secure GitHub App.</p>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setGithubNotice('GitHub App connection will be configured through the backend service.')}
              >
                <Github size={15} /> Connect GitHub
              </button>
            </div>
            {githubNotice && (
              <p className="form-feedback success-feedback" style={{ marginTop: '10px' }} role="status">
                <CheckCircle2 size={14} /> {githubNotice}
              </p>
            )}
          </div>

          <div className="panel-kicker"><span className="panel-kicker-line" /> REGISTERED PROJECT</div>
          {registeredProject ? (
            <>
              <div className="project-profile">
                <span className="project-profile-icon"><Github size={22} /></span>
                <div><h2>{registeredProject.name}</h2><p>Registered with the Gitlexa backend</p></div>
              </div>
              <div className="registered-project">
                <a href={registeredProject.repo_url} target="_blank" rel="noreferrer">{registeredProject.repo_url}</a>
                <code>Project ID: {registeredProject.id}</code>
              </div>
              <p className="registration-note">Registration stores the project in backend memory. Repository metadata is verified only after a successful live analysis.</p>
            </>
          ) : (
            <div className="analysis-empty-state">
              <span className="empty-state-icon"><Github size={20} /></span>
              <h2>No project registered</h2>
              <p>Use the form to register the GitHub repository you want to analyze.</p>
            </div>
          )}
        </section>

        <section className="panel registration-panel">
          <div className="panel-kicker"><span className="panel-kicker-line" /> BACKEND REGISTRATION</div>
          <h2>Register a repository</h2>
          <p className="registration-intro">This calls the existing <code>POST /api/v1/projects</code> endpoint. No GitHub token is sent from your browser.</p>
          {registeredProject && (
            <div className="registered-project">
              <span><CheckCircle2 size={15} /> Registered in this session</span>
              <strong>{registeredProject.name}</strong>
              <small>{registeredProject.repo_url}</small>
              <code>ID: {registeredProject.id}</code>
            </div>
          )}
          <form className="registration-form" onSubmit={handleSubmit}>
            <label htmlFor="project-name">Project name</label>
            <input id="project-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Platform API" required maxLength={80} />
            <label htmlFor="repo-url">GitHub repository URL</label>
            <input id="repo-url" type="url" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/org/repository" pattern="https?://github\.com/.+" required />
            {error && <p className="form-feedback error-feedback" role="alert"><CircleAlert size={14} />{error}</p>}
            {success && <p className="form-feedback success-feedback" role="status"><CheckCircle2 size={14} />{success}</p>}
            <button className="primary-button" type="submit" disabled={isSubmitting}>
              <Plus size={15} /> {isSubmitting ? 'Registering…' : 'Register project'} <ArrowRight size={15} />
            </button>
          </form>
          <p className="registration-note">Backend storage is in-memory and may not survive a restart.</p>
        </section>
      </div>
    </div>
  );
}
