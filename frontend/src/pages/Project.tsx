import { FormEvent, useState } from 'react';
import { ArrowRight, CheckCircle2, CircleAlert, Github, Layers3, Plus, ShieldCheck } from 'lucide-react';
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
        <div><div className="eyebrow"><span className="eyebrow-line" /> REPOSITORY PROFILE</div><h1>Project <span>space.</span></h1><p>Register a repository with the backend to queue an analysis.</p></div>
        <span className="outline-chip"><Layers3 size={13} /> BACKEND PROJECTS</span>
      </section>

      <div className="project-content-grid">
        <section className="panel project-profile-panel">
          <div className="panel-kicker"><span className="panel-kicker-line" /> DEMO REPOSITORY</div>
          <div className="project-profile">
            <span className="project-profile-icon"><Github size={22} /></span>
            <div><h2>northstar / platform-api</h2><p>Sample repository · Not connected to GitHub</p></div>
            <span className="demo-tag">DEMO</span>
          </div>
          <div className="project-profile-facts">
            <div><span>PRIMARY BRANCH</span><strong><i className="language-dot" /> main</strong></div>
            <div><span>LANGUAGE</span><strong><i className="language-dot" /> TypeScript</strong></div>
            <div><span>TELEMETRY</span><strong><CircleAlert size={14} /> Sample only</strong></div>
          </div>
          <div className="project-callout"><ShieldCheck size={15} /><p>Live repository telemetry is unavailable because this frontend has no verified telemetry read endpoint.</p></div>
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
