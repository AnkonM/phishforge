import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BenchmarkRunner } from '../components/BenchmarkRunner'
import { KpiCard } from '../components/KpiCard'
import { EmptyState, ErrorState, PageSkeleton } from '../components/Skeletons'
import { formatCondition, formatPercent, formatRole, formatScore } from '../lib/format'
import { api } from '../lib/api'

function chartTooltipStyle() {
  return {
    contentStyle: {
      background: 'var(--chart-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 8,
      fontSize: 12,
    },
  }
}

export function Dashboard() {
  const { data: stats, isLoading, error, refetch } = useQuery({ queryKey: ['stats'], queryFn: api.stats })

  if (isLoading) return <PageSkeleton />
  if (error || !stats) return <ErrorState message="Could not load dashboard stats." />
  if (stats.total_runs === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-lg font-semibold">Dashboard</h1>
        <EmptyState title="No runs yet" hint="Run a scenario from Studio, or use the benchmark runner below." />
        <BenchmarkRunner onFinished={refetch} />
      </div>
    )
  }

  const conditions = Object.keys(stats.terminal_state_distribution)
  const allStates = Array.from(new Set(conditions.flatMap((c) => Object.keys(stats.terminal_state_distribution[c]))))
  const terminalChartData = allStates.map((state) => {
    const row: Record<string, string | number> = { state }
    for (const c of conditions) row[c] = stats.terminal_state_distribution[c][state] ?? 0
    return row
  })

  const leakageData = conditions.map((c) => ({
    condition: formatCondition(c),
    rate: stats.safety_leakage[c]?.rate_pct ?? 0,
  }))

  const qualityDims = ['realism_score', 'relevance_score', 'indicator_score', 'difficulty_score', 'language_score'] as const
  const qualityData = qualityDims.map((dim) => {
    const row: Record<string, string | number> = { dimension: dim.replace('_score', '') }
    for (const c of conditions) row[c] = stats.quality_by_condition[c]?.[dim] ?? 0
    return row
  })

  return (
    <div className="space-y-8">
      <h1 className="text-lg font-semibold" style={{ color: 'var(--color-ink)' }}>
        Dashboard
      </h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <KpiCard label="Total runs" value={String(stats.total_runs)} />
        <KpiCard label="Pass rate" value={formatPercent(stats.pass_rate_pct)} />
        <KpiCard label="Rejected unsafe" value={formatPercent(stats.rejected_unsafe_rate_pct)} />
        <KpiCard label="Mean iterations" value={stats.mean_iterations.toFixed(1)} />
        <KpiCard label="Mean final Q" value={formatScore(stats.mean_final_score)} />
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
          Terminal-state distribution, by mode
        </h2>
        <div className="h-64 rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={terminalChartData}>
              <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
              <XAxis dataKey="state" tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" />
              <YAxis tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" allowDecimals={false} />
              <Tooltip {...chartTooltipStyle()} />
              <Legend formatter={(v) => formatCondition(String(v))} wrapperStyle={{ fontSize: 12 }} />
              {conditions.map((c, i) => (
                <Bar key={c} dataKey={c} name={c} fill={i === 0 ? 'var(--color-signal)' : 'var(--color-forge)'} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section>
        <h2 className="mb-1 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
          Safety leakage: unsafe but would have been approved
        </h2>
        <p className="mb-3 text-xs" style={{ color: 'var(--color-ink-muted)' }}>
          Computed from your stored runs (N={stats.total_runs}) — descriptive only, not the paper's benchmark figure.
        </p>
        <div className="h-48 rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={leakageData} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid stroke="var(--chart-grid)" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" />
              <YAxis dataKey="condition" type="category" tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" width={110} />
              <Tooltip {...chartTooltipStyle()} formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Leakage rate']} />
              <Bar dataKey="rate" fill="var(--color-rejected-unsafe)" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
          Quality by condition (mean per dimension)
        </h2>
        <div className="h-64 rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={qualityData}>
              <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
              <XAxis dataKey="dimension" tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" />
              <YAxis domain={[0, 100]} tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" />
              <Tooltip {...chartTooltipStyle()} />
              <Legend formatter={(v) => formatCondition(String(v))} wrapperStyle={{ fontSize: 12 }} />
              {conditions.map((c, i) => (
                <Bar key={c} dataKey={c} name={c} fill={i === 0 ? 'var(--color-signal)' : 'var(--color-forge)'} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
            Score distribution
          </h2>
          <div className="h-48 rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.score_histogram}>
                <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                <XAxis dataKey="bucket" tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" />
                <YAxis tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" allowDecimals={false} />
                <Tooltip {...chartTooltipStyle()} />
                <Bar dataKey="count" fill="var(--color-signal)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section>
          <h2 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
            Iterations to converge
          </h2>
          <div className="h-48 rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.iterations_histogram}>
                <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                <XAxis dataKey="iterations" tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" />
                <YAxis tick={{ fill: 'var(--chart-text-muted)', fontSize: 11 }} stroke="var(--chart-axis)" allowDecimals={false} />
                <Tooltip {...chartTooltipStyle()} />
                <Bar dataKey="count" fill="var(--color-forge)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
            By role
          </h2>
          <BreakdownTable data={stats.by_role} labelFn={(k) => formatRole(k)} />
        </section>
        <section>
          <h2 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
            By difficulty
          </h2>
          <BreakdownTable data={stats.by_difficulty} labelFn={(k) => `Level ${k}`} />
        </section>
      </div>

      <section>
        <BenchmarkRunner onFinished={refetch} />
      </section>

      <p className="text-xs" style={{ color: 'var(--color-ink-muted)' }}>
        {stats.n_note}
      </p>
    </div>
  )
}

function BreakdownTable({
  data,
  labelFn,
}: {
  data: Record<string, { mean_score: number; pass_rate_pct: number; total: number }>
  labelFn: (key: string) => string
}) {
  const entries = Object.entries(data)
  if (entries.length === 0) return <EmptyState title="No data" />
  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b text-xs" style={{ borderColor: 'var(--color-border)', color: 'var(--color-ink-muted)' }}>
          <th className="py-1.5 font-medium">Group</th>
          <th className="py-1.5 font-medium">N</th>
          <th className="py-1.5 font-medium">Mean Q</th>
          <th className="py-1.5 font-medium">Pass rate</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([key, v]) => (
          <tr key={key} className="border-b" style={{ borderColor: 'var(--color-border)' }}>
            <td className="py-1.5">{labelFn(key)}</td>
            <td className="py-1.5 font-mono">{v.total}</td>
            <td className="py-1.5 font-mono">{formatScore(v.mean_score)}</td>
            <td className="py-1.5 font-mono">{formatPercent(v.pass_rate_pct)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
