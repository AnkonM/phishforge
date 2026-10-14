export function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div
      className="rounded-[var(--radius-lg)] border p-4"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
    >
      <p className="text-xs font-medium" style={{ color: 'var(--color-ink-muted)' }}>
        {label}
      </p>
      <p className="mt-1 font-mono text-2xl font-semibold" style={{ color: 'var(--color-ink)' }}>
        {value}
      </p>
      {sub && (
        <p className="mt-0.5 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
          {sub}
        </p>
      )}
    </div>
  )
}
