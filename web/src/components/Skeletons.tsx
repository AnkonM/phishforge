export function SkeletonBlock({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-[var(--radius-md)] motion-reduce:animate-none ${className}`}
      style={{ background: 'var(--color-border)' }}
      aria-hidden
    />
  )
}

export function PageSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading">
      <SkeletonBlock className="h-8 w-48" />
      <SkeletonBlock className="h-40 w-full" />
      <SkeletonBlock className="h-40 w-full" />
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading table">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonBlock key={i} className="h-8 w-full" />
      ))}
    </div>
  )
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-[var(--radius-lg)] border py-10 text-center" style={{ borderColor: 'var(--color-border)' }}>
      <p className="font-medium" style={{ color: 'var(--color-ink)' }}>
        {title}
      </p>
      {hint && (
        <p className="mt-1 text-sm" style={{ color: 'var(--color-ink-muted)' }}>
          {hint}
        </p>
      )}
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      className="rounded-[var(--radius-lg)] border p-4 text-sm"
      style={{ borderColor: 'var(--color-rejected-unsafe)', background: 'var(--color-rejected-unsafe-bg)', color: 'var(--color-rejected-unsafe)' }}
      role="alert"
    >
      {message}
    </div>
  )
}
