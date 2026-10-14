import { AlertTriangle, Ban, CheckCircle2, Clock, RotateCw, ServerCrash, ShieldAlert, XCircle, type LucideIcon } from 'lucide-react'
import { terminalStateInfo } from '../lib/format'

const ICONS: Record<string, LucideIcon> = {
  PASS: CheckCircle2,
  REVISE: RotateCw,
  FAIL: XCircle,
  REJECTED_UNSAFE: ShieldAlert,
  GENERATION_FAILURE: ServerCrash,
  FAILED_TO_CONVERGE: Clock,
  GENERATED_UNVERIFIED: AlertTriangle,
  CANCELLED: Ban,
  ERROR: AlertTriangle,
}

const COLOR_VARS: Record<string, string> = {
  PASS: 'pass',
  REVISE: 'revise',
  FAIL: 'fail',
  REJECTED_UNSAFE: 'rejected-unsafe',
  GENERATION_FAILURE: 'generation-failure',
  FAILED_TO_CONVERGE: 'failed-to-converge',
  GENERATED_UNVERIFIED: 'revise',
  CANCELLED: 'generation-failure',
  ERROR: 'rejected-unsafe',
}

export function StateBadge({ state, size = 'md' }: { state: string; size?: 'sm' | 'md' }) {
  const Icon = ICONS[state] ?? AlertTriangle
  const colorKey = COLOR_VARS[state] ?? 'revise'
  const info = terminalStateInfo(state)
  const pad = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${pad}`}
      style={{
        color: `var(--color-${colorKey})`,
        backgroundColor: `var(--color-${colorKey}-bg)`,
      }}
      title={info.description}
    >
      <Icon size={size === 'sm' ? 12 : 14} aria-hidden />
      <span>{info.label}</span>
    </span>
  )
}
