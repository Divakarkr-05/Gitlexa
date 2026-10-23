import { postJson } from './api';
import type { ProjectCreate, ProjectResponse } from '../types';

export function createProject(project: ProjectCreate): Promise<ProjectResponse> {
  return postJson<ProjectResponse, ProjectCreate>('/projects', project);
}
