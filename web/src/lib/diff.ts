import { diffWords } from 'diff'

export interface DiffToken {
  text: string
  type: 'added' | 'removed' | 'unchanged'
}

/** Word-level diff between two plain-text strings (email subject/body). */
export function wordDiff(before: string, after: string): DiffToken[] {
  const parts = diffWords(before ?? '', after ?? '')
  return parts.map((part) => ({
    text: part.value,
    type: part.added ? 'added' : part.removed ? 'removed' : 'unchanged',
  }))
}
