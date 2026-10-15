import { useQuery, useQueryClient } from '@tanstack/react-query'
import { GitCompare, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { RunsTable } from '../components/RunsTable'
import { EmptyState, ErrorState, TableSkeleton } from '../components/Skeletons'
import { api } from '../lib/api'
import type { ScenarioSpecification } from '../lib/types'

export function Runs() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ state: '', role: '', difficulty: '', mode: '', q: '' })
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const { data: runs, isLoading, error } = useQuery({
    queryKey: ['runs', filters],
    queryFn: () =>
      api.listRuns({
        state: filters.state || undefined,
        role: filters.role || undefined,
        difficulty: filters.difficulty ? Number(filters.difficulty) : undefined,
        mode: filters.mode || undefined,
        q: filters.q || undefined,
      }),
  })

  function toggleSelect(id: string) {
    setSelected((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else {
        if (next.size >= 2) next.clear()
        next.add(id)
      }
      return next
    })
  }

  async function handleDeleteSelected() {
    for (const id of selected) {
      await api.deleteRun(id)
    }
    setSelected(new Set())
    queryClient.invalidateQueries({ queryKey: ['runs'] })
    queryClient.invalidateQueries({ queryKey: ['stats'] })
  }

  async function handleDeleteOne(id: string) {
    await api.deleteRun(id)
    queryClient.invalidateQueries({ queryKey: ['runs'] })
    queryClient.invalidateQueries({ queryKey: ['stats'] })
  }

  async function handleRerun(id: string) {
    const detail = await api.getRun(id)
    const spec: ScenarioSpecification = detail.record.scenario
    const mode = detail.record.condition === 'baseline_direct' ? 'direct' : 'guided'
    const resp = await api.createRun(spec, mode)
    navigate(`/runs/${resp.run_id}`)
  }

  function handleCompareSelected() {
    if (selected.size === 2) {
      const [a, b] = Array.from(selected)
      navigate(`/runs/${a}?compareWith=${b}`)
    }
  }

  async function handleDownload(id: string) {
    const detail = await api.getRun(id)
    const blob = new Blob([JSON.stringify(detail.record, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold" style={{ color: 'var(--color-ink)' }}>
          Runs
        </h1>
        {selected.size > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <span style={{ color: 'var(--color-ink-muted)' }}>{selected.size} selected</span>
            {selected.size === 2 && (
              <button type="button" onClick={handleCompareSelected} className="flex items-center gap-1 rounded border px-2 py-1" style={{ borderColor: 'var(--color-border)' }}>
                <GitCompare size={14} aria-hidden /> Compare
              </button>
            )}
            <button type="button" onClick={handleDeleteSelected} className="flex items-center gap-1 rounded border px-2 py-1" style={{ borderColor: 'var(--color-border)', color: 'var(--color-rejected-unsafe)' }}>
              <Trash2 size={14} aria-hidden /> Delete
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <select
          className="rounded border px-2 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={filters.state}
          onChange={(e) => setFilters((f) => ({ ...f, state: e.target.value }))}
          aria-label="Filter by terminal state"
        >
          <option value="">All states</option>
          {['PASS', 'REJECTED_UNSAFE', 'FAILED_TO_CONVERGE', 'GENERATION_FAILURE', 'GENERATED_UNVERIFIED'].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          className="rounded border px-2 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={filters.role}
          onChange={(e) => setFilters((f) => ({ ...f, role: e.target.value }))}
          aria-label="Filter by role"
        >
          <option value="">All roles</option>
          {['finance', 'hr', 'it', 'sales', 'operations', 'executive'].map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <select
          className="rounded border px-2 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={filters.mode}
          onChange={(e) => setFilters((f) => ({ ...f, mode: e.target.value }))}
          aria-label="Filter by mode"
        >
          <option value="">All modes</option>
          <option value="verifier_guided">Verifier-guided</option>
          <option value="baseline_direct">Direct baseline</option>
        </select>
        <select
          className="rounded border px-2 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          value={filters.difficulty}
          onChange={(e) => setFilters((f) => ({ ...f, difficulty: e.target.value }))}
          aria-label="Filter by difficulty"
        >
          <option value="">All difficulties</option>
          {[1, 2, 3, 4].map((d) => (
            <option key={d} value={d}>
              Level {d}
            </option>
          ))}
        </select>
        <input
          className="min-w-[160px] flex-1 rounded border px-2 py-1.5 text-sm"
          style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
          placeholder="Search org context, scenario type, run id…"
          value={filters.q}
          onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
        />
      </div>

      {isLoading && <TableSkeleton />}
      {error && <ErrorState message="Could not load runs." />}
      {runs && runs.length === 0 && <EmptyState title="No runs yet" hint="Start one from Studio, or run the Dashboard's benchmark." />}
      {runs && runs.length > 0 && (
        <RunsTable
          runs={runs}
          selected={selected}
          onToggleSelect={toggleSelect}
          onRerun={handleRerun}
          onDownload={handleDownload}
          onDelete={handleDeleteOne}
        />
      )}
    </div>
  )
}
