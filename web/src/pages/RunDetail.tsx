import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Trash2 } from 'lucide-react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ConvergenceView } from '../components/ConvergenceView'
import { DiffView } from '../components/DiffView'
import { EmailCard } from '../components/EmailCard'
import { GatePanel } from '../components/GatePanel'
import { JsonToggle } from '../components/JsonToggle'
import { PipelineStepper } from '../components/PipelineStepper'
import { ScorePanel } from '../components/ScorePanel'
import { ErrorState, PageSkeleton } from '../components/Skeletons'
import { StateBadge } from '../components/StateBadge'
import { VerifierPanel } from '../components/VerifierPanel'
import { formatCondition, formatDateTime, formatDifficulty, formatRole, formatScenarioType } from '../lib/format'
import { buildViewStateFromRecord } from '../lib/runReducer'
import { api } from '../lib/api'
import type { RunRecord } from '../lib/types'

function RunColumn({ record }: { record: RunRecord }) {
  const state = buildViewStateFromRecord(record)
  const lastIteration = state.iterations[state.iterations.length - 1]

  return (
    <div className="space-y-4">
      <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium" style={{ color: 'var(--color-ink)' }}>
              {formatRole(record.scenario.target_role)} · {formatScenarioType(record.scenario.scenario_type)}
            </p>
            <p className="text-xs" style={{ color: 'var(--color-ink-muted)' }}>
              {formatDifficulty(record.scenario.difficulty)} · {formatCondition(record.condition)} · {formatDateTime(record.created_at)}
            </p>
          </div>
          <StateBadge state={record.terminal_state} />
        </div>
        <PipelineStepper stages={state.stages} currentIteration={state.currentIteration} maxIterations={3} />
      </div>

      {lastIteration?.simulation && <EmailCard simulation={lastIteration.simulation} />}

      {lastIteration?.safety_result && (
        <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
          <h4 className="mb-3 text-sm font-semibold">Safety gate</h4>
          <GatePanel result={lastIteration.safety_result} />
        </div>
      )}

      {lastIteration?.verification && (
        <>
          <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
            <h4 className="mb-3 text-sm font-semibold">Verifier</h4>
            <VerifierPanel result={lastIteration.verification} />
          </div>
          <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
            <h4 className="mb-3 text-sm font-semibold">Score</h4>
            <ScorePanel result={lastIteration.verification} />
          </div>
        </>
      )}

      <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
        <h4 className="mb-4 text-sm font-semibold">Iteration convergence</h4>
        <ConvergenceView iterations={state.iterations} terminalState={state.terminalState} />
      </div>

      {state.iterations.filter((i) => i.simulation).length >= 2 && (
        <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
          <h4 className="mb-3 text-sm font-semibold">Email diff</h4>
          <DiffView iterations={state.iterations} />
        </div>
      )}

      <JsonToggle data={record} label="Raw RunRecord JSON" />
    </div>
  )
}

export function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const [searchParams] = useSearchParams()
  const compareWith = searchParams.get('compareWith')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId as string),
    enabled: !!runId,
  })
  const { data: compareData } = useQuery({
    queryKey: ['run', compareWith],
    queryFn: () => api.getRun(compareWith as string),
    enabled: !!compareWith,
  })

  if (isLoading) return <PageSkeleton />
  if (error || !data) return <ErrorState message="Could not load this run." />

  const record = data.record

  async function handleDelete() {
    if (!runId) return
    await api.deleteRun(runId)
    queryClient.invalidateQueries({ queryKey: ['runs'] })
    navigate('/runs')
  }

  function handleDownload() {
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${record.run_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-mono text-lg font-semibold" style={{ color: 'var(--color-ink)' }}>
          Run {record.run_id.slice(0, 8)}
        </h1>
        <div className="flex gap-2">
          <button type="button" onClick={handleDownload} className="flex items-center gap-1 rounded border px-2 py-1 text-sm" style={{ borderColor: 'var(--color-border)' }}>
            <Download size={14} aria-hidden /> Download
          </button>
          <button type="button" onClick={handleDelete} className="flex items-center gap-1 rounded border px-2 py-1 text-sm" style={{ borderColor: 'var(--color-border)', color: 'var(--color-rejected-unsafe)' }}>
            <Trash2 size={14} aria-hidden /> Delete
          </button>
        </div>
      </div>

      <div className={compareData ? 'grid gap-6 lg:grid-cols-2' : ''}>
        <RunColumn record={record} />
        {compareData && <RunColumn record={compareData.record} />}
      </div>
    </div>
  )
}
