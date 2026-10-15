import { useState } from 'react'
import { wordDiff } from '../lib/diff'
import type { IterationViewData } from '../lib/runReducer'

function DiffText({ before, after }: { before: string; after: string }) {
  const tokens = wordDiff(before, after)
  return (
    <p className="whitespace-pre-wrap text-sm leading-relaxed">
      {tokens.map((t, i) => {
        if (t.type === 'unchanged') return <span key={i}>{t.text}</span>
        const style =
          t.type === 'added'
            ? { background: 'var(--color-pass-bg)', color: 'var(--color-pass)' }
            : { background: 'var(--color-rejected-unsafe-bg)', color: 'var(--color-rejected-unsafe)', textDecoration: 'line-through' }
        return (
          <mark key={i} className="rounded px-0.5" style={style}>
            {t.text}
          </mark>
        )
      })}
    </p>
  )
}

export function DiffView({ iterations }: { iterations: IterationViewData[] }) {
  const withSim = iterations.filter((it) => it.simulation)
  const [fromN, setFromN] = useState(withSim[0]?.iteration_number)
  const [toN, setToN] = useState(withSim[withSim.length - 1]?.iteration_number)

  if (withSim.length < 2) {
    return (
      <p className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>
        Need at least two generated iterations to diff.
      </p>
    )
  }

  const from = withSim.find((it) => it.iteration_number === fromN) ?? withSim[0]
  const to = withSim.find((it) => it.iteration_number === toN) ?? withSim[withSim.length - 1]

  return (
    <div>
      <div className="mb-3 flex items-center gap-3 text-sm">
        <label className="flex items-center gap-1.5">
          <span style={{ color: 'var(--color-ink-muted)' }}>From</span>
          <select
            className="rounded border px-2 py-1"
            style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            value={fromN}
            onChange={(e) => setFromN(Number(e.target.value))}
          >
            {withSim.map((it) => (
              <option key={it.iteration_number} value={it.iteration_number}>
                Iteration {it.iteration_number}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5">
          <span style={{ color: 'var(--color-ink-muted)' }}>To</span>
          <select
            className="rounded border px-2 py-1"
            style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            value={toN}
            onChange={(e) => setToN(Number(e.target.value))}
          >
            {withSim.map((it) => (
              <option key={it.iteration_number} value={it.iteration_number}>
                Iteration {it.iteration_number}
              </option>
            ))}
          </select>
        </label>
      </div>

      {from.simulation && to.simulation && (
        <div className="space-y-3 rounded-[var(--radius-md)] border p-4" style={{ borderColor: 'var(--color-border)' }}>
          <div>
            <p className="mb-1 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
              Subject
            </p>
            <DiffText before={from.simulation.subject} after={to.simulation.subject} />
          </div>
          <div>
            <p className="mb-1 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
              Body
            </p>
            <DiffText before={from.simulation.body} after={to.simulation.body} />
          </div>
        </div>
      )}
    </div>
  )
}
