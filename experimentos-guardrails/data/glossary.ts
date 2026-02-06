export interface GlossaryEntry {
  term: string;
  shortDescription: string;
  longDescription: string;
}

export const GLOSSARY: Record<string, GlossaryEntry> = {
  'p-value': {
    term: 'P-Value',
    shortDescription: 'The probability of observing this result (or more extreme) if there were no real difference.',
    longDescription:
      'A p-value below 0.05 means there is less than a 5% chance the observed difference is due to random variation alone. Lower p-values provide stronger evidence against the null hypothesis. However, p-value does not measure effect size or practical significance.',
  },
  ci: {
    term: 'Confidence Interval (CI)',
    shortDescription: 'A range of plausible values for the true effect size, typically at 95% confidence.',
    longDescription:
      'If you repeated this experiment many times, 95% of computed intervals would contain the true effect. When the CI does not cross zero, the result is statistically significant. Wider intervals indicate more uncertainty.',
  },
  srm: {
    term: 'SRM (Sample Ratio Mismatch)',
    shortDescription: 'A check that traffic was split as expected between variants.',
    longDescription:
      'SRM detects whether the actual user counts deviate from the planned split (e.g., 50/50). A significant SRM (p < 0.01) indicates a data quality issue such as bot filtering, bucketing bugs, or logging errors. Results should not be trusted when SRM is detected.',
  },
  lift: {
    term: 'Lift',
    shortDescription: 'The relative change in conversion rate from control to treatment.',
    longDescription:
      'Lift = (Treatment Rate - Control Rate) / Control Rate. A lift of +20% means the treatment group converted 20% more than control. Relative lift is preferred over absolute lift for comparing experiments with different baseline rates.',
  },
  delta: {
    term: 'Delta',
    shortDescription: 'The absolute difference between treatment and control rates.',
    longDescription:
      'Delta measures the raw difference: Treatment Rate - Control Rate. For primary metrics this is shown as relative lift (%), while for guardrails it is typically shown in percentage points (pp) to highlight even small absolute changes.',
  },
  guardrail: {
    term: 'Guardrail',
    shortDescription: 'A secondary metric that must not degrade when shipping a change.',
    longDescription:
      'Guardrails protect against unintended side effects. Common guardrails include error rates, latency, and revenue. A "severe" guardrail violation (significant worsening beyond threshold) can block a launch even if the primary metric improves.',
  },
  'bayesian-probability': {
    term: 'Bayesian Probability',
    shortDescription: 'The probability that the treatment is better than the control.',
    longDescription:
      'Computed via Monte Carlo simulation of posterior distributions. Unlike p-values, Bayesian probability directly answers "how likely is treatment better?" A value of 99.9% means there is very high confidence that treatment outperforms control. In ExperimentOS, Bayesian results are informational and do not influence the automated decision.',
  },
  'expected-loss': {
    term: 'Expected Loss',
    shortDescription: 'The expected cost (in conversion rate) of choosing treatment if it is actually worse.',
    longDescription:
      'Expected loss quantifies the risk of a wrong decision. A low expected loss (e.g., 0.001%) means that even if treatment is worse, the cost is negligible. Combined with high Bayesian probability, low expected loss suggests a safe-to-ship experiment.',
  },
  power: {
    term: 'Statistical Power',
    shortDescription: 'The probability of detecting a real effect if one exists.',
    longDescription:
      'Power of 80% means there is an 80% chance of declaring significance when the true effect matches the MDE. Higher power requires larger sample sizes. Use the Power Calculator to determine the required sample size before starting an experiment.',
  },
  mde: {
    term: 'MDE (Minimum Detectable Effect)',
    shortDescription: 'The smallest effect size your experiment is designed to detect.',
    longDescription:
      'MDE is chosen before the experiment starts, based on business impact. A smaller MDE requires more users but catches subtler improvements. For example, an MDE of 2% means the experiment can reliably detect a 2% or larger relative lift.',
  },
};

export const getGlossaryEntry = (key: string): GlossaryEntry | undefined => {
  return GLOSSARY[key];
};
