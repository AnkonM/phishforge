import type { VerificationResult } from '../lib/types'

const DIMENSIONS: { key: keyof VerificationResult; label: string; weightKey: string }[] = [
  { key: 'realism_score', label: 'Realism', weightKey: 'realism' },
  { key: 'relevance_score', label: 'Role relevance', weightKey: 'role_relevance' },
  { key: 'indicator_score', label: 'Indicator coverage', weightKey: 'indicator_coverage' },
  { key: 'difficulty_score', label: 'Difficulty match', weightKey: 'difficulty_match' },
  { key: 'language_score', label: 'Language quality', weightKey: 'language_quality' },
]

export function ScorePanel({
  result,
  weights,
  passThreshold = 80,
  reviseThreshold = 60,
}: {
  result: VerificationResult | null
  weights?: Record<string, number>
  passThreshold?: number
  reviseThreshold?: number
}) {
  if (!result) {
    return <p className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>Not yet scored.</p>
  }

  const bandColor =
    result.pass_fail === 'PASS' ? 'var(--color-pass)' : result.pass_fail === 'REVISE' ? 'var(--color-revise)' : 'var(--color-fail)'

  return (
    <div>
      <div className="mb-4 flex items-baseline gap-3">
        <span className="font-mono text-3xl font-semibold" style={{ color: bandColor }}>
          {result.overall_score.toFixed(1)}
        </span>
        <span className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>
          / 100 · {result.pass_fail} band
        </span>
      </div>

      <div className="space-y-2.5">
        {DIMENSIONS.map((d) => {
          const value = result[d.key] as number
          const weight = weights?.[d.weightKey]
          return (
            <div key={d.key}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span style={{ color: 'var(--color-ink-secondary)' }}>
                  {d.label}
                  {weight !== undefined && <span style={{ color: 'var(--color-ink-muted)' }}> · weight {Math.round(weight * 100)}%</span>}
                </span>
                <span className="font-mono" style={{ color: 'var(--color-ink)' }}>
                  {value.toFixed(1)}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full" style={{ background: 'var(--color-border)' }}>
                <div
                  className="h-full rounded-full transition-[width] duration-300 motion-reduce:transition-none"
                  style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: 'var(--color-signal)' }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <p className="mt-3 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
        PASS ≥ {passThreshold} · REVISE ≥ {reviseThreshold} · FAIL below {reviseThreshold}
      </p>
    </div>
  )
}
