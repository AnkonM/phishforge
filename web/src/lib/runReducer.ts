import type {
  Condition,
  DemoScriptName,
  GeneratedSimulation,
  PassFailBand,
  RefinementResult,
  RunEvent,
  RunRecord,
  SafetyCheckResult,
  TerminalState,
  VerificationResult,
} from './types'

export type StageStatus = 'idle' | 'running' | 'passed' | 'failed' | 'skipped'

export interface StageState {
  generator: StageStatus
  safety: StageStatus
  verifier: StageStatus
  scoring: StageStatus
  refinement: StageStatus
}

export interface IterationViewData {
  iteration_number: number
  simulation: GeneratedSimulation | null
  safety_result: SafetyCheckResult | null
  verification: VerificationResult | null
  score: number | null
  pass_fail: PassFailBand | null
  revision_instructions: string | null
  weaknesses: string[]
  status: string | null
  termination_reason: RefinementResult['termination_reason']
}

export interface RunErrorEntry {
  stage: string
  message: string
  iteration?: number
}

export interface RunViewState {
  runId: string | null
  condition: Condition | null
  demoScript: DemoScriptName | null
  currentIteration: number
  stages: StageState
  iterations: IterationViewData[]
  terminalState: TerminalState | 'CANCELLED' | 'ERROR' | null
  cancelled: boolean
  record: RunRecord | null
  errors: RunErrorEntry[]
  finished: boolean
}

const idleStages: StageState = {
  generator: 'idle',
  safety: 'idle',
  verifier: 'idle',
  scoring: 'idle',
  refinement: 'idle',
}

export const initialRunViewState: RunViewState = {
  runId: null,
  condition: null,
  demoScript: null,
  currentIteration: 0,
  stages: { ...idleStages },
  iterations: [],
  terminalState: null,
  cancelled: false,
  record: null,
  errors: [],
  finished: false,
}

function ensureIteration(state: RunViewState, n: number): IterationViewData[] {
  if (state.iterations.some((it) => it.iteration_number === n)) return state.iterations
  return [
    ...state.iterations,
    {
      iteration_number: n,
      simulation: null,
      safety_result: null,
      verification: null,
      score: null,
      pass_fail: null,
      revision_instructions: null,
      weaknesses: [],
      status: null,
      termination_reason: null,
    },
  ]
}

function updateIteration(
  iterations: IterationViewData[],
  n: number,
  patch: Partial<IterationViewData>,
): IterationViewData[] {
  return iterations.map((it) => (it.iteration_number === n ? { ...it, ...patch } : it))
}

export function runEventReducer(state: RunViewState, event: RunEvent): RunViewState {
  switch (event.event) {
    case 'run_started':
      return {
        ...initialRunViewState,
        runId: event.run_id,
        condition: event.condition,
        demoScript: event.demo_script,
      }

    case 'iteration_started': {
      const n = event.iteration ?? state.currentIteration + 1
      return {
        ...state,
        currentIteration: n,
        stages: { ...idleStages, generator: 'running' },
        iterations: ensureIteration(state, n),
      }
    }

    case 'generation_started':
      return { ...state, stages: { ...state.stages, generator: 'running' } }

    case 'generation_complete': {
      const n = event.iteration ?? state.currentIteration
      return {
        ...state,
        stages: { ...state.stages, generator: 'passed', safety: 'running' },
        iterations: updateIteration(ensureIteration(state, n), n, { simulation: event.simulation }),
      }
    }

    case 'safety_result': {
      const n = event.iteration ?? state.currentIteration
      const passed = event.result.passed
      return {
        ...state,
        stages: {
          ...state.stages,
          safety: passed ? 'passed' : 'failed',
          verifier: passed ? 'running' : 'skipped',
          scoring: passed ? 'idle' : 'skipped',
          refinement: passed ? 'idle' : 'skipped',
        },
        iterations: updateIteration(ensureIteration(state, n), n, { safety_result: event.result }),
      }
    }

    case 'verification_result': {
      const n = event.iteration ?? state.currentIteration
      return {
        ...state,
        stages: { ...state.stages, verifier: 'passed', scoring: 'running' },
        iterations: updateIteration(ensureIteration(state, n), n, { verification: event.result }),
      }
    }

    case 'score_result': {
      const n = event.iteration ?? state.currentIteration
      return {
        ...state,
        stages: { ...state.stages, scoring: 'passed', refinement: 'running' },
        iterations: updateIteration(ensureIteration(state, n), n, {
          score: event.overall_score,
          pass_fail: event.pass_fail,
          verification: event.result,
        }),
      }
    }

    case 'refinement_instruction': {
      const n = event.iteration ?? state.currentIteration
      return {
        ...state,
        stages: { ...state.stages, refinement: 'passed' },
        iterations: updateIteration(ensureIteration(state, n), n, {
          revision_instructions: event.instructions,
          weaknesses: event.weaknesses,
        }),
      }
    }

    case 'iteration_status': {
      const n = event.iteration ?? state.currentIteration
      return {
        ...state,
        iterations: updateIteration(ensureIteration(state, n), n, { status: event.status }),
      }
    }

    case 'run_finished': {
      const lastN = state.currentIteration
      let stages = state.stages
      if (event.terminal_state === 'GENERATION_FAILURE') {
        stages = { ...idleStages, generator: 'failed' }
      } else if (event.terminal_state === 'PASS') {
        stages = { generator: 'passed', safety: 'passed', verifier: 'passed', scoring: 'passed', refinement: 'passed' }
      }
      const record = event.record ?? null
      const termination_reason = record?.iterations[record.iterations.length - 1]?.refinement?.termination_reason ?? null
      return {
        ...state,
        stages,
        terminalState: event.terminal_state,
        cancelled: event.cancelled,
        record,
        finished: true,
        iterations:
          termination_reason && lastN
            ? updateIteration(state.iterations, lastN, { termination_reason })
            : state.iterations,
      }
    }

    case 'error': {
      const n = event.iteration ?? state.currentIteration
      const stages =
        event.stage === 'generation' ? { ...idleStages, generator: 'failed' as StageStatus } : state.stages
      return {
        ...state,
        stages,
        errors: [...state.errors, { stage: event.stage, message: event.message, iteration: n }],
      }
    }

    default:
      return state
  }
}

/** Builds the same RunViewState shape directly from a stored RunRecord, so
 * RunDetail (static) can share every component with Studio (live) without
 * replaying an event stream. */
export function buildViewStateFromRecord(record: RunRecord): RunViewState {
  const iterations: IterationViewData[] = record.iterations.map((it) => ({
    iteration_number: it.iteration_number,
    simulation: it.simulation,
    safety_result: it.safety_result,
    verification: it.verification,
    score: it.score,
    pass_fail: it.verification?.pass_fail ?? null,
    revision_instructions: it.refinement?.revision_instructions ?? null,
    weaknesses: it.refinement?.weaknesses ?? [],
    status: null,
    termination_reason: it.refinement?.termination_reason ?? null,
  }))

  let stages: StageState = { ...idleStages }
  if (record.terminal_state === 'GENERATION_FAILURE') {
    stages = { ...idleStages, generator: 'failed' }
  } else if (record.terminal_state === 'REJECTED_UNSAFE') {
    stages = { generator: 'passed', safety: 'failed', verifier: 'skipped', scoring: 'skipped', refinement: 'skipped' }
  } else if (record.terminal_state === 'PASS' || record.terminal_state === 'FAILED_TO_CONVERGE') {
    stages = { generator: 'passed', safety: 'passed', verifier: 'passed', scoring: 'passed', refinement: 'passed' }
  } else if (record.terminal_state === 'GENERATED_UNVERIFIED') {
    const last = iterations[iterations.length - 1]
    stages = {
      generator: 'passed',
      safety: last?.safety_result ? (last.safety_result.passed ? 'passed' : 'failed') : 'idle',
      verifier: last?.verification ? 'passed' : 'idle',
      scoring: last?.score !== null && last?.score !== undefined ? 'passed' : 'idle',
      refinement: 'idle',
    }
  }

  return {
    runId: record.run_id,
    condition: record.condition,
    demoScript: null,
    currentIteration: iterations[iterations.length - 1]?.iteration_number ?? 0,
    stages,
    iterations,
    terminalState: record.terminal_state,
    cancelled: false,
    record,
    errors: [],
    finished: true,
  }
}
