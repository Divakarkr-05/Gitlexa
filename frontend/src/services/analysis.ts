import { postJson } from './api';
import type { AnalysisResponse } from '../types';

export function runAnalysis(projectId: string): Promise<AnalysisResponse> {
  return postJson<AnalysisResponse, { project_id: string; mode: 'live' }>(
    '/analysis/run',
    { project_id: projectId, mode: 'live' },
  );
}
