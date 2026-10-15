import { ChevronRight } from 'lucide-react'
import { useState } from 'react'

export function JsonToggle({ data, label = 'Raw JSON' }: { data: unknown; label?: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-xs font-medium"
        style={{ color: 'var(--color-ink-muted)' }}
        aria-expanded={open}
      >
        <ChevronRight size={14} className={`transition-transform ${open ? 'rotate-90' : ''}`} aria-hidden />
        {label}
      </button>
      {open && (
        <pre
          className="scrollbar-thin mt-2 max-h-96 overflow-auto rounded-[var(--radius-md)] border p-3 font-mono text-xs"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-page)', color: 'var(--color-ink-secondary)' }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}
