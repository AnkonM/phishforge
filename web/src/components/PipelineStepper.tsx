import { Check, Loader2, Minus, Wand2, X } from 'lucide-react'
import type { CSSProperties } from 'react'
import type { StageState, StageStatus } from '../lib/runReducer'

const STAGES: { key: keyof StageState; label: string }[] = [
  { key: 'generator', label: 'Generator' },
  { key: 'safety', label: 'Safety Gate' },
  { key: 'verifier', label: 'Verifier' },
  { key: 'scoring', label: 'Scoring' },
  { key: 'refinement', label: 'Refinement' },
]

function StatusIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case 'passed':
      return <Check size={14} aria-hidden />
    case 'failed':
      return <X size={14} aria-hidden />
    case 'running':
      return <Loader2 size={14} className="animate-spin motion-reduce:animate-none" aria-hidden />
    case 'skipped':
      return <Minus size={14} aria-hidden />
    default:
      return <Wand2 size={14} aria-hidden className="opacity-40" />
  }
}

function dotStyle(status: StageStatus): CSSProperties {
  switch (status) {
    case 'passed':
      return { background: 'var(--color-pass-bg)', color: 'var(--color-pass)', borderColor: 'var(--color-pass)' }
    case 'failed':
      return {
        background: 'var(--color-rejected-unsafe-bg)',
        color: 'var(--color-rejected-unsafe)',
        borderColor: 'var(--color-rejected-unsafe)',
      }
    case 'running':
      return { background: 'var(--color-surface)', color: 'var(--color-signal)', borderColor: 'var(--color-signal)' }
    case 'skipped':
      return {
        background: 'var(--color-surface)',
        color: 'var(--color-ink-muted)',
        borderColor: 'var(--color-border)',
      }
    default:
      return {
        background: 'var(--color-surface)',
        color: 'var(--color-ink-muted)',
        borderColor: 'var(--color-border)',
      }
  }
}

export function PipelineStepper({
  stages,
  currentIteration,
  maxIterations,
}: {
  stages: StageState
  currentIteration: number
  maxIterations: number
}) {
  return (
    <div role="group" aria-label="Pipeline stage progress">
      {currentIteration > 0 && (
        <p className="mb-3 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
          Iteration <span className="font-mono font-medium">{currentIteration}</span> of{' '}
          <span className="font-mono">{maxIterations}</span>
        </p>
      )}
      <ol className="flex items-stretch gap-0">
        {STAGES.map((s, idx) => {
          const status = stages[s.key]
          return (
            <li key={s.key} className="flex flex-1 items-center">
              <div className="flex flex-1 flex-col items-center gap-2 text-center">
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-full border-2 transition-colors duration-200 motion-reduce:transition-none"
                  style={dotStyle(status)}
                  aria-label={`${s.label}: ${status}`}
                >
                  <StatusIcon status={status} />
                </div>
                <span className="text-xs font-medium" style={{ color: 'var(--color-ink-secondary)' }}>
                  {s.label}
                </span>
                <span className="text-[11px] capitalize" style={{ color: 'var(--color-ink-muted)' }}>
                  {status}
                </span>
              </div>
              {idx < STAGES.length - 1 && (
                <div
                  className="mx-1 mb-6 h-0.5 flex-1"
                  style={{
                    background:
                      status === 'passed' || status === 'failed' || status === 'skipped'
                        ? 'var(--color-border-strong)'
                        : 'var(--color-border)',
                  }}
                  aria-hidden
                />
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
