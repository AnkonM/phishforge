import { ShieldAlert } from 'lucide-react'
import type { ReactNode } from 'react'
import type { GeneratedSimulation } from '../lib/types'

/** Renders a GeneratedSimulation as an email-client-style preview. Links and
 * domains are always plain text (never <a>, never dangerouslySetInnerHTML) --
 * this is training content, not a real email. */
export function EmailCard({
  simulation,
  highlightTerms,
}: {
  simulation: GeneratedSimulation
  highlightTerms?: string[]
}) {
  return (
    <div
      className="relative overflow-hidden rounded-[var(--radius-lg)] border"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
    >
      <div
        className="flex items-center gap-2 border-b px-4 py-2 text-xs font-medium"
        style={{ borderColor: 'var(--color-border)', background: 'var(--color-revise-bg)', color: 'var(--color-revise)' }}
      >
        <ShieldAlert size={14} aria-hidden />
        <span>SIMULATION — training content only. Not a real email.</span>
      </div>

      <div className="space-y-2 border-b px-4 py-3" style={{ borderColor: 'var(--color-border)' }}>
        <Field label="From">
          <span className="font-mono text-sm">{simulation.sender}</span>
        </Field>
        <Field label="Subject">
          <HighlightedText text={simulation.subject} terms={highlightTerms} />
        </Field>
      </div>

      <div className="whitespace-pre-wrap px-4 py-4 text-sm leading-relaxed" style={{ color: 'var(--color-ink)' }}>
        <HighlightedText text={simulation.body} terms={highlightTerms} />
      </div>

      {simulation.intended_indicators.length > 0 && (
        <div className="flex flex-wrap gap-1.5 border-t px-4 py-3" style={{ borderColor: 'var(--color-border)' }}>
          {simulation.intended_indicators.map((ind) => (
            <span
              key={ind}
              className="rounded-full px-2 py-0.5 text-[11px] font-mono"
              style={{ background: 'var(--color-page)', color: 'var(--color-ink-secondary)' }}
            >
              {ind.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex gap-2 text-sm">
      <span className="w-16 shrink-0 font-medium" style={{ color: 'var(--color-ink-muted)' }}>
        {label}
      </span>
      <span>{children}</span>
    </div>
  )
}

/** Plain-text rendering with optional highlighted substrings (for safety
 * findings) -- built from text nodes only, never innerHTML. */
function HighlightedText({ text, terms }: { text: string; terms?: string[] }) {
  if (!terms || terms.length === 0) return <>{text}</>
  const pattern = terms
    .map((t) => t.trim())
    .filter(Boolean)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|')
  if (!pattern) return <>{text}</>
  const regex = new RegExp(`(${pattern})`, 'gi')
  const segments = text.split(regex)
  // String.split with one capturing group interleaves the captured matches
  // at odd indices -- using index parity avoids reusing a global-flag
  // regex's stateful .test() (which would give wrong results on reuse).
  return (
    <>
      {segments.map((seg, i) =>
        i % 2 === 1 ? (
          <mark
            key={i}
            style={{ background: 'var(--color-rejected-unsafe-bg)', color: 'var(--color-rejected-unsafe)' }}
            className="rounded px-0.5"
          >
            {seg}
          </mark>
        ) : (
          <span key={i}>{seg}</span>
        ),
      )}
    </>
  )
}
