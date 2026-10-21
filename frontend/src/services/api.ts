export interface HealthResponse {
  status: string;
  service?: string;
  version?: string;
}

export interface AuthStatusResponse {
  authenticated: boolean;
  provider: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
export const API_BASE_URL = (configuredBaseUrl || '/api/v1').replace(/\/+$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  const headers = new Headers(init?.headers);
  headers.set('Accept', 'application/json');
  if (init?.body) headers.set('Content-Type', 'application/json');
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : 'Network request failed';
    throw new ApiError(`Could not reach the Gitlexa API: ${reason}`);
  }

  const contentType = response.headers.get('content-type') ?? '';
  const payload: unknown = contentType.includes('application/json')
    ? await response.json().catch(() => null)
    : null;

  if (!response.ok) {
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload
      && typeof payload.detail === 'string'
      ? payload.detail
      : `Request failed with status ${response.status}`;
    throw new ApiError(detail, response.status);
  }

  if (payload === null) {
    throw new ApiError('The API returned an empty or invalid JSON response', response.status);
  }

  return payload as T;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export function fetchAuthStatus(): Promise<AuthStatusResponse> {
  return request<AuthStatusResponse>('/auth/status');
}

export function postJson<TResponse, TRequest>(path: string, body: TRequest): Promise<TResponse> {
  return request<TResponse>(path, { method: 'POST', body: JSON.stringify(body) });
}
