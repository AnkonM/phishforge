import type { RunMode } from '../lib/types'

const OPTIONS: { value: RunMode; label: string; hint: string }[] = [
  { value: 'guided', label: 'Verifier-guided', hint: 'Full closed-loop pipeline' },
  { value: 'direct', label: 'Direct baseline', hint: 'Single-shot (post-hoc checked)' },
  { value: 'compare', label: 'Compare', hint: 'Both, side by side' },
]

export function ModeSwitch({ value, onChange }: { value: RunMode; onChange: (mode: RunMode) => void }) {
  return (
    <div
      role="radiogroup"
      aria-label="Run mode"
      className="inline-flex rounded-[var(--radius-md)] border p-1"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-page)' }}
    >
      {OPTIONS.map((opt) => {
        const active = value === opt.value
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className="rounded-[var(--radius-sm)] px-3 py-1.5 text-sm font-medium transition-colors"
            style={
              active
                ? { background: 'var(--color-surface)', color: 'var(--color-signal)', boxShadow: '0 1px 2px rgba(0,0,0,0.08)' }
                : { color: 'var(--color-ink-secondary)' }
            }
            title={opt.hint}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
