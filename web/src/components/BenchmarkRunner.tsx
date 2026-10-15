import { AlertTriangle } from 'lucide-react'
import { useRef, useState } from 'react'
import { api } from '../lib/api'
import { formatScore } from '../lib/format'
import { subscribeToStream } from '../lib/sse'
import type { BenchmarkEvent, ProviderMode } from '../lib/types'
import { StateBadge } from './StateBadge'

interface Row {
  scenario_id: string
  condition: string
  run_id?: string
  terminal_state?: string
  score?: number | null
  status: 'running' | 'done' | 'error'
}

export function BenchmarkRunner({ onFinished }: { onFinished?: () => void }) {
  const [confirming, setConfirming] = useState(false)
  const [mode, setMode] = useState<ProviderMode>('demo')
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState<{ index: number; total: number } | null>(null)
  const [rows, setRows] = useState<Row[]>([])
  const cleanupRef = useRef<(() => void) | null>(null)

  async function start() {
    setConfirming(false)
    setRunning(true)
    setRows([])
    const { benchmark_id } = await api.createBenchmark(mode)
    cleanupRef.current = subscribeToStream<BenchmarkEvent>(
      `/api/benchmark/${benchmark_id}/events`,
      (event) => {
        if (event.event === 'benchmark_started') {
          setProgress({ index: 0, total: event.total })
        } else if (event.event === 'scenario_started') {
          setProgress({ index: event.index, total: event.total })
          setRows((r) => [...r, { scenario_id: event.scenario_id, condition: event.condition, status: 'running' }])
        } else if (event.event === 'scenario_finished') {
          setRows((r) =>
            r.map((row) =>
              row.scenario_id === event.scenario_id && row.condition === event.condition && row.status === 'running'
                ? { ...row, run_id: event.run_id, terminal_state: event.terminal_state, score: event.score, status: 'done' }
                : row,
            ),
          )
        } else if (event.event === 'scenario_error') {
          setRows((r) =>
            r.map((row) =>
              row.scenario_id === event.scenario_id && row.condition === event.condition && row.status === 'running'
                ? { ...row, status: 'error' }
                : row,
            ),
          )
        }
      },
      () => {
        setRunning(false)
        onFinished?.()
      },
    )
  }

  function exportCsv() {
    const header = 'scenario_id,condition,run_id,terminal_state,score\n'
    const body = rows.map((r) => `${r.scenario_id},${r.condition},${r.run_id ?? ''},${r.terminal_state ?? ''},${r.score ?? ''}`).join('\n')
    downloadFile('benchmark_results.csv', header + body, 'text/csv')
  }

  function exportJson() {
    downloadFile('benchmark_results.json', JSON.stringify(rows, null, 2), 'application/json')
  }

  return (
    <div className="rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-medium" style={{ color: 'var(--color-ink)' }}>
          Benchmark runner
        </h3>
        {!running && (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="rounded-[var(--radius-md)] px-3 py-1.5 text-sm font-medium"
            style={{ background: 'var(--color-signal)', color: 'var(--color-signal-ink)' }}
          >
            Run 12 presets × 2 conditions
          </button>
        )}
      </div>
      <p className="mb-3 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
        Runs all 12 benchmark presets under both verifier-guided and direct-baseline conditions
        (24 pipeline runs total) and feeds the results into the Dashboard like any other run.
      </p>

      {confirming && (
        <div
          role="alertdialog"
          aria-label="Confirm benchmark run"
          className="mb-3 rounded-[var(--radius-md)] border p-3 text-sm"
          style={{ borderColor: 'var(--color-revise)', background: 'var(--color-revise-bg)' }}
        >
          <p className="mb-2 flex items-center gap-2 font-medium" style={{ color: 'var(--color-revise)' }}>
            <AlertTriangle size={14} aria-hidden /> This will make 24 pipeline runs.
          </p>
          <label className="mb-3 flex items-center gap-2">
            <span>Provider:</span>
            <select
              className="rounded border px-2 py-1"
              style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
              value={mode}
              onChange={(e) => setMode(e.target.value as ProviderMode)}
            >
              <option value="demo">Demo (mock, offline)</option>
              <option value="live">Live (real Gemini calls)</option>
            </select>
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={start}
              className="rounded-[var(--radius-md)] px-3 py-1.5 font-medium"
              style={{ background: 'var(--color-signal)', color: 'var(--color-signal-ink)' }}
            >
              Confirm &amp; run
            </button>
            <button type="button" onClick={() => setConfirming(false)} className="rounded-[var(--radius-md)] px-3 py-1.5">
              Cancel
            </button>
          </div>
        </div>
      )}

      {progress && (
        <div className="mb-3">
          <div className="h-2 w-full overflow-hidden rounded-full" style={{ background: 'var(--color-border)' }}>
            <div
              className="h-full rounded-full transition-[width] duration-300"
              style={{ width: `${(progress.index / progress.total) * 100}%`, background: 'var(--color-signal)' }}
            />
          </div>
          <p className="mt-1 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
            {progress.index} / {progress.total}
          </p>
        </div>
      )}

      {rows.length > 0 && (
        <>
          <div className="scrollbar-thin max-h-64 overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr style={{ color: 'var(--color-ink-muted)' }}>
                  <th className="py-1">Scenario</th>
                  <th className="py-1">Condition</th>
                  <th className="py-1">State</th>
                  <th className="py-1">Score</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-t" style={{ borderColor: 'var(--color-border)' }}>
                    <td className="py-1 font-mono">{r.scenario_id}</td>
                    <td className="py-1">{r.condition}</td>
                    <td className="py-1">
                      {r.status === 'running' ? (
                        <span style={{ color: 'var(--color-ink-muted)' }}>running…</span>
                      ) : r.terminal_state ? (
                        <StateBadge state={r.terminal_state} size="sm" />
                      ) : (
                        <span style={{ color: 'var(--color-rejected-unsafe)' }}>error</span>
                      )}
                    </td>
                    <td className="py-1 font-mono">{formatScore(r.score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!running && (
            <div className="mt-3 flex gap-2">
              <button type="button" onClick={exportCsv} className="rounded border px-2 py-1 text-xs" style={{ borderColor: 'var(--color-border)' }}>
                Export CSV
              </button>
              <button type="button" onClick={exportJson} className="rounded border px-2 py-1 text-xs" style={{ borderColor: 'var(--color-border)' }}>
                Export JSON
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function downloadFile(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
