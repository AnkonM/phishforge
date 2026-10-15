import { X } from 'lucide-react'
import { useId, useState } from 'react'
import { formatDifficulty, formatRole, formatScenarioType } from '../lib/format'
import type { FormErrors } from '../lib/scenarioDefaults'
import type { ConfigResponse, ScenarioSpecification } from '../lib/types'

const SUGGESTED_INDICATORS = [
  'urgency',
  'authority_impersonation',
  'suspicious_link',
  'generic_greeting',
  'unusual_request',
  'credential_harvesting_pretext',
  'delivery_expense_pretext',
  'spelling_errors',
]

export function ScenarioForm({
  value,
  onChange,
  config,
  errors,
}: {
  value: ScenarioSpecification
  onChange: (next: ScenarioSpecification) => void
  config: ConfigResponse
  errors?: FormErrors
}) {
  const [indicatorInput, setIndicatorInput] = useState('')
  const orgId = useId()
  const difficultyId = useId()

  function set<K extends keyof ScenarioSpecification>(key: K, v: ScenarioSpecification[K]) {
    onChange({ ...value, [key]: v })
  }

  function addIndicator(raw: string) {
    const v = raw.trim().toLowerCase().replace(/\s+/g, '_')
    if (!v || value.desired_indicators.includes(v)) return
    set('desired_indicators', [...value.desired_indicators, v])
    setIndicatorInput('')
  }

  function removeIndicator(ind: string) {
    set(
      'desired_indicators',
      value.desired_indicators.filter((i) => i !== ind),
    )
  }

  return (
    <form className="space-y-3.5" aria-label="Scenario builder">
      <div>
        <label htmlFor={orgId} className="mb-1 block text-sm font-medium" style={{ color: 'var(--color-ink)' }}>
          Organization context
        </label>
        <textarea
          id={orgId}
          rows={2}
          className="w-full rounded-[var(--radius-md)] border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={value.organization_context}
          onChange={(e) => set('organization_context', e.target.value)}
          placeholder="Fictional org name, size, and relevant systems (e.g. SSO provider)."
        />
        {errors?.organization_context && <FieldError message={errors.organization_context} />}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-sm font-medium">Target role</label>
          <select
            className="w-full rounded-[var(--radius-md)] border px-2.5 py-1.5 text-sm"
            style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            value={value.target_role}
            onChange={(e) => set('target_role', e.target.value as ScenarioSpecification['target_role'])}
          >
            {config.supported_roles.map((r) => (
              <option key={r} value={r}>
                {formatRole(r)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Scenario type</label>
          <select
            className="w-full rounded-[var(--radius-md)] border px-2.5 py-1.5 text-sm"
            style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            value={value.scenario_type}
            onChange={(e) => set('scenario_type', e.target.value)}
          >
            {config.supported_scenario_types.map((t) => (
              <option key={t} value={t}>
                {formatScenarioType(t)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor={difficultyId} className="mb-1 block text-sm font-medium">
          Difficulty
        </label>
        <select
          id={difficultyId}
          className="w-full rounded-[var(--radius-md)] border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={value.difficulty}
          onChange={(e) => set('difficulty', Number(e.target.value) as ScenarioSpecification['difficulty'])}
        >
          {config.difficulty_rubric.map((d) => (
            <option key={d.level} value={d.level}>
              {formatDifficulty(d.level)}
            </option>
          ))}
        </select>
        <p className="mt-1.5 text-xs leading-relaxed" style={{ color: 'var(--color-ink-muted)' }}>
          {config.difficulty_rubric.find((d) => d.level === value.difficulty)?.description}
        </p>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Desired social-engineering indicators</label>
        <div
          className="flex flex-wrap items-center gap-1.5 rounded-[var(--radius-md)] border p-2"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        >
          {value.desired_indicators.map((ind) => (
            <span
              key={ind}
              className="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
              style={{ background: 'var(--color-page)', color: 'var(--color-ink-secondary)' }}
            >
              {ind.replace(/_/g, ' ')}
              <button
                type="button"
                onClick={() => removeIndicator(ind)}
                aria-label={`Remove indicator ${ind}`}
                className="rounded-full hover:opacity-70"
              >
                <X size={10} aria-hidden />
              </button>
            </span>
          ))}
          <input
            className="min-w-[8ch] flex-1 bg-transparent text-sm outline-none"
            value={indicatorInput}
            onChange={(e) => setIndicatorInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault()
                addIndicator(indicatorInput)
              }
            }}
            placeholder="type and press Enter"
          />
        </div>
        <div className="mt-1.5 flex flex-wrap gap-1">
          {SUGGESTED_INDICATORS.filter((s) => !value.desired_indicators.includes(s)).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => addIndicator(s)}
              className="rounded-full border px-2 py-0.5 text-[11px]"
              style={{ borderColor: 'var(--color-border)', color: 'var(--color-ink-muted)' }}
            >
              + {s.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
        {errors?.desired_indicators && <FieldError message={errors.desired_indicators} />}
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Language</label>
        <select
          className="w-48 rounded-[var(--radius-md)] border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={value.language}
          onChange={(e) => set('language', e.target.value)}
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.label} ({lang.code})
            </option>
          ))}
        </select>
        <p className="mt-1.5 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
          Passed to the generator prompt as the target language for the simulation content.
        </p>
      </div>
    </form>
  )
}

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'it', label: 'Italian' },
  { code: 'nl', label: 'Dutch' },
  { code: 'hi', label: 'Hindi' },
  { code: 'ar', label: 'Arabic' },
  { code: 'zh', label: 'Chinese' },
  { code: 'ja', label: 'Japanese' },
  { code: 'ko', label: 'Korean' },
]

function FieldError({ message }: { message: string }) {
  return (
    <p className="mt-1 text-xs" style={{ color: 'var(--color-rejected-unsafe)' }}>
      {message}
    </p>
  )
}

