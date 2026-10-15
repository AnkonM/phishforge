import type { ReactNode } from 'react'

/** Standard page shell: the Layout's <main> is a fixed-height, non-scrolling
 * region (so the sidebar never scrolls away) -- each ordinary page (every
 * page except Studio, which manages its own split-pane scrolling) opts into
 * scrolling here, with the padding that used to live on <main> itself. */
export function PageScroll({ children }: { children: ReactNode }) {
  return <div className="h-full overflow-y-auto px-4 py-5 lg:px-8 lg:py-6">{children}</div>
}
