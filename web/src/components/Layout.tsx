import { BarChart3, Beaker, ChevronsLeft, ChevronsRight, Settings as SettingsIcon, Workflow } from 'lucide-react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useSidebar } from '../hooks/useSidebar'
import { ThemeToggle } from './ThemeToggle'

const NAV = [
  { to: '/', label: 'Studio', icon: Beaker },
  { to: '/runs', label: 'Runs', icon: Workflow },
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { to: '/settings', label: 'Settings & About', icon: SettingsIcon },
]

export function Layout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useSidebar()

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-[var(--color-surface)] focus:p-2"
      >
        Skip to content
      </a>
      <nav
        className={`flex shrink-0 flex-row items-center gap-4 border-b px-4 py-3 lg:flex-col lg:items-stretch lg:gap-1 lg:border-b-0 lg:border-r lg:py-5 lg:transition-[width] lg:duration-200 motion-reduce:lg:transition-none ${
          collapsed ? 'lg:w-16 lg:px-2' : 'lg:w-56 lg:px-3'
        }`}
        style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        aria-label="Primary"
      >
        <div
          className="mb-4 hidden items-center lg:flex"
          style={collapsed ? { justifyContent: 'center' } : { justifyContent: 'space-between' }}
        >
          {!collapsed && (
            <p className="truncate px-2 text-sm font-semibold" style={{ color: 'var(--color-ink)' }}>
              PhishForge Console
            </p>
          )}
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] hover:bg-[var(--color-page)]"
            style={{ color: 'var(--color-ink-muted)' }}
          >
            {collapsed ? <ChevronsRight size={15} aria-hidden /> : <ChevronsLeft size={15} aria-hidden />}
          </button>
        </div>

        <div className="flex flex-1 flex-row gap-1 lg:flex-col">
          {NAV.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-[var(--radius-md)] px-2.5 py-2 text-sm font-medium transition-colors ${
                    isActive ? '' : 'hover:bg-[var(--color-page)]'
                  } ${collapsed ? 'lg:justify-center' : ''}`
                }
                style={({ isActive }) =>
                  isActive
                    ? { background: 'var(--color-page)', color: 'var(--color-signal)' }
                    : { color: 'var(--color-ink-secondary)' }
                }
              >
                <Icon size={16} aria-hidden />
                <span className={collapsed ? 'sm:inline lg:hidden' : 'hidden sm:inline'}>{item.label}</span>
              </NavLink>
            )
          })}
        </div>
        <div className={`hidden lg:flex ${collapsed ? 'justify-center' : ''}`}>
          <ThemeToggle />
        </div>
      </nav>
      <main id="main-content" className="flex-1 px-4 py-5 lg:px-8 lg:py-6">
        {children}
      </main>
    </div>
  )
}
