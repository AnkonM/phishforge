import { formatDifficulty, formatRole, formatScenarioType } from '../lib/format'
import type { ScenarioSpecification } from '../lib/types'

export function PresetPicker({
  presets,
  onSelect,
}: {
  presets: ScenarioSpecification[]
  onSelect: (spec: ScenarioSpecification) => void
}) {
  return (
    <div className="scrollbar-thin flex gap-2 overflow-x-auto pb-1">
      {presets.map((p) => (
        <button
          key={p.scenario_id}
          type="button"
          onClick={() => onSelect(p)}
          className="shrink-0 rounded-[var(--radius-md)] border px-3 py-2 text-left text-xs transition-colors hover:border-[var(--color-signal)]"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        >
          <p className="font-medium" style={{ color: 'var(--color-ink)' }}>
            {formatRole(p.target_role)} · {formatScenarioType(p.scenario_type)}
          </p>
          <p style={{ color: 'var(--color-ink-muted)' }}>{formatDifficulty(p.difficulty)}</p>
        </button>
      ))}
    </div>
  )
}
