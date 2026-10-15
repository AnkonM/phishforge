import { Laptop, Moon, Sun } from 'lucide-react'
import { useTheme, type ThemePreference } from '../hooks/useTheme'

const OPTIONS: { value: ThemePreference; icon: typeof Laptop; label: string }[] = [
  { value: 'system', icon: Laptop, label: 'System' },
  { value: 'light', icon: Sun, label: 'Light' },
  { value: 'dark', icon: Moon, label: 'Dark' },
]

export function ThemeToggle({ collapsed = false }: { collapsed?: boolean }) {
  const [pref, setPref] = useTheme()

  if (collapsed) {
    const idx = OPTIONS.findIndex((o) => o.value === pref)
    const current = OPTIONS[idx]
    const next = OPTIONS[(idx + 1) % OPTIONS.length]
    const Icon = current.icon
    return (
      <button
        type="button"
        onClick={() => setPref(next.value)}
        aria-label={`Theme: ${current.label}. Click to switch to ${next.label}.`}
        title={`Theme: ${current.label} (click for ${next.label})`}
        className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-sm)] border"
        style={{ borderColor: 'var(--color-border)', color: 'var(--color-ink-muted)' }}
      >
        <Icon size={14} aria-hidden />
      </button>
    )
  }

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="inline-flex rounded-[var(--radius-md)] border p-0.5"
      style={{ borderColor: 'var(--color-border)' }}
    >
      {OPTIONS.map((opt) => {
        const Icon = opt.icon
        const active = pref === opt.value
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={opt.label}
            title={opt.label}
            onClick={() => setPref(opt.value)}
            className="rounded-[var(--radius-sm)] p-1.5"
            style={active ? { background: 'var(--color-page)', color: 'var(--color-signal)' } : { color: 'var(--color-ink-muted)' }}
          >
            <Icon size={14} aria-hidden />
          </button>
        )
      })}
    </div>
  )
}
