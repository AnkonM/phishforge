import type { IterationViewData } from '../lib/runReducer'

const DIMENSIONS: { key: 'realism_score' | 'relevance_score' | 'indicator_score' | 'difficulty_score' | 'language_score'; label: string }[] = [
  { key: 'realism_score', label: 'Realism' },
  { key: 'relevance_score', label: 'Role relevance' },
  { key: 'indicator_score', label: 'Indicator coverage' },
  { key: 'difficulty_score', label: 'Difficulty match' },
  { key: 'language_score', label: 'Language quality' },
]

/** Small multiples: one mini bar group per iteration, each dimension shown
 * as a bar with a delta label vs. the previous iteration. */
export function DimensionBreakdown({ iterations }: { iterations: IterationViewData[] }) {
  if (iterations.length === 0) return null

  return (
    <div>
      <h4 className="mb-3 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
        Dimension breakdown by iteration
      </h4>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {iterations.map((it, idx) => {
          const prev = idx > 0 ? iterations[idx - 1] : null
          const v = it.verification
          if (!v) return null
          return (
            <div
              key={it.iteration_number}
              className="rounded-[var(--radius-md)] border p-3"
              style={{ borderColor: 'var(--color-border)' }}
            >
              <p className="mb-2 text-xs font-medium" style={{ color: 'var(--color-ink-secondary)' }}>
                Iteration {it.iteration_number}
              </p>
              <div className="space-y-1.5">
                {DIMENSIONS.map((d) => {
                  const value = v[d.key]
                  const prevValue = prev?.verification?.[d.key]
                  const delta = prevValue !== undefined && prevValue !== null ? value - prevValue : null
                  return (
                    <div key={d.key} className="flex items-center gap-2 text-xs">
                      <span className="w-28 shrink-0 truncate" style={{ color: 'var(--color-ink-muted)' }}>
                        {d.label}
                      </span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: 'var(--color-border)' }}>
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: 'var(--color-signal)' }}
                        />
                      </div>
                      <span className="w-10 shrink-0 text-right font-mono" style={{ color: 'var(--color-ink)' }}>
                        {value.toFixed(0)}
                      </span>
                      {delta !== null && (
                        <span
                          className="w-10 shrink-0 text-right font-mono text-[11px]"
                          style={{ color: delta >= 0 ? 'var(--color-pass)' : 'var(--color-rejected-unsafe)' }}
                        >
                          {delta >= 0 ? '+' : ''}
                          {delta.toFixed(0)}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
