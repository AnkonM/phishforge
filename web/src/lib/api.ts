import type {
  BenchmarkCreateResponse,
  ConfigResponse,
  CreateRunResponse,
  DemoScriptName,
  HealthResponse,
  ProviderMode,
  ReachabilityResponse,
  RunDetailResponse,
  RunMode,
  RunSummary,
  ScenarioSpecification,
  StatsResponse,
} from './types'

const BASE = '/api'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      // body wasn't JSON; fall back to statusText
    }
    throw new ApiError(resp.status, detail)
  }
  if (resp.status === 204) return undefined as T
  return resp.json() as Promise<T>
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  setMode: (mode: ProviderMode) =>
    request<HealthResponse>('/health/mode', { method: 'PUT', body: JSON.stringify({ mode }) }),
  reachability: () => request<ReachabilityResponse>('/health/reachability', { method: 'POST' }),
  config: () => request<ConfigResponse>('/config'),
  presets: () => request<ScenarioSpecification[]>('/presets'),

  createRun: (spec: ScenarioSpecification, mode: RunMode, demo_script?: DemoScriptName | null) =>
    request<CreateRunResponse>('/runs', {
      method: 'POST',
      body: JSON.stringify({ spec, mode, demo_script: demo_script ?? null }),
    }),
  listRuns: (filters?: { state?: string; role?: string; difficulty?: number; mode?: string; q?: string }) => {
    const params = new URLSearchParams()
    if (filters) {
      for (const [k, v] of Object.entries(filters)) {
        if (v !== undefined && v !== '') params.set(k, String(v))
      }
    }
    const qs = params.toString()
    return request<RunSummary[]>(`/runs${qs ? `?${qs}` : ''}`)
  },
  getRun: (runId: string) => request<RunDetailResponse>(`/runs/${runId}`),
  deleteRun: (runId: string) => request<void>(`/runs/${runId}`, { method: 'DELETE' }),
  cancelRun: (runId: string) => request<{ cancelled: boolean }>(`/runs/${runId}/cancel`, { method: 'POST' }),

  stats: () => request<StatsResponse>('/stats'),

  createBenchmark: (mode: ProviderMode) =>
    request<BenchmarkCreateResponse>('/benchmark', { method: 'POST', body: JSON.stringify({ mode }) }),
}

export { ApiError }
