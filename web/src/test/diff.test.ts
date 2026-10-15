import { describe, expect, it } from 'vitest'
import { wordDiff } from '../lib/diff'

describe('wordDiff', () => {
  it('marks unchanged text when strings are identical', () => {
    const result = wordDiff('hello world', 'hello world')
    expect(result.every((t) => t.type === 'unchanged')).toBe(true)
  })

  it('detects an added word', () => {
    const result = wordDiff('hello world', 'hello new world')
    expect(result.some((t) => t.type === 'added' && t.text.includes('new'))).toBe(true)
  })

  it('detects a removed word', () => {
    const result = wordDiff('hello old world', 'hello world')
    expect(result.some((t) => t.type === 'removed' && t.text.includes('old'))).toBe(true)
  })

  it('handles empty strings without throwing', () => {
    expect(() => wordDiff('', '')).not.toThrow()
    expect(wordDiff('', 'new text').some((t) => t.type === 'added')).toBe(true)
  })
})
