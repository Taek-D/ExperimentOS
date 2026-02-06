import type {
  HealthCheckResult,
  AnalysisResult,
  BayesianInsights,
  MultiVariantBayesianInsights,
} from '../api/client';

/**
 * Pre-computed demo data for the interactive tutorial.
 * Based on a hypothetical demo_launch experiment:
 * - control: 10,000 users, 1,000 conversions (10%)
 * - treatment: 10,000 users, 1,200 conversions (12%)
 * - guardrail: error_count (no degradation)
 */

export const DEMO_HEALTH_RESULT: HealthCheckResult = {
  status: 'ok',
  result: {
    overall_status: 'Healthy',
    schema: { status: 'Healthy', issues: [] },
    srm: { status: 'Healthy', message: 'No SRM detected (p=0.999)', p_value: 0.999 },
  },
  preview: [
    { variant: 'control', users: 10000, conversions: 1000, error_count: 50 },
    { variant: 'treatment', users: 10000, conversions: 1200, error_count: 48 },
  ],
  columns: ['variant', 'users', 'conversions', 'error_count'],
  filename: 'demo_launch.csv',
};

export const DEMO_ANALYSIS_RESULT: AnalysisResult = {
  status: 'ok',
  primary_result: {
    control: { users: 10000, conversions: 1000, rate: 0.1 },
    treatment: { users: 10000, conversions: 1200, rate: 0.12 },
    absolute_lift: 0.02,
    relative_lift: 0.2,
    ci_95: [0.011, 0.029],
    p_value: 0.0001,
    is_significant: true,
  },
  guardrail_results: [
    {
      name: 'error_count',
      control_count: 50,
      treatment_count: 48,
      control_rate: 0.005,
      treatment_rate: 0.0048,
      delta: -0.0002,
      relative_lift: -0.04,
      worsened: false,
      severe: false,
      p_value: 0.87,
    },
  ],
};

export const DEMO_BAYESIAN_INSIGHTS: BayesianInsights = {
  conversion: {
    prob_treatment_beats_control: 0.9998,
    expected_loss: 0.000012,
    control_posterior: { alpha: 1001, beta: 9001 },
    treatment_posterior: { alpha: 1201, beta: 8801 },
  },
  continuous: {},
};

/**
 * Multi-variant demo data (3 variants).
 * - control: 10,000 users, 1,000 conversions (10%)
 * - variant_a: 10,000 users, 1,150 conversions (11.5%)
 * - variant_b: 10,000 users, 1,300 conversions (13%)
 * - guardrail: error_count, bounce_count
 */

export const DEMO_MULTIVARIANT_HEALTH: HealthCheckResult = {
  status: 'ok',
  result: {
    overall_status: 'Healthy',
    schema: { status: 'Healthy', issues: [] },
    srm: { status: 'Healthy', message: 'No SRM detected (p=0.985)', p_value: 0.985 },
  },
  preview: [
    { variant: 'control', users: 10000, conversions: 1000, error_count: 50, bounce_count: 250 },
    { variant: 'variant_a', users: 10000, conversions: 1150, error_count: 52, bounce_count: 245 },
    { variant: 'variant_b', users: 10000, conversions: 1300, error_count: 48, bounce_count: 240 },
  ],
  columns: ['variant', 'users', 'conversions', 'error_count', 'bounce_count'],
  filename: 'demo_multivariant.csv',
};

export const DEMO_MULTIVARIANT_ANALYSIS: AnalysisResult = {
  status: 'ok',
  is_multivariant: true,
  variant_count: 3,
  primary_result: {
    is_multivariant: true,
    overall: {
      chi2_stat: 25.6,
      p_value: 0.000003,
      dof: 2,
      is_significant: true,
    },
    control_stats: { users: 10000, conversions: 1000, rate: 0.1 },
    variants: {
      variant_a: {
        users: 10000,
        conversions: 1150,
        rate: 0.115,
        absolute_lift: 0.015,
        relative_lift: 0.15,
        ci_95: [0.006, 0.024],
        p_value: 0.001,
        p_value_corrected: 0.002,
        is_significant: true,
        is_significant_corrected: true,
      },
      variant_b: {
        users: 10000,
        conversions: 1300,
        rate: 0.13,
        absolute_lift: 0.03,
        relative_lift: 0.3,
        ci_95: [0.02, 0.04],
        p_value: 0.00001,
        p_value_corrected: 0.00002,
        is_significant: true,
        is_significant_corrected: true,
      },
    },
    correction_method: 'bonferroni',
    best_variant: 'variant_b',
    all_pairs: [
      {
        variant_a: 'control',
        variant_b: 'variant_a',
        absolute_lift: 0.015,
        p_value: 0.001,
        p_value_corrected: 0.003,
        is_significant_corrected: true,
      },
      {
        variant_a: 'control',
        variant_b: 'variant_b',
        absolute_lift: 0.03,
        p_value: 0.00001,
        p_value_corrected: 0.00003,
        is_significant_corrected: true,
      },
      {
        variant_a: 'variant_a',
        variant_b: 'variant_b',
        absolute_lift: 0.015,
        p_value: 0.001,
        p_value_corrected: 0.003,
        is_significant_corrected: true,
      },
    ],
  },
  guardrail_results: {
    by_variant: {
      variant_a: [
        {
          name: 'error_count',
          variant: 'variant_a',
          control_count: 50,
          treatment_count: 52,
          control_rate: 0.005,
          treatment_rate: 0.0052,
          delta: 0.0002,
          relative_lift: 0.04,
          worsened: false,
          severe: false,
          p_value: 0.85,
        },
        {
          name: 'bounce_count',
          variant: 'variant_a',
          control_count: 250,
          treatment_count: 245,
          control_rate: 0.025,
          treatment_rate: 0.0245,
          delta: -0.0005,
          relative_lift: -0.02,
          worsened: false,
          severe: false,
          p_value: 0.78,
        },
      ],
      variant_b: [
        {
          name: 'error_count',
          variant: 'variant_b',
          control_count: 50,
          treatment_count: 48,
          control_rate: 0.005,
          treatment_rate: 0.0048,
          delta: -0.0002,
          relative_lift: -0.04,
          worsened: false,
          severe: false,
          p_value: 0.87,
        },
        {
          name: 'bounce_count',
          variant: 'variant_b',
          control_count: 250,
          treatment_count: 240,
          control_rate: 0.025,
          treatment_rate: 0.024,
          delta: -0.001,
          relative_lift: -0.04,
          worsened: false,
          severe: false,
          p_value: 0.65,
        },
      ],
    },
    any_severe: false,
    any_worsened: false,
    summary: [
      { name: 'error_count', worst_variant: 'variant_a', worst_delta: 0.0002, severe: false, worsened: false },
      { name: 'bounce_count', worst_variant: 'variant_a', worst_delta: -0.0005, severe: false, worsened: false },
    ],
  },
};

export const DEMO_MULTIVARIANT_BAYESIAN: MultiVariantBayesianInsights = {
  conversion: {
    vs_control: {
      variant_a: {
        prob_beats_control: 0.975,
        expected_loss: 0.00035,
        posterior: { alpha: 1151, beta: 8851 },
      },
      variant_b: {
        prob_beats_control: 0.9999,
        expected_loss: 0.000008,
        posterior: { alpha: 1301, beta: 8701 },
      },
    },
    prob_being_best: {
      control: 0.002,
      variant_a: 0.12,
      variant_b: 0.878,
    },
    control_posterior: { alpha: 1001, beta: 9001 },
  },
  continuous: { by_variant: {} },
};
