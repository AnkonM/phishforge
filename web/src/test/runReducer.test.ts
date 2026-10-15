import { describe, expect, it } from 'vitest'
import { buildViewStateFromRecord, initialRunViewState, runEventReducer } from '../lib/runReducer'
import type { RunEvent, RunRecord } from '../lib/types'

function reduceAll(events: RunEvent[]) {
  return events.reduce(runEventReducer, initialRunViewState)
}

describe('runEventReducer', () => {
  it('tracks a single-iteration PASS run through every stage', () => {
    const events: RunEvent[] = [
      { event: 'run_started', run_id: 'r1', ts: 't', condition: 'verifier_guided', demo_script: 'first_pass' },
      { event: 'iteration_started', run_id: 'r1', ts: 't', iteration: 1 },
      { event: 'generation_started', run_id: 'r1', ts: 't', iteration: 1 },
      {
        event: 'generation_complete',
        run_id: 'r1',
        ts: 't',
        iteration: 1,
        simulation: { subject: 's', sender: 'a@b.test', body: 'hi', metadata: {}, intended_indicators: [] } as never,
      },
      {
        event: 'safety_result',
        run_id: 'r1',
        ts: 't',
        iteration: 1,
        result: { passed: true, status: 'PASS', findings: [] },
      },
      {
        event: 'verification_result',
        run_id: 'r1',
        ts: 't',
        iteration: 1,
        result: { overall_score: 0, pass_fail: 'FAIL' } as never,
      },
      {
        event: 'score_result',
        run_id: 'r1',
        ts: 't',
        iteration: 1,
        overall_score: 92.1,
        pass_fail: 'PASS',
        result: { overall_score: 92.1, pass_fail: 'PASS' } as never,
      },
      { event: 'refinement_instruction', run_id: 'r1', ts: 't', iteration: 1, instructions: 'keep going', weaknesses: [] },
      { event: 'run_finished', run_id: 'r1', ts: 't', terminal_state: 'PASS', cancelled: false },
    ]
    const state = reduceAll(events)
    expect(state.finished).toBe(true)
    expect(state.terminalState).toBe('PASS')
    expect(state.stages).toEqual({
      generator: 'passed',
      safety: 'passed',
      verifier: 'passed',
      scoring: 'passed',
      refinement: 'passed',
    })
    expect(state.iterations).toHaveLength(1)
    expect(state.iterations[0].score).toBe(92.1)
  })

  it('replays the paper worked example: 72.8 -> 92.8 across two iterations', () => {
    const mkScore = (iteration: number, score: number, passFail: 'REVISE' | 'PASS'): RunEvent => ({
      event: 'score_result',
      run_id: 'r1',
      ts: 't',
      iteration,
      overall_score: score,
      pass_fail: passFail,
      result: { overall_score: score, pass_fail: passFail } as never,
    })
    const events: RunEvent[] = [
      { event: 'run_started', run_id: 'r1', ts: 't', condition: 'verifier_guided', demo_script: 'revise_pass' },
      { event: 'iteration_started', run_id: 'r1', ts: 't', iteration: 1 },
      mkScore(1, 72.8, 'REVISE'),
      { event: 'iteration_started', run_id: 'r1', ts: 't', iteration: 2 },
      mkScore(2, 92.8, 'PASS'),
      { event: 'run_finished', run_id: 'r1', ts: 't', terminal_state: 'PASS', cancelled: false },
    ]
    const state = reduceAll(events)
    expect(state.iterations.map((i) => i.score)).toEqual([72.8, 92.8])
    expect(state.terminalState).toBe('PASS')
  })

  it('skips verifier/scoring/refinement when the safety gate rejects', () => {
    const events: RunEvent[] = [
      { event: 'run_started', run_id: 'r1', ts: 't', condition: 'verifier_guided', demo_script: 'safety_reject' },
      { event: 'iteration_started', run_id: 'r1', ts: 't', iteration: 1 },
      {
        event: 'safety_result',
        run_id: 'r1',
        ts: 't',
        iteration: 1,
        result: { passed: false, status: 'FAIL', findings: ['real brand impersonation'] },
      },
      { event: 'run_finished', run_id: 'r1', ts: 't', terminal_state: 'REJECTED_UNSAFE', cancelled: false },
    ]
    const state = reduceAll(events)
    expect(state.stages.safety).toBe('failed')
    expect(state.stages.verifier).toBe('skipped')
    expect(state.stages.scoring).toBe('skipped')
    expect(state.stages.refinement).toBe('skipped')
    expect(state.terminalState).toBe('REJECTED_UNSAFE')
  })

  it('marks the generator failed on a generation error', () => {
    const events: RunEvent[] = [
      { event: 'run_started', run_id: 'r1', ts: 't', condition: 'verifier_guided', demo_script: null },
      { event: 'iteration_started', run_id: 'r1', ts: 't', iteration: 1 },
      { event: 'error', run_id: 'r1', ts: 't', iteration: 1, stage: 'generation', message: 'boom' },
      { event: 'run_finished', run_id: 'r1', ts: 't', terminal_state: 'GENERATION_FAILURE', cancelled: false },
    ]
    const state = reduceAll(events)
    expect(state.stages.generator).toBe('failed')
    expect(state.errors).toHaveLength(1)
    expect(state.terminalState).toBe('GENERATION_FAILURE')
  })
})

describe('buildViewStateFromRecord', () => {
  it('produces an equivalent view for a stored PASS record', () => {
    const record: RunRecord = {
      run_id: 'r1',
      scenario: {
        organization_context: 'x',
        target_role: 'it',
        scenario_type: 'password_alert',
        difficulty: 1,
        language: 'en',
        desired_indicators: ['urgency'],
        prohibited_elements: [],
        simulation_constraints: {},
      },
      condition: 'verifier_guided',
      terminal_state: 'PASS',
      created_at: '2026-01-01T00:00:00Z',
      iterations: [
        {
          iteration_number: 1,
          simulation: null,
          safety_result: { passed: true, status: 'PASS', findings: [] },
          verification: { overall_score: 92.1, pass_fail: 'PASS' } as never,
          score: 92.1,
          refinement: { termination_reason: 'PASS' } as never,
        },
      ],
    }
    const state = buildViewStateFromRecord(record)
    expect(state.finished).toBe(true)
    expect(state.terminalState).toBe('PASS')
    expect(state.iterations[0].score).toBe(92.1)
    expect(state.stages.safety).toBe('passed')
  })

  it('handles a single-iteration run as a clean "converged on first attempt" state', () => {
    const record: RunRecord = {
      run_id: 'r2',
      scenario: {
        organization_context: 'x',
        target_role: 'it',
        scenario_type: 'password_alert',
        difficulty: 1,
        language: 'en',
        desired_indicators: [],
        prohibited_elements: [],
        simulation_constraints: {},
      },
      condition: 'verifier_guided',
      terminal_state: 'PASS',
      created_at: '2026-01-01T00:00:00Z',
      iterations: [
        {
          iteration_number: 1,
          simulation: null,
          safety_result: { passed: true, status: 'PASS', findings: [] },
          verification: { overall_score: 95, pass_fail: 'PASS' } as never,
          score: 95,
          refinement: { termination_reason: 'PASS' } as never,
        },
      ],
    }
    const state = buildViewStateFromRecord(record)
    expect(state.iterations).toHaveLength(1)
  })

  it('handles a REJECTED_UNSAFE record with no score', () => {
    const record: RunRecord = {
      run_id: 'r3',
      scenario: {
        organization_context: 'x',
        target_role: 'it',
        scenario_type: 'password_alert',
        difficulty: 1,
        language: 'en',
        desired_indicators: [],
        prohibited_elements: [],
        simulation_constraints: {},
      },
      condition: 'verifier_guided',
      terminal_state: 'REJECTED_UNSAFE',
      created_at: '2026-01-01T00:00:00Z',
      iterations: [
        {
          iteration_number: 1,
          simulation: null,
          safety_result: { passed: false, status: 'FAIL', findings: ['x'] },
          verification: null,
          score: null,
          refinement: null,
        },
      ],
    }
    const state = buildViewStateFromRecord(record)
    expect(state.iterations[0].score).toBeNull()
    expect(state.stages.verifier).toBe('skipped')
  })
})
