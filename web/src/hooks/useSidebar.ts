import { useCallback, useState } from 'react'

const STORAGE_KEY = 'phishforge-console-sidebar-collapsed'

function readStored(): boolean {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'true') return true
    if (v === 'false') return false
  } catch {
    // localStorage unavailable -- fall back to default
  }
  return true // collapsed by default
}

export function useSidebar(): [boolean, (collapsed: boolean) => void] {
  const [collapsed, setCollapsed] = useState<boolean>(readStored)

  const update = useCallback((next: boolean) => {
    setCollapsed(next)
    try {
      localStorage.setItem(STORAGE_KEY, String(next))
    } catch {
      // ignore -- per-viewer convenience only
    }
  }, [])

  return [collapsed, update]
}
