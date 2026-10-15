import { Download, RotateCw, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatCondition, formatDateTime, formatDifficulty, formatRole, formatScenarioType, formatScore } from '../lib/format'
import type { RunSummary } from '../lib/types'
import { StateBadge } from './StateBadge'

export function RunsTable({
  runs,
  selected,
  onToggleSelect,
  onRerun,
  onDownload,
  onDelete,
}: {
  runs: RunSummary[]
  selected?: Set<string>
  onToggleSelect?: (runId: string) => void
  onRerun?: (runId: string) => void
  onDownload?: (runId: string) => void
  onDelete?: (runId: string) => void
}) {
  if (runs.length === 0) {
    return (
      <p className="py-8 text-center text-sm" style={{ color: 'var(--color-ink-muted)' }}>
        No runs match the current filters.
      </p>
    )
  }

  return (
    <div className="scrollbar-thin overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b text-xs" style={{ borderColor: 'var(--color-border)', color: 'var(--color-ink-muted)' }}>
            {onToggleSelect && <th className="w-8 py-2"></th>}
            <th className="py-2 pr-3 font-medium">Time</th>
            <th className="py-2 pr-3 font-medium">Role</th>
            <th className="py-2 pr-3 font-medium">Scenario type</th>
            <th className="py-2 pr-3 font-medium">Difficulty</th>
            <th className="py-2 pr-3 font-medium">Mode</th>
            <th className="py-2 pr-3 font-medium">State</th>
            <th className="py-2 pr-3 font-medium">Final Q</th>
            <th className="py-2 pr-3 font-medium">Iterations</th>
            {(onRerun || onDownload || onDelete) && <th className="py-2 pr-3 font-medium">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr
              key={r.run_id}
              className="border-b transition-colors hover:bg-[var(--color-page)]"
              style={{ borderColor: 'var(--color-border)' }}
            >
              {onToggleSelect && (
                <td className="py-2">
                  <input
                    type="checkbox"
                    checked={selected?.has(r.run_id) ?? false}
                    onChange={() => onToggleSelect(r.run_id)}
                    aria-label={`Select run ${r.run_id}`}
                  />
                </td>
              )}
              <td className="py-2 pr-3 font-mono text-xs" style={{ color: 'var(--color-ink-secondary)' }}>
                <Link to={`/runs/${r.run_id}`} className="hover:underline">
                  {formatDateTime(r.created_at)}
                </Link>
              </td>
              <td className="py-2 pr-3">{formatRole(r.target_role)}</td>
              <td className="py-2 pr-3">{formatScenarioType(r.scenario_type)}</td>
              <td className="py-2 pr-3">{formatDifficulty(r.difficulty)}</td>
              <td className="py-2 pr-3">
                {formatCondition(r.condition)}
                {r.imported && (
                  <span className="ml-1.5 rounded px-1.5 py-0.5 text-[10px]" style={{ background: 'var(--color-page)', color: 'var(--color-ink-muted)' }}>
                    imported
                  </span>
                )}
              </td>
              <td className="py-2 pr-3">
                <StateBadge state={r.terminal_state} size="sm" />
              </td>
              <td className="py-2 pr-3 font-mono">{formatScore(r.final_score)}</td>
              <td className="py-2 pr-3 font-mono">{r.iteration_count}</td>
              {(onRerun || onDownload || onDelete) && (
                <td className="py-2 pr-3">
                  <div className="flex items-center gap-1.5">
                    {onRerun && (
                      <button type="button" onClick={() => onRerun(r.run_id)} aria-label="Re-run with same spec" title="Re-run">
                        <RotateCw size={13} style={{ color: 'var(--color-ink-muted)' }} aria-hidden />
                      </button>
                    )}
                    {onDownload && (
                      <button type="button" onClick={() => onDownload(r.run_id)} aria-label="Download JSON" title="Download JSON">
                        <Download size={13} style={{ color: 'var(--color-ink-muted)' }} aria-hidden />
                      </button>
                    )}
                    {onDelete && (
                      <button type="button" onClick={() => onDelete(r.run_id)} aria-label="Delete run" title="Delete">
                        <Trash2 size={13} style={{ color: 'var(--color-rejected-unsafe)' }} aria-hidden />
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
