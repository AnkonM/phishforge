import { CheckCircle2, XCircle } from 'lucide-react'
import type { SafetyCheckResult, SafetyRuleInfo } from '../lib/types'

const RULE_LABELS: Record<string, string> = {
  check_no_real_domains: 'No real domains',
  check_no_credential_harvesting: 'No credential harvesting',
  check_no_attachment_payloads: 'No dangerous attachments',
  check_no_real_brand_impersonation: 'No real brand impersonation',
  check_no_real_pii: 'No real PII',
}

// Distinctive substrings each rule's own finding messages always contain
// (see core/safety/safety_gate.py) -- used to attribute a finding back to
// the rule that raised it, for per-rule pass/fail display.
const RULE_FINDING_MARKERS: Record<string, string[]> = {
  check_no_real_domains: ['real domain', 'real web domain'],
  check_no_credential_harvesting: ['credential harvesting'],
  check_no_attachment_payloads: ['attachment payload', 'payload execution'],
  check_no_real_brand_impersonation: ['brand impersonation'],
  check_no_real_pii: ['social security', 'credit card'],
}

export function GatePanel({ result, rules }: { result: SafetyCheckResult | null; rules?: SafetyRuleInfo[] }) {
  if (!result) {
    return <p className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>Not yet evaluated.</p>
  }

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        {result.passed ? (
          <CheckCircle2 size={16} style={{ color: 'var(--color-pass)' }} aria-hidden />
        ) : (
          <XCircle size={16} style={{ color: 'var(--color-rejected-unsafe)' }} aria-hidden />
        )}
        <span className="font-medium" style={{ color: result.passed ? 'var(--color-pass)' : 'var(--color-rejected-unsafe)' }}>
          {result.passed ? 'All 5 rules passed' : `${result.findings.length} finding(s)`}
        </span>
      </div>

      <ul className="space-y-1.5">
        {(rules ?? Object.keys(RULE_LABELS).map((name) => ({ name, description: '' }))).map((rule) => {
          const markers = RULE_FINDING_MARKERS[rule.name] ?? []
          const findingsForRule = result.findings.filter((f) =>
            markers.some((m) => f.toLowerCase().includes(m)),
          )
          const ruleFailed = !result.passed && findingsForRule.length > 0
          return (
            <li key={rule.name} className="flex items-start gap-2 text-sm">
              {ruleFailed ? (
                <XCircle size={14} className="mt-0.5 shrink-0" style={{ color: 'var(--color-rejected-unsafe)' }} aria-hidden />
              ) : (
                <CheckCircle2 size={14} className="mt-0.5 shrink-0" style={{ color: 'var(--color-pass)' }} aria-hidden />
              )}
              <span style={{ color: 'var(--color-ink-secondary)' }}>{RULE_LABELS[rule.name] ?? rule.name}</span>
            </li>
          )
        })}
      </ul>

      {result.findings.length > 0 && (
        <ul className="mt-3 space-y-1.5 border-t pt-3 text-sm" style={{ borderColor: 'var(--color-border)' }}>
          {result.findings.map((f, i) => (
            <li key={i} style={{ color: 'var(--color-rejected-unsafe)' }}>
              {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
