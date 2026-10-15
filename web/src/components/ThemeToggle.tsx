import { Laptop, Moon, Sun } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

const OPTIONS = [
  { value: 'system' as const, icon: Laptop, label: 'System' },
  { value: 'light' as const, icon: Sun, label: 'Light' },
  { value: 'dark' as const, icon: Moon, label: 'Dark' },
]

export function ThemeToggle() {
  const [pref, setPref] = useTheme()
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
