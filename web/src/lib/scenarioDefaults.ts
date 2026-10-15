import type { ScenarioSpecification } from './types'

export interface FormErrors {
  [field: string]: string
}

export function validateScenario(spec: ScenarioSpecification): FormErrors {
  const errors: FormErrors = {}
  if (!spec.organization_context.trim()) errors.organization_context = 'Organization context is required.'
  if (spec.desired_indicators.length === 0) errors.desired_indicators = 'At least one indicator is required.'
  return errors
}

export const EMPTY_SCENARIO: ScenarioSpecification = {
  organization_context: '',
  target_role: 'it',
  scenario_type: 'password_alert',
  difficulty: 1,
  language: 'en',
  desired_indicators: [],
  prohibited_elements: [],
  simulation_constraints: {},
}
