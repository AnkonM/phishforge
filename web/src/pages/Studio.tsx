import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Ban, Play } from 'lucide-react'
import { useEffect, useState } from 'react'
import { ConvergenceView } from '../components/ConvergenceView'
import { DiffView } from '../components/DiffView'
import { EmailCard } from '../components/EmailCard'
import { GatePanel } from '../components/GatePanel'
import { ModeSwitch } from '../components/ModeSwitch'
import { PipelineStepper } from '../components/PipelineStepper'
import { PresetPicker } from '../components/PresetPicker'
import { ScenarioForm } from '../components/ScenarioForm'
import { ScorePanel } from '../components/ScorePanel'
import { ErrorState, PageSkeleton } from '../components/Skeletons'
import { StateBadge } from '../components/StateBadge'
import { VerifierPanel } from '../components/VerifierPanel'
import { useRunStream } from '../hooks/useRunStream'
import { api } from '../lib/api'
import { EMPTY_SCENARIO, validateScenario } from '../lib/scenarioDefaults'
import type { DemoScriptName, RunMode, ScenarioSpecification } from '../lib/types'

const DEMO_SCRIPTS: { value: DemoScriptName; label: string }[] = [
  { value: 'first_pass', label: 'First-pass PASS' },
  { value: 'revise_pass', label: 'REVISE → PASS' },
  { value: 'safety_reject', label: 'Safety-gate rejection' },
  { value: 'plateau', label: 'Plateau / FAILED_TO_CONVERGE' },
]

export function Studio() {
  const queryClient = useQueryClient()
  const { data: config, isLoading: configLoading, error: configError } = useQuery({
    queryKey: ['config'],
    queryFn: api.config,
  })
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: api.health })
  const { data: presets } = useQuery({ queryKey: ['presets'], queryFn: api.presets })

  const [spec, setSpec] = useState<ScenarioSpecification>(EMPTY_SCENARIO)
  const [mode, setMode] = useState<RunMode>('guided')
  const [demoScript, setDemoScript] = useState<DemoScriptName | ''>('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [runId, setRunId] = useState<string | null>(null)
  const [compareRunId, setCompareRunId] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [diffOpen, setDiffOpen] = useState(false)

  const { state } = useRunStream(runId)
  const { state: compareState } = useRunStream(compareRunId)

  useEffect(() => {
    if (state.finished || compareState.finished) {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    }
  }, [state.finished, compareState.finished, queryClient])

  if (configLoading) return <PageSkeleton />
  if (configError || !config) return <ErrorState message="Could not load pipeline configuration from the server." />

  async function handleRun() {
    const v = validateScenario(spec)
    setErrors(v)
    if (Object.keys(v).length > 0) return
    setSubmitError(null)
    setRunId(null)
    setCompareRunId(null)
    try {
      const resp = await api.createRun(spec, mode, demoScript || null)
      if (mode === 'compare' && resp.run_ids) {
        setRunId(resp.run_ids[0])
        setCompareRunId(resp.run_ids[1])
      } else {
        setRunId(resp.run_id)
      }
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to start run.')
    }
  }

  async function handleCancel() {
    if (runId) await api.cancelRun(runId)
    if (compareRunId) await api.cancelRun(compareRunId)
  }

  return (
    <div className="h-full overflow-y-auto px-4 py-5 lg:h-full lg:overflow-hidden lg:p-0">
      <div className="lg:grid lg:h-full lg:grid-cols-[340px_1fr] lg:items-stretch">
        {/* LEFT: scenario configuration -- frozen in place; only scrolls internally
            if its own content doesn't fit, independent of the right pane. */}
        <div className="flex flex-col lg:h-full lg:overflow-hidden lg:border-r" style={{ borderColor: 'var(--color-border)' }}>
          <div className="space-y-3.5 lg:flex-1 lg:overflow-y-auto lg:px-5 lg:py-5">
            <div>
              <h1 className="text-lg font-semibold" style={{ color: 'var(--color-ink)' }}>
                Studio
              </h1>
              <p className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>
                Build a scenario and watch the pipeline run live.{' '}
                {health && (
                  <span className="font-medium" style={{ color: health.mode === 'demo' ? 'var(--color-revise)' : 'var(--color-pass)' }}>
                    {health.mode === 'demo' ? 'Demo mode' : 'Live mode'}
                  </span>
                )}
              </p>
            </div>

            {presets && presets.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
                  Benchmark presets
                </p>
                <PresetPicker presets={presets} onSelect={setSpec} />
              </div>
            )}

            <ScenarioForm value={spec} onChange={setSpec} config={config} errors={errors} />

            <div>
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
                Run mode
              </p>
              <ModeSwitch value={mode} onChange={setMode} />
            </div>

            {health?.mode === 'demo' && (
              <div>
                <label className="mb-1 block text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
                  Demo script (optional)
                </label>
                <select
                  className="w-full rounded-[var(--radius-md)] border px-2.5 py-1.5 text-sm"
                  style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
                  value={demoScript}
                  onChange={(e) => setDemoScript(e.target.value as DemoScriptName | '')}
                >
                  <option value="">Auto (based on difficulty)</option>
                  {DEMO_SCRIPTS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Pinned action bar -- always visible, never scrolls away. */}
          <div className="shrink-0 space-y-2 border-t pt-3 lg:px-5 lg:pb-5 lg:pt-3" style={{ borderColor: 'var(--color-border)' }}>
            {submitError && <ErrorState message={submitError} />}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleRun}
                className="flex items-center gap-2 rounded-[var(--radius-md)] px-4 py-2 text-sm font-medium"
                style={{ background: 'var(--color-signal)', color: 'var(--color-signal-ink)' }}
              >
                <Play size={14} aria-hidden /> Run scenario
              </button>
              {runId && !state.finished && (
                <button
                  type="button"
                  onClick={handleCancel}
                  className="flex items-center gap-2 rounded-[var(--radius-md)] border px-4 py-2 text-sm font-medium"
                  style={{ borderColor: 'var(--color-border)' }}
                >
                  <Ban size={14} aria-hidden /> Cancel
                </button>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: live pipeline output -- the only pane that scrolls. */}
        <div className="mt-6 space-y-6 lg:mt-0 lg:h-full lg:overflow-y-auto lg:px-5 lg:py-5">
          {!runId && (
            <div
              className="flex h-64 items-center justify-center rounded-[var(--radius-lg)] border text-sm"
              style={{ borderColor: 'var(--color-border)', color: 'var(--color-ink-muted)' }}
            >
              Configure a scenario and run it to see the live pipeline here.
            </div>
          )}

          {runId && (
            <div className={compareRunId ? 'grid gap-6 lg:grid-cols-2' : ''}>
              <RunPane title={compareRunId ? 'Verifier-guided' : undefined} state={state} config={config} />
              {compareRunId && <RunPane title="Direct baseline" state={compareState} config={config} />}
            </div>
          )}

          {runId && state.iterations.length > 0 && (
            <section className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
              <h2 className="mb-4 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
                Iteration convergence
              </h2>
              <ConvergenceView
                iterations={state.iterations}
                terminalState={state.terminalState}
                passThreshold={config.pass_threshold}
                reviseThreshold={config.revise_threshold}
              />
              {state.iterations.filter((i) => i.simulation).length >= 2 && (
                <div className="mt-6 border-t pt-4" style={{ borderColor: 'var(--color-border)' }}>
                  <button
                    type="button"
                    className="text-sm font-medium"
                    style={{ color: 'var(--color-signal)' }}
                    onClick={() => setDiffOpen((o) => !o)}
                  >
                    {diffOpen ? 'Hide' : 'Show'} email diff between iterations
                  </button>
                  {diffOpen && (
                    <div className="mt-3">
                      <DiffView iterations={state.iterations} />
                    </div>
                  )}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

function RunPane({
  title,
  state,
  config,
}: {
  title?: string
  state: ReturnType<typeof useRunStream>['state']
  config: { pass_threshold: number; revise_threshold: number; scoring_weights: Record<string, number>; max_iterations: number }
}) {
  const lastIteration = state.iterations[state.iterations.length - 1]
  return (
    <div className="space-y-4">
      {title && (
        <h3 className="text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
          {title}
        </h3>
      )}
      <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
        <div className="mb-4 flex items-center justify-between">
          <PipelineStepper stages={state.stages} currentIteration={state.currentIteration} maxIterations={config.max_iterations} />
        </div>
        {state.finished && state.terminalState && (
          <div className="mb-3">
            <StateBadge state={state.terminalState} />
          </div>
        )}
        {state.errors.length > 0 && (
          <div className="mb-3 space-y-1">
            {state.errors.map((e, i) => (
              <ErrorState key={i} message={`${e.stage}: ${e.message}`} />
            ))}
          </div>
        )}
      </div>

      {lastIteration?.simulation && <EmailCard simulation={lastIteration.simulation} />}

      {lastIteration?.safety_result && (
        <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
          <h4 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
            Safety gate
          </h4>
          <GatePanel result={lastIteration.safety_result} />
        </div>
      )}

      {lastIteration?.verification && (
        <>
          <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
            <h4 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
              Verifier
            </h4>
            <VerifierPanel result={lastIteration.verification} />
          </div>
          <div className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
            <h4 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
              Score
            </h4>
            <ScorePanel
              result={lastIteration.verification}
              weights={config.scoring_weights}
              passThreshold={config.pass_threshold}
              reviseThreshold={config.revise_threshold}
            />
          </div>
        </>
      )}
    </div>
  )
}
