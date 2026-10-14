import { useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, XCircle } from 'lucide-react'
import { useState } from 'react'
import { ArchitectureDiagram } from '../components/ArchitectureDiagram'
import { ErrorState, PageSkeleton } from '../components/Skeletons'
import { api } from '../lib/api'
import type { ProviderMode } from '../lib/types'

export function Settings() {
  const queryClient = useQueryClient()
  const { data: health, isLoading: healthLoading } = useQuery({ queryKey: ['health'], queryFn: api.health })
  const { data: config, isLoading: configLoading } = useQuery({ queryKey: ['config'], queryFn: api.config })
  const [reachability, setReachability] = useState<{ reachable: boolean; detail: string } | null>(null)
  const [testing, setTesting] = useState(false)

  async function setMode(mode: ProviderMode) {
    await api.setMode(mode)
    queryClient.invalidateQueries({ queryKey: ['health'] })
  }

  async function testReachability() {
    setTesting(true)
    try {
      setReachability(await api.reachability())
    } finally {
      setTesting(false)
    }
  }

  if (healthLoading || configLoading) return <PageSkeleton />
  if (!health || !config) return <ErrorState message="Could not load settings." />

  return (
    <div className="max-w-3xl space-y-8">
      <h1 className="text-lg font-semibold" style={{ color: 'var(--color-ink)' }}>
        Settings &amp; About
      </h1>

      <section className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
        <h2 className="mb-3 text-sm font-semibold">Provider status</h2>
        <div className="mb-4 flex items-center gap-2 text-sm">
          {health.key_configured ? (
            <CheckCircle2 size={16} style={{ color: 'var(--color-pass)' }} aria-hidden />
          ) : (
            <XCircle size={16} style={{ color: 'var(--color-ink-muted)' }} aria-hidden />
          )}
          <span>{health.key_configured ? 'GEMINI_API_KEY is configured' : 'No API key configured'}</span>
          <span className="font-mono text-xs" style={{ color: 'var(--color-ink-muted)' }}>
            ({config.model_name})
          </span>
        </div>

        <div className="mb-4">
          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
            Mode
          </p>
          <div className="inline-flex rounded-[var(--radius-md)] border p-1" style={{ borderColor: 'var(--color-border)' }}>
            {(['demo', 'live'] as ProviderMode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className="rounded-[var(--radius-sm)] px-3 py-1.5 text-sm font-medium"
                style={health.mode === m ? { background: 'var(--color-page)', color: 'var(--color-signal)' } : { color: 'var(--color-ink-secondary)' }}
              >
                {m === 'demo' ? 'Demo (mock provider)' : 'Live (Gemini)'}
              </button>
            ))}
          </div>
          <p className="mt-1.5 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
            Demo mode never calls the live API — four deterministic scripted scenarios make the whole console
            demoable and testable offline.
          </p>
        </div>

        <button
          type="button"
          onClick={testReachability}
          disabled={testing || !health.key_configured}
          className="rounded-[var(--radius-md)] border px-3 py-1.5 text-sm font-medium disabled:opacity-50"
          style={{ borderColor: 'var(--color-border)' }}
        >
          {testing ? 'Testing…' : 'Test reachability'}
        </button>
        {reachability && (
          <p className="mt-2 text-sm" style={{ color: reachability.reachable ? 'var(--color-pass)' : 'var(--color-rejected-unsafe)' }}>
            {reachability.detail}
          </p>
        )}
      </section>

      <section className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
        <h2 className="mb-3 text-sm font-semibold">Pipeline configuration (read-only)</h2>
        <div className="mb-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Stat label="PASS threshold" value={`≥ ${config.pass_threshold}`} />
          <Stat label="REVISE threshold" value={`≥ ${config.revise_threshold}`} />
          <Stat label="Max iterations" value={String(config.max_iterations)} />
          <Stat label="Plateau rule" value={`Δ<${config.improvement_epsilon} ×${config.improvement_patience}`} />
        </div>

        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
          Dimension weights
        </h3>
        <div className="mb-4 flex flex-wrap gap-3 text-sm">
          {Object.entries(config.scoring_weights).map(([k, v]) => (
            <span key={k} className="rounded-full px-2.5 py-1" style={{ background: 'var(--color-page)' }}>
              {k.replace(/_/g, ' ')}: {Math.round(v * 100)}%
            </span>
          ))}
        </div>

        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
          Safety gate rules
        </h3>
        <ul className="mb-4 space-y-1.5 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
          {config.safety_rules.map((r) => (
            <li key={r.name}>
              <span className="font-mono text-xs" style={{ color: 'var(--color-ink-muted)' }}>
                {r.name}
              </span>{' '}
              — {r.description}
            </li>
          ))}
        </ul>

        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
          Difficulty rubric
        </h3>
        <ul className="space-y-1.5 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
          {config.difficulty_rubric.map((d) => (
            <li key={d.level}>
              <span className="font-medium" style={{ color: 'var(--color-ink)' }}>
                Level {d.level} — {d.label}:
              </span>{' '}
              {d.description}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-[var(--radius-lg)] border p-5" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
        <h2 className="mb-3 text-sm font-semibold">About</h2>
        <ArchitectureDiagram />
        <div className="mt-4 space-y-2 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
          <p>
            <strong style={{ color: 'var(--color-ink)' }}>Generator</strong> produces a candidate training email
            from the scenario spec (and, after the first iteration, revision instructions).
          </p>
          <p>
            <strong style={{ color: 'var(--color-ink)' }}>Safety Gate</strong> runs five deterministic, zero-LLM
            checks and hard-stops the run on any violation — a REJECTED_UNSAFE run never reaches scoring.
          </p>
          <p>
            <strong style={{ color: 'var(--color-ink)' }}>Verifier</strong> combines Layer A deterministic rule
            checks with Layer B LLM-judged realism/relevance/difficulty.
          </p>
          <p>
            <strong style={{ color: 'var(--color-ink)' }}>Scoring Engine</strong> computes the weighted overall
            score Q and classifies it PASS/REVISE/FAIL.
          </p>
          <p>
            <strong style={{ color: 'var(--color-ink)' }}>Refinement Controller</strong> turns weaknesses into
            revision instructions for the next iteration, or stops the loop (pass, iteration ceiling, or
            plateau).
          </p>
        </div>

        <h3 className="mb-2 mt-5 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
          Limitations (from the paper)
        </h3>
        <ul className="list-disc space-y-1 pl-5 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
          <li>Small benchmark N (12 scenarios) — results throughout this console are descriptive, not inferential.</li>
          <li>Human evaluation used a single rater.</li>
          <li>The Layer B judge is the same model family as the generator, which can share blind spots.</li>
        </ul>
      </section>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs" style={{ color: 'var(--color-ink-muted)' }}>
        {label}
      </p>
      <p className="font-mono font-medium" style={{ color: 'var(--color-ink)' }}>
        {value}
      </p>
    </div>
  )
}
