import type { Condition, TargetRole, TerminalState } from './types'

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return '—'
  return score.toFixed(1)
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelativeShort(iso: string): string {
  const d = new Date(iso)
  const diffMs = Date.now() - d.getTime()
  const sec = Math.round(diffMs / 1000)
  if (sec < 60) return `${sec}s ago`
  const min = Math.round(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.round(min / 60)
  if (hr < 24) return `${hr}h ago`
  const day = Math.round(hr / 24)
  return `${day}d ago`
}

const ROLE_LABELS: Record<TargetRole, string> = {
  finance: 'Finance',
  hr: 'HR',
  it: 'IT',
  sales: 'Sales',
  operations: 'Operations',
  executive: 'Executive',
}

export function formatRole(role: TargetRole | string): string {
  return ROLE_LABELS[role as TargetRole] ?? role
}

export function formatScenarioType(scenarioType: string): string {
  return scenarioType
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function formatCondition(condition: Condition | string): string {
  switch (condition) {
    case 'verifier_guided':
      return 'Verifier-guided'
    case 'baseline_direct':
      return 'Direct baseline'
    case 'baseline_static':
      return 'Baseline (static)'
    default:
      return condition
  }
}

const DIFFICULTY_LABELS: Record<number, string> = {
  1: 'Obvious',
  2: 'Moderate',
  3: 'Advanced',
  4: 'Expert',
}

export function formatDifficulty(level: number): string {
  return `${level} · ${DIFFICULTY_LABELS[level] ?? ''}`
}

export interface TerminalStateInfo {
  label: string
  description: string
}

export const TERMINAL_STATE_INFO: Record<string, TerminalStateInfo> = {
  PASS: { label: 'Pass', description: 'Converged: quality score reached the pass threshold.' },
  REVISE: { label: 'Revise', description: 'Below the pass threshold; refinement continues.' },
  FAIL: { label: 'Fail', description: 'Below the revise floor.' },
  REJECTED_UNSAFE: {
    label: 'Rejected (unsafe)',
    description: 'The deterministic safety gate blocked this simulation before scoring.',
  },
  GENERATION_FAILURE: {
    label: 'Generation failed',
    description: 'The generator could not produce valid output after its retry budget.',
  },
  FAILED_TO_CONVERGE: {
    label: 'Failed to converge',
    description: 'Did not reach the pass threshold within the iteration ceiling.',
  },
  GENERATED_UNVERIFIED: {
    label: 'Generated (unverified)',
    description: 'Single-shot baseline output, not run through the in-loop safety/verifier gate.',
  },
  CANCELLED: { label: 'Cancelled', description: 'Cancelled by request before reaching a terminal state.' },
  ERROR: { label: 'Error', description: 'An unexpected error interrupted the run.' },
}

export function terminalStateInfo(state: TerminalState | string): TerminalStateInfo {
  return TERMINAL_STATE_INFO[state] ?? { label: state, description: '' }
}
