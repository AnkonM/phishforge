import {
  CartesianGrid,
  Label,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { IterationViewData } from '../lib/runReducer'
import { DimensionBreakdown } from './DimensionBreakdown'
import { FindingsTimeline } from './FindingsTimeline'

interface ChartPoint {
  iteration: number
  score: number | null
}

export function ConvergenceView({
  iterations,
  terminalState,
  passThreshold = 80,
  reviseThreshold = 60,
}: {
  iterations: IterationViewData[]
  terminalState: string | null
  passThreshold?: number
  reviseThreshold?: number
}) {
  const scored = iterations.filter((it) => it.score !== null)

  if (terminalState === 'REJECTED_UNSAFE' && scored.length === 0) {
    return (
      <div className="rounded-[var(--radius-lg)] border p-6 text-center" style={{ borderColor: 'var(--color-border)' }}>
        <p className="text-sm font-medium" style={{ color: 'var(--color-rejected-unsafe)' }}>
          No score — the safety gate stopped this run before scoring.
        </p>
        <p className="mt-1 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
          The verifier never runs once the deterministic safety gate finds a violation, so there
          is no quality score to chart for this run.
        </p>
      </div>
    )
  }

  if (scored.length === 0) {
    return (
      <p className="text-sm" style={{ color: 'var(--color-ink-muted)' }}>
        No score yet.
      </p>
    )
  }

  const data: ChartPoint[] = iterations.map((it) => ({ iteration: it.iteration_number, score: it.score }))

  return (
    <div className="space-y-6">
      <div>
        {scored.length === 1 && (
          <p className="mb-2 text-xs font-medium" style={{ color: 'var(--color-pass)' }}>
            Converged on first attempt — no refinement was needed.
          </p>
        )}
        <div
          className="h-64 w-full"
          role="img"
          aria-label={`Quality score by iteration: ${scored.map((s) => `iteration ${s.iteration_number} scored ${s.score}`).join(', ')}`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
              <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
              <XAxis
                dataKey="iteration"
                type="number"
                domain={[1, Math.max(3, data.length)]}
                allowDecimals={false}
                tick={{ fill: 'var(--chart-text-muted)', fontSize: 12 }}
                stroke="var(--chart-axis)"
                label={{ value: 'Iteration', position: 'insideBottom', offset: -4, fill: 'var(--chart-text-muted)', fontSize: 12 }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: 'var(--chart-text-muted)', fontSize: 12 }}
                stroke="var(--chart-axis)"
                width={36}
              />
              <ReferenceLine y={passThreshold} stroke="var(--color-pass)" strokeDasharray="4 4">
                <Label value={`PASS ≥ ${passThreshold}`} position="right" fill="var(--color-pass)" fontSize={11} />
              </ReferenceLine>
              <ReferenceLine y={reviseThreshold} stroke="var(--color-revise)" strokeDasharray="4 4">
                <Label value={`REVISE ≥ ${reviseThreshold}`} position="right" fill="var(--color-revise)" fontSize={11} />
              </ReferenceLine>
              <Tooltip
                contentStyle={{
                  background: 'var(--chart-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value) => [Number(value).toFixed(1), 'Q score']}
                labelFormatter={(l) => `Iteration ${l}`}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="var(--chart-line-primary)"
                strokeWidth={2}
                dot={{ r: 4, fill: 'var(--chart-line-primary)' }}
                activeDot={{ r: 6 }}
                isAnimationActive
                label={{ position: 'top', fontSize: 11, fill: 'var(--color-ink-secondary)', formatter: (v: unknown) => Number(v).toFixed(1) }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <DimensionBreakdown iterations={scored} />
      <FindingsTimeline iterations={iterations} />
    </div>
  )
}
