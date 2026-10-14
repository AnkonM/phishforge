// Mirrors server/models.py and the core pipeline schemas (models/schemas/*.py).
// Kept hand-written (not generated) per docs/API.md, which is the source of truth.

export type TargetRole = 'finance' | 'hr' | 'it' | 'sales' | 'operations' | 'executive'
export type Difficulty = 1 | 2 | 3 | 4
export type TerminalState =
  | 'PASS'
  | 'FAILED_TO_CONVERGE'
  | 'REJECTED_UNSAFE'
  | 'GENERATION_FAILURE'
  | 'GENERATED_UNVERIFIED'
export type Condition = 'baseline_static' | 'baseline_direct' | 'verifier_guided'
export type RunMode = 'guided' | 'direct' | 'compare'
export type ProviderMode = 'live' | 'demo'
export type DemoScriptName = 'first_pass' | 'revise_pass' | 'safety_reject' | 'plateau'
export type PassFailBand = 'PASS' | 'REVISE' | 'FAIL'
export type TerminationReason = 'PASS' | 'MAX_ITERATIONS' | 'NO_IMPROVEMENT' | 'SAFETY_FAIL'

export interface ScenarioSpecification {
  scenario_id?: string
  organization_context: string
  target_role: TargetRole
  scenario_type: string
  difficulty: Difficulty
  language: string
  desired_indicators: string[]
  prohibited_elements: string[]
  simulation_constraints: Record<string, unknown>
}

export interface GeneratedSimulation {
  generation_id: string
  scenario_id: string
  subject: string
  sender: string
  body: string
  metadata: Record<string, unknown>
  intended_indicators: string[]
  model: string
  prompt_version: string
  timestamp: string
}

export interface SafetyCheckResult {
  passed: boolean
  status: 'PASS' | 'FAIL'
  findings: string[]
}

export interface VerificationResult {
  verification_id: string
  generation_id: string
  realism_score: number
  relevance_score: number
  difficulty_score: number
  indicator_score: number
  language_score: number
  safety_status: 'PASS' | 'FAIL'
  safety_findings: string[]
  semantic_findings: string[]
  overall_score: number
  pass_fail: PassFailBand
  verifier_version: string
}

export interface RefinementResult {
  iteration_number: number
  prior_score: number | null
  weaknesses: string[]
  revision_instructions: string
  new_score: number | null
  score_delta: number | null
  termination_reason: TerminationReason | null
}

export interface IterationRecord {
  iteration_number: number
  simulation: GeneratedSimulation | null
  safety_result: SafetyCheckResult | null
  verification: VerificationResult | null
  score: number | null
  refinement: RefinementResult | null
}

export interface RunRecord {
  run_id: string
  scenario: ScenarioSpecification
  condition: Condition
  iterations: IterationRecord[]
  terminal_state: TerminalState
  created_at: string
}

export interface RunSummary {
  run_id: string
  created_at: string
  target_role: TargetRole
  scenario_type: string
  difficulty: Difficulty
  condition: Condition
  terminal_state: TerminalState
  final_score: number | null
  iteration_count: number
  compare_group_id: string | null
  imported: boolean
}

export interface RunDetailResponse {
  record: RunRecord
  compare_group_id: string | null
  imported: boolean
}

export interface HealthResponse {
  status: 'ok'
  mode: ProviderMode
  key_configured: boolean
}

export interface SafetyRuleInfo {
  name: string
  description: string
}

export interface DifficultyLevelInfo {
  level: Difficulty
  label: string
  description: string
}

export interface ConfigResponse {
  scoring_weights: Record<string, number>
  pass_threshold: number
  revise_threshold: number
  max_iterations: number
  improvement_epsilon: number
  improvement_patience: number
  supported_roles: TargetRole[]
  supported_scenario_types: string[]
  safety_rules: SafetyRuleInfo[]
  difficulty_rubric: DifficultyLevelInfo[]
  model_name: string
}

export interface ReachabilityResponse {
  reachable: boolean
  detail: string
}

export interface CreateRunResponse {
  run_id: string | null
  compare_group_id: string | null
  run_ids: string[] | null
}

export interface StatsCondBreakdown {
  leaked: number
  total: number
  rate_pct: number
}

export interface StatsResponse {
  total_runs: number
  pass_rate_pct: number
  rejected_unsafe_rate_pct: number
  mean_iterations: number
  mean_final_score: number
  terminal_state_distribution: Record<string, Record<string, number>>
  safety_leakage: Record<string, StatsCondBreakdown>
  quality_by_condition: Record<
    string,
    { realism_score: number; relevance_score: number; indicator_score: number; difficulty_score: number; language_score: number }
  >
  score_histogram: { bucket: string; count: number }[]
  iterations_histogram: { iterations: number; count: number }[]
  by_role: Record<string, { mean_score: number; pass_rate_pct: number; total: number }>
  by_difficulty: Record<string, { mean_score: number; pass_rate_pct: number; total: number }>
  n_note: string
}

export interface BenchmarkCreateResponse {
  benchmark_id: string
}

// --- SSE event schema (docs/API.md) ---

interface BaseEvent {
  run_id: string
  ts: string
  iteration?: number
}

export interface RunStartedEvent extends BaseEvent {
  event: 'run_started'
  condition: Condition
  demo_script: DemoScriptName | null
}
export interface IterationStartedEvent extends BaseEvent {
  event: 'iteration_started'
}
export interface GenerationStartedEvent extends BaseEvent {
  event: 'generation_started'
}
export interface GenerationCompleteEvent extends BaseEvent {
  event: 'generation_complete'
  simulation: GeneratedSimulation
}
export interface SafetyResultEvent extends BaseEvent {
  event: 'safety_result'
  result: SafetyCheckResult
}
export interface VerificationResultEvent extends BaseEvent {
  event: 'verification_result'
  result: VerificationResult
}
export interface ScoreResultEvent extends BaseEvent {
  event: 'score_result'
  overall_score: number
  pass_fail: PassFailBand
  result: VerificationResult
}
export interface RefinementInstructionEvent extends BaseEvent {
  event: 'refinement_instruction'
  instructions: string
  weaknesses: string[]
}
export interface IterationStatusEvent extends BaseEvent {
  event: 'iteration_status'
  status: 'GENERATED_UNVERIFIED' | 'GENERATION_FAILURE' | 'REJECTED_UNSAFE' | 'PASS' | 'FAILED_TO_CONVERGE' | 'REVISE'
}
export interface RunFinishedEvent extends BaseEvent {
  event: 'run_finished'
  terminal_state: TerminalState | 'CANCELLED' | 'ERROR'
  cancelled: boolean
  record?: RunRecord
}
export interface ErrorEvent extends BaseEvent {
  event: 'error'
  stage: string
  message: string
}

export type RunEvent =
  | RunStartedEvent
  | IterationStartedEvent
  | GenerationStartedEvent
  | GenerationCompleteEvent
  | SafetyResultEvent
  | VerificationResultEvent
  | ScoreResultEvent
  | RefinementInstructionEvent
  | IterationStatusEvent
  | RunFinishedEvent
  | ErrorEvent

export interface BenchmarkStartedEvent {
  event: 'benchmark_started'
  benchmark_id: string
  ts: string
  total: number
  mode: ProviderMode
}
export interface ScenarioStartedEvent {
  event: 'scenario_started'
  benchmark_id: string
  ts: string
  index: number
  total: number
  scenario_id: string
  condition: Condition
}
export interface ScenarioFinishedEvent {
  event: 'scenario_finished'
  benchmark_id: string
  ts: string
  index: number
  total: number
  scenario_id: string
  condition: Condition
  run_id: string
  terminal_state: TerminalState
  score: number | null
}
export interface ScenarioErrorEvent {
  event: 'scenario_error'
  benchmark_id: string
  ts: string
  index?: number
  scenario_id: string
  condition: Condition
  message: string
}
export interface BenchmarkFinishedEvent {
  event: 'benchmark_finished'
  benchmark_id: string
  ts: string
}

export type BenchmarkEvent =
  | BenchmarkStartedEvent
  | ScenarioStartedEvent
  | ScenarioFinishedEvent
  | ScenarioErrorEvent
  | BenchmarkFinishedEvent
