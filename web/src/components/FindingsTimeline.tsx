import type { IterationViewData } from '../lib/runReducer'

export function FindingsTimeline({ iterations }: { iterations: IterationViewData[] }) {
  const withFindings = iterations.filter((it) => it.weaknesses.length > 0 || it.revision_instructions)
  if (withFindings.length === 0) return null

  return (
    <div>
      <h4 className="mb-3 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
        Findings &amp; refinement timeline
      </h4>
      <ol className="space-y-4 border-l pl-4" style={{ borderColor: 'var(--color-border)' }}>
        {withFindings.map((it) => (
          <li key={it.iteration_number} className="relative">
            <span
              className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full"
              style={{ background: 'var(--color-signal)' }}
              aria-hidden
            />
            <p className="text-sm font-medium" style={{ color: 'var(--color-ink)' }}>
              Iteration {it.iteration_number}
            </p>
            {it.weaknesses.length > 0 && (
              <ul className="mt-1 space-y-1 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
                {it.weaknesses.map((w, i) => (
                  <li key={i} className="flex gap-2">
                    <span aria-hidden>·</span>
                    <span>{w}</span>
                  </li>
                ))}
              </ul>
            )}
            {it.revision_instructions && (
              <p
                className="mt-2 rounded-[var(--radius-sm)] p-2 text-xs"
                style={{ background: 'var(--color-page)', color: 'var(--color-ink-secondary)' }}
              >
                <span className="font-medium" style={{ color: 'var(--color-ink-muted)' }}>
                  Sent back to generator:{' '}
                </span>
                {it.revision_instructions}
              </p>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}
