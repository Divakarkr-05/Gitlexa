import { FormEvent, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowUp, Bot, CircleHelp, Sparkles, X } from 'lucide-react';
import type { AnalysisResponse, EvidenceResult, ProjectResponse } from '../types';

type RepositoryIntent =
  | 'issues'
  | 'pull_requests'
  | 'commits'
  | 'workflows'
  | 'blockers'
  | 'dependencies'
  | 'progress'
  | 'metadata'
  | 'summary';

interface AssistantExperienceProps {
  onClose: () => void;
  analysisResult: AnalysisResponse | null;
  registeredProject: ProjectResponse | null;
  analysisError: string;
}

interface Message {
  id: number;
  role: 'assistant' | 'user';
  text: string;
}

const suggestions = [
  'Which issues are open in our repository?',
  'Why is our project blocked?',
  'Why did the latest GitHub Actions run fail?',
  'Summarize recent commits in our repository.',
];

const outOfScopeReply =
  "I'm Alexa+, Gitlexa's GitHub project assistant. I can help you investigate repository issues, pull requests, commits, workflow failures, and project blockers. Ask me something about your registered repository.";

function classifyRepositoryQuestion(prompt: string): RepositoryIntent | null {
  const normalized = prompt.toLowerCase().replace(/[’']/g, '');
  if (
    /\b(joke|funny|recipe|weather|sports|arithmetic|calculate|personal advice|dating advice)\b/.test(normalized)
    || /\bwhat is \d+\s*[+*/-]\s*\d+/.test(normalized)
    || /\bhow (do i|can i|to) (code|write|implement|build|learn)\b/.test(normalized)
    || /\b(explain|teach me) (python|javascript|typescript|programming|coding)\b/.test(normalized)
  ) return null;

  const hasRepositoryContext =
    /\b(our|this|registered|the)\s+(github\s+)?(repository|repo|project)\b/.test(normalized)
    || /\bgithub repository\b/.test(normalized);
  if (
    /\b(code|coding|program|programming|function|class|algorithm|script)\b/.test(normalized)
    && !hasRepositoryContext
    && !/\bgithub actions\b/.test(normalized)
  ) return null;
  const asksForData =
    /\b(which|what|list|show|summari[sz]e|latest|recent|open|closed|merged|failing|failed|failure|status|blocked|blocker|risk|progress|details|review|reviews|commit|commits|build|workflow|workflows|issue|issues|bug|bugs|pull request|pull requests|pr|prs|configuration|metadata|branch|language|visibility|stars|forks|dependencies)\b/.test(normalized);

  if (/\b(issue|issues|bug|bugs)\b/.test(normalized) && asksForData) return 'issues';
  if (/\b(pull request|pull requests|prs?|review|reviews|merge|merged)\b/.test(normalized) && asksForData) return 'pull_requests';
  if (/\b(commit|commits|code changes|recent changes|changes in the code)\b/.test(normalized) && asksForData) return 'commits';
  if (/\b(workflow|workflows|github actions|ci\/cd|ci|build|builds|run|runs)\b/.test(normalized) && asksForData) return 'workflows';
  if (/\b(dependency|dependencies)\b/.test(normalized) && hasRepositoryContext) return 'dependencies';
  if (/\b(progress|milestone|delivery)\b/.test(normalized) && hasRepositoryContext) return 'progress';
  if (/\b(blocked|blocker|blockers)\b/.test(normalized) && hasRepositoryContext) return 'blockers';
  if (/\b(risk|risks)\b/.test(normalized) && hasRepositoryContext) return 'blockers';
  if (/\b(metadata|configuration|configured|default branch|language|visibility|stars|forks|repository url|repo url|project info|repository info)\b/.test(normalized) && hasRepositoryContext) return 'metadata';
  if (/\b(summarize|summary|overview)\b/.test(normalized) && hasRepositoryContext) return 'summary';
  return null;
}

function unavailableResponse(result: AnalysisResponse, source: string): string {
  const availability = result.data_availability[source];
  if (!availability || !availability.toLowerCase().startsWith('available')) {
    return `I could not verify that information: GitHub ${source.replace('_', ' ')} data is unavailable in the current live analysis.`;
  }
  return '';
}

function describeEvidence(result: AnalysisResponse, items: EvidenceResult[]): string {
  const sourceLabel = 'LIVE GITHUB';
  if (!items.length) {
    return `${sourceLabel}: The relevant GitHub source was queried, but it returned no matching records. This does not prove information outside the queried data is absent.`;
  }
  return `${sourceLabel} evidence for ${result.repository}: ${items.map((item) =>
    `${item.title}${item.description ? ` — ${item.description}` : ''}${item.timestamp ? ` (observed ${new Date(item.timestamp).toLocaleString()})` : ''}${item.source_url ? ` [${item.source_url}]` : ''}`,
  ).join(' ')}`;
}

function getAnalysisResponse(
  prompt: string,
  result: AnalysisResponse | null,
  registeredProject: ProjectResponse | null,
  analysisError: string,
): string {
  const intent = classifyRepositoryQuestion(prompt);
  if (!intent) return outOfScopeReply;

  if (result?.simulated) {
    return 'This analysis result is not verified live GitHub data, so I cannot use it to answer repository questions. Run a live analysis first.';
  }

  if (!result) {
    if (analysisError) {
      return `The last live repository analysis could not be retrieved: ${analysisError} Retry the live analysis from the Analysis page.`;
    }
    return registeredProject
      ? `No live analysis result is available for registered project ${registeredProject.name} (${registeredProject.repo_url}). Run a live analysis to retrieve GitHub data. Registration alone does not verify repository details.`
      : 'No GitHub repository is registered or analyzed yet. Register a repository and run an analysis before asking me about its evidence.';
  }

  const sourceLabel = 'LIVE GITHUB';
  const issueQuestion = intent === 'issues';
  const pullQuestion = intent === 'pull_requests';
  const closedOrMerged = /\b(closed|merged|merge status|reviews?)\b/i.test(prompt);
  const category = issueQuestion ? 'issues'
    : pullQuestion ? 'pull_requests'
      : intent === 'commits' ? 'commits'
        : intent === 'workflows' ? 'workflow_runs'
          : '';

  if (closedOrMerged && (issueQuestion || pullQuestion)) {
    return `${sourceLabel}: Closed issues, merged pull requests, and review details were not retrieved by this analysis, so I cannot verify that information.`;
  }

  if (category) {
    const unavailable = unavailableResponse(result, category);
    if (unavailable) return unavailable;
    const evidenceType = issueQuestion ? 'issue'
      : pullQuestion ? 'pull_request'
        : intent === 'commits' ? 'commit'
          : 'ci_run';
    const items = result.evidence.filter((item) => item.type === evidenceType);
    if (intent === 'workflows' && /\b(latest|most recent)\b/i.test(prompt)) {
      const latest = items[0];
      return latest
        ? `${sourceLabel} latest workflow evidence for ${result.repository}: ${latest.title}. ${latest.description}${latest.source_url ? ` Source: ${latest.source_url}` : ''}`
        : `${sourceLabel}: GitHub Actions was queried, but no workflow run was returned; I cannot verify why a latest run failed.`;
    }
    return describeEvidence(result, items);
  }

  if (intent === 'blockers') {
    if (!result.blockers.length && !result.data_availability.workflow_runs?.toLowerCase().startsWith('available')) {
      return 'I could not verify project blockers because GitHub workflow data is unavailable in this analysis.';
    }
    return result.blockers.length
      ? `${sourceLabel} blockers for ${result.repository}: ${result.blockers.map((blocker) =>
        `${blocker.title}; severity ${blocker.severity}; confidence ${Math.round(blocker.confidence * 100)}%; impact: ${blocker.impact}; supporting evidence: ${blocker.evidence_ids.map((id) => result.evidence.find((item) => item.id === id)?.title ?? id).join(', ')}; recommended action: ${blocker.recommended_actions.join(' ')}`,
      ).join(' ')}`
      : `${sourceLabel}: The analysis identified no blockers in the evidence it retrieved. This does not establish that the repository has no other risks.`;
  }

  if (intent === 'dependencies') {
    return 'I could not verify project dependencies: dependency manifests or dependency-update data were not retrieved in this analysis.';
  }

  if (intent === 'progress') {
    return 'I could not verify project progress: milestones, project-board status, and delivery data were not retrieved in this analysis.';
  }

  if (intent === 'metadata') {
    if (result.repository_metadata) {
      const metadata = result.repository_metadata;
      return `${sourceLabel} metadata for ${metadata.full_name}: ${metadata.visibility} repository; default branch ${metadata.default_branch}; language ${metadata.language ?? 'not reported'}; ${metadata.stargazers_count} stars; ${metadata.forks_count} forks; updated ${metadata.updated_at ?? 'time not reported'}. ${metadata.html_url}`;
    }
    return registeredProject
      ? `The registered project is ${registeredProject.name} with URL ${registeredProject.repo_url}. Registration alone does not verify its GitHub metadata. Run a live analysis to retrieve it.`
      : 'Repository metadata could not be verified from the available analysis result.';
  }

  return `${sourceLabel} analysis for ${result.repository}: ${result.summary}`;
}

export default function AssistantExperience({
  onClose,
  analysisResult,
  registeredProject,
  analysisError,
}: AssistantExperienceProps) {
  const [messages, setMessages] = useState<Message[]>(() => [
    {
      id: 0,
      role: 'assistant',
      text: analysisResult && !analysisResult.simulated
        ? `LIVE GITHUB analysis context is ready for ${analysisResult.repository}. ${analysisResult.summary} I will answer only from this result.`
        : registeredProject
          ? `Repository assistant ready for registered project ${registeredProject.name}. Run a live analysis before asking about repository evidence.`
          : 'No GitHub repository is registered yet. Register one and run an analysis before asking about its evidence.',
    },
  ]);
  const [draft, setDraft] = useState('');
  const [processing, setProcessing] = useState(false);
  const messageId = useRef(1);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    headingRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [onClose]);

  function submitPrompt(prompt: string) {
    const trimmed = prompt.trim();
    if (!trimmed || processing) return;

    setMessages((current) => [...current, { id: messageId.current++, role: 'user', text: trimmed }]);
    setDraft('');
    setProcessing(true);
    timerRef.current = setTimeout(() => {
      setMessages((current) => [...current, {
        id: messageId.current++,
        role: 'assistant',
        text: getAnalysisResponse(trimmed, analysisResult, registeredProject, analysisError),
      }]);
      setProcessing(false);
      timerRef.current = null;
    }, 550);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitPrompt(draft);
  }

  return (
    <main className="assistant-experience">
      <div className="assistant-topline">
        <button className="assistant-back-button" type="button" onClick={onClose}>
          <ArrowLeft size={16} aria-hidden="true" /> <span>Back to workspace</span>
        </button>
        <span className="assistant-top-brand"><span className="assistant-brand-icon"><Sparkles size={15} aria-hidden="true" /></span> GITLEXA <span>/</span> ALEXA+</span>
        <span className="assistant-top-status"><i aria-hidden="true" /> {analysisResult ? (analysisResult.simulated ? 'NO VERIFIED DATA' : 'LIVE GITHUB CONTEXT') : analysisError ? 'RETRIEVAL FAILED' : 'NO ANALYSIS RESULT'}</span>
      </div>

      <div className="assistant-stage">
        <div className="assistant-stage-glow" aria-hidden="true" />
        <div className="assistant-intro">
          <div className="assistant-brand-lockup"><span className="assistant-lockup-spark"><Sparkles size={16} aria-hidden="true" /></span><span>GITLEXA <b>+</b></span></div>
          <h1 ref={headingRef} tabIndex={-1}>Your repository.<br /><span>In conversation.</span></h1>
          <p>Ask about the signals in your workspace.</p>
          <div className="assistant-grounding-pill"><span /> RULE-BASED <b>·</b> CURRENT LIVE EVIDENCE ONLY</div>
        </div>

        <div className="assistant-orb-wrap" aria-hidden="true">
          <div className={`assistant-orb ${processing ? 'is-processing' : ''}`}>
            <span className="orb-halo orb-halo-one" />
            <span className="orb-halo orb-halo-two" />
            <span className="orb-core"><span /><i /></span>
            <span className="orb-orbit"><i /><i /><i /></span>
            <span className="orb-wave orb-wave-one" />
            <span className="orb-wave orb-wave-two" />
          </div>
          <span className="orb-caption">GITLEXA ASSISTANT</span>
        </div>

        <section className="assistant-conversation" aria-label="Repository assistant conversation">
          <div className="conversation-head">
            <span className="conversation-label">CONVERSATION <span>·</span> {analysisResult ? analysisResult.repository : 'NO ANALYSIS RESULT'}</span>
            <span className={`assistant-status ${processing ? 'processing' : ''}`} role="status" aria-live="polite"><i /> {processing ? 'Thinking…' : 'Ready to help'}</span>
          </div>
          <div className="conversation-messages" aria-live="polite" aria-relevant="additions">
            {messages.map((message) => (
              <article className={`conversation-message ${message.role}`} key={message.id}>
                {message.role === 'assistant' && <span className="message-avatar"><Bot size={15} aria-hidden="true" /></span>}
                <div className="message-body">
                  <div className="message-meta">{message.role === 'assistant' ? 'GITLEXA ASSISTANT' : 'YOU'}{message.role === 'assistant' && <span className="simulated-label">{analysisResult && !analysisResult.simulated ? 'LIVE GITHUB GROUNDED' : 'NO VERIFIED DATA'}</span>}</div>
                  <p>{message.text}</p>
                </div>
              </article>
            ))}
            {processing && (
              <div className="processing-row" role="status"><span className="typing-indicator"><i /><i /><i /></span><span>Preparing a result-grounded response…</span></div>
            )}
          </div>
          <div className="suggested-prompts">
            <span className="suggested-label">TRY ASKING</span>
            <div className="suggestion-list">
              {suggestions.map((suggestion) => (
                <button type="button" key={suggestion} disabled={processing} onClick={() => submitPrompt(suggestion)}>
                  {suggestion}<ArrowUp size={12} aria-hidden="true" />
                </button>
              ))}
            </div>
          </div>
          <form className="assistant-composer" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="assistant-prompt">Ask Alexa+ about the registered GitHub repository</label>
            <input
              id="assistant-prompt"
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about your repository…"
              disabled={processing}
              autoComplete="off"
            />
            <button type="submit" disabled={processing || !draft.trim()} aria-label="Send message"><ArrowUp size={17} /></button>
          </form>
          <p className="assistant-grounding-footnote"><CircleHelp size={12} aria-hidden="true" /> Rule-based responses use only the latest successful live analysis. No generative AI service is connected.</p>
        </section>
      </div>
      <button className="assistant-exit-icon" type="button" onClick={onClose} aria-label="Close assistant"><X size={16} /></button>
    </main>
  );
}
