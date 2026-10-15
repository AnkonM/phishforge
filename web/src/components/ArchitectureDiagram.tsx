const STAGES = [
  { label: 'Generator', x: 20 },
  { label: 'Safety Gate', x: 160 },
  { label: 'Verifier', x: 300 },
  { label: 'Scoring', x: 440 },
  { label: 'Refinement', x: 580 },
]

export function ArchitectureDiagram() {
  return (
    <svg
      viewBox="0 0 700 160"
      className="w-full"
      role="img"
      aria-label="Five-stage closed loop: Generator, Safety Gate, Verifier, Scoring, Refinement, looping back to Generator"
    >
      {STAGES.map((s, i) => (
        <g key={s.label}>
          <rect
            x={s.x}
            y={50}
            width={100}
            height={48}
            rx={8}
            fill="var(--color-surface)"
            stroke={i === 1 ? 'var(--color-rejected-unsafe)' : 'var(--color-border-strong)'}
            strokeWidth={1.5}
          />
          <text x={s.x + 50} y={78} textAnchor="middle" fontSize="12" fontWeight={500} fill="var(--color-ink)">
            {s.label}
          </text>
          {i < STAGES.length - 1 && (
            <line
              x1={s.x + 100}
              y1={74}
              x2={STAGES[i + 1].x}
              y2={74}
              stroke="var(--color-ink-muted)"
              strokeWidth={1.5}
              markerEnd="url(#arrow)"
            />
          )}
        </g>
      ))}

      {/* Loop back from Refinement to Generator (REVISE) */}
      <path
        d="M 630 98 C 630 140, 70 140, 70 98"
        fill="none"
        stroke="var(--color-signal)"
        strokeWidth={1.5}
        strokeDasharray="4 3"
        markerEnd="url(#arrow-signal)"
      />
      <text x={350} y={148} textAnchor="middle" fontSize="11" fill="var(--color-signal)">
        REVISE → back to Generator (up to 3 iterations)
      </text>

      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6" fill="none" stroke="var(--color-ink-muted)" strokeWidth={1.2} />
        </marker>
        <marker id="arrow-signal" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6" fill="none" stroke="var(--color-signal)" strokeWidth={1.2} />
        </marker>
      </defs>
    </svg>
  )
}
