import type { VerificationResult } from '../lib/types'

export function VerifierPanel({ result }: { result: VerificationResult | null }) {
  if (!result) {
    return <p className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>Not yet evaluated.</p>
  }

  return (
    <div className="space-y-4">
      <div>
        <h4 className="mb-2 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
          Layer A — deterministic checks
        </h4>
        <dl className="grid grid-cols-2 gap-3">
          <ScoreStat label="Indicator coverage" value={result.indicator_score} />
          <ScoreStat label="Language quality" value={result.language_score} />
        </dl>
      </div>

      <div>
        <h4 className="mb-2 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
          Layer B — LLM judge
        </h4>
        <dl className="grid grid-cols-3 gap-3">
          <ScoreStat label="Realism" value={result.realism_score} />
          <ScoreStat label="Role relevance" value={result.relevance_score} />
          <ScoreStat label="Difficulty match" value={result.difficulty_score} />
        </dl>
      </div>

      {result.semantic_findings.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-ink-muted)' }}>
            Weakness findings
          </h4>
          <ul className="space-y-1.5 text-sm" style={{ color: 'var(--color-ink-secondary)' }}>
            {result.semantic_findings.map((f, i) => (
              <li key={i} className="flex gap-2">
                <span aria-hidden>·</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function ScoreStat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-xs" style={{ color: 'var(--color-ink-muted)' }}>
        {label}
      </dt>
      <dd className="font-mono text-lg font-medium" style={{ color: 'var(--color-ink)' }}>
        {value.toFixed(1)}
      </dd>
    </div>
  )
}
