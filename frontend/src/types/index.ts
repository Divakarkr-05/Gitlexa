export interface ProjectCreate {
  name: string;
  repo_url: string;
}

export interface ProjectResponse extends ProjectCreate {
  id: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  project_id: string;
}
