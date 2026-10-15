import { useCallback, useEffect, useState } from 'react'

export type ThemePreference = 'system' | 'light' | 'dark'
const STORAGE_KEY = 'phishforge-console-theme'

function readStored(): ThemePreference {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'light' || v === 'dark' || v === 'system') return v
  } catch {
    // localStorage unavailable (private mode, etc.) -- fall back to system
  }
  return 'system'
}

export function useTheme(): [ThemePreference, (pref: ThemePreference) => void] {
  const [pref, setPref] = useState<ThemePreference>(readStored)

  useEffect(() => {
    const root = document.documentElement
    if (pref === 'system') {
      root.removeAttribute('data-theme')
    } else {
      root.setAttribute('data-theme', pref)
    }
  }, [pref])

  const update = useCallback((next: ThemePreference) => {
    setPref(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // ignore -- per-viewer convenience only
    }
  }, [])

  return [pref, update]
}
