export interface ProjectCreate {
  name: string;
  repo_url: string;
}

export interface ProjectResponse extends ProjectCreate {
  id: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  project_id: string;
  repository: string;
  status: 'completed';
  source: 'demo' | 'live';
  simulated: boolean;
  analyzed_at: string;
  repository_metadata: RepositoryMetadata | null;
  data_availability: Record<string, string>;
  summary: string;
  blockers: BlockerResult[];
  evidence: EvidenceResult[];
  correlations: CorrelationResult[];
}

export type EvidenceType = 'issue' | 'pull_request' | 'ci_run' | 'commit' | 'code' | 'log';

export interface EvidenceResult {
  id: string;
  type: EvidenceType;
  title: string;
  description: string;
  source_url: string | null;
  source_ref: string | null;
  timestamp: string | null;
  score: number;
  simulated: boolean;
}

export interface RepositoryMetadata {
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  visibility: string;
  language: string | null;
  default_branch: string;
  is_fork: boolean;
  is_archived: boolean;
  stargazers_count: number;
  forks_count: number;
  open_issues_count: number;
  created_at: string | null;
  updated_at: string | null;
  pushed_at: string | null;
}

export interface BlockerResult {
  id: string;
  title: string;
  explanation: string;
  impact: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  confidence: number;
  evidence_ids: string[];
  recommended_actions: string[];
}

export interface CorrelationResult {
  id: string;
  evidence_ids: string[];
  relationship: string;
  explanation: string;
  confidence: number;
}
