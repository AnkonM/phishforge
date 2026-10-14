import { BarChart3, Beaker, Settings as SettingsIcon, Workflow } from 'lucide-react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { ThemeToggle } from './ThemeToggle'

const NAV = [
  { to: '/', label: 'Studio', icon: Beaker },
  { to: '/runs', label: 'Runs', icon: Workflow },
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { to: '/settings', label: 'Settings & About', icon: SettingsIcon },
]

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-[var(--color-surface)] focus:p-2"
      >
        Skip to content
      </a>
      <nav
        className="flex shrink-0 flex-row items-center gap-4 border-b px-4 py-3 lg:w-56 lg:flex-col lg:items-stretch lg:gap-1 lg:border-b-0 lg:border-r lg:px-3 lg:py-5"
        style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
        aria-label="Primary"
      >
        <p className="hidden px-2 pb-4 text-sm font-semibold lg:block" style={{ color: 'var(--color-ink)' }}>
          PhishForge Console
        </p>
        <div className="flex flex-1 flex-row gap-1 lg:flex-col">
          {NAV.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-[var(--radius-md)] px-2.5 py-2 text-sm font-medium transition-colors ${
                    isActive ? '' : 'hover:bg-[var(--color-page)]'
                  }`
                }
                style={({ isActive }) =>
                  isActive
                    ? { background: 'var(--color-page)', color: 'var(--color-signal)' }
                    : { color: 'var(--color-ink-secondary)' }
                }
              >
                <Icon size={16} aria-hidden />
                <span className="hidden sm:inline">{item.label}</span>
              </NavLink>
            )
          })}
        </div>
        <div className="hidden lg:block">
          <ThemeToggle />
        </div>
      </nav>
      <main id="main-content" className="flex-1 px-4 py-5 lg:px-8 lg:py-6">
        {children}
      </main>
    </div>
  )
}
