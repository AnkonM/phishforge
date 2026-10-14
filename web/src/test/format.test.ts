import { describe, expect, it } from 'vitest'
import {
  formatDifficulty,
  formatPercent,
  formatRole,
  formatScenarioType,
  formatScore,
  terminalStateInfo,
} from '../lib/format'

describe('formatScore', () => {
  it('renders an em-dash for null/undefined', () => {
    expect(formatScore(null)).toBe('—')
    expect(formatScore(undefined)).toBe('—')
  })
  it('renders one decimal place', () => {
    expect(formatScore(72.8)).toBe('72.8')
    expect(formatScore(100)).toBe('100.0')
  })
})

describe('formatPercent', () => {
  it('appends % with one decimal', () => {
    expect(formatPercent(25)).toBe('25.0%')
    expect(formatPercent(33.33)).toBe('33.3%')
  })
})

describe('formatRole / formatScenarioType / formatDifficulty', () => {
  it('maps role codes to display labels', () => {
    expect(formatRole('it')).toBe('IT')
    expect(formatRole('hr')).toBe('HR')
  })
  it('title-cases scenario type slugs', () => {
    expect(formatScenarioType('password_alert')).toBe('Password Alert')
    expect(formatScenarioType('invoice_fraud')).toBe('Invoice Fraud')
  })
  it('includes the rubric label for each difficulty level', () => {
    expect(formatDifficulty(1)).toContain('Obvious')
    expect(formatDifficulty(4)).toContain('Expert')
  })
})

describe('terminalStateInfo', () => {
  it('has an entry for every terminal state the pipeline can produce', () => {
    for (const state of ['PASS', 'REJECTED_UNSAFE', 'GENERATION_FAILURE', 'FAILED_TO_CONVERGE', 'GENERATED_UNVERIFIED']) {
      const info = terminalStateInfo(state)
      expect(info.label).not.toBe('')
      expect(info.description).not.toBe('')
    }
  })
  it('falls back gracefully for an unknown state', () => {
    const info = terminalStateInfo('SOMETHING_NEW')
    expect(info.label).toBe('SOMETHING_NEW')
  })
})
