import React from 'react';
import Icon from './Icon';

interface LandingPageProps {
  onGetStarted: () => void;
  onLoadDemo: () => void;
}

const STATS = [
  { value: '99.9%', label: 'SRM Detection Rate', icon: 'verified' },
  { value: '5x', label: 'Faster Decisions', icon: 'speed' },
  { value: '209+', label: 'Test Coverage', icon: 'check_circle' },
  { value: '<2s', label: 'Analysis Time', icon: 'timer' },
];

const FEATURES = [
  {
    icon: 'health_and_safety',
    title: 'Automated Health Check',
    description: 'Schema validation and SRM detection catch data issues before they invalidate your experiment. No more shipping on broken data.',
    accent: 'primary',
  },
  {
    icon: 'shield',
    title: 'Guardrail Monitoring',
    description: 'Track safety metrics alongside your primary KPI. Get instant alerts when guardrails breach severity thresholds.',
    accent: 'warning',
  },
  {
    icon: 'description',
    title: 'Decision Memo',
    description: 'Auto-generated decision documents with statistical evidence, guardrail status, and clear launch/hold/rollback recommendations.',
    accent: 'info',
  },
  {
    icon: 'calculate',
    title: 'Power Calculator',
    description: 'Calculate required sample sizes for conversion and continuous metrics. Know exactly when your experiment has enough data.',
    accent: 'secondary',
  },
  {
    icon: 'monitoring',
    title: 'Sequential Testing',
    description: "O'Brien-Fleming boundaries let you peek at results without inflating false positive rates. Stop early with confidence.",
    accent: 'success',
  },
  {
    icon: 'insights',
    title: 'Bayesian Insights',
    description: 'Posterior distributions and probability of beating control — intuitive supplements to your frequentist primary analysis.',
    accent: 'danger',
  },
];

const STEPS = [
  { num: '01', title: 'Upload or Connect', description: 'Drop a CSV or connect your experiment platform (Statsig, GrowthBook) with one click.' },
  { num: '02', title: 'Automated Analysis', description: 'Health check, frequentist tests, guardrails, and Bayesian insights — all computed in seconds.' },
  { num: '03', title: 'Ship with Confidence', description: 'Get a clear Launch / Hold / Rollback decision backed by statistical evidence and guardrail checks.' },
];

const accentColor: Record<string, string> = {
  primary: 'text-primary bg-primary/10 border-primary/15',
  warning: 'text-warning bg-warning/10 border-warning/15',
  info: 'text-info bg-info/10 border-info/15',
  secondary: 'text-secondary bg-secondary/10 border-secondary/15',
  success: 'text-success bg-success/10 border-success/15',
  danger: 'text-danger bg-danger/10 border-danger/15',
};

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onLoadDemo }) => {
  return (
    <div className="min-h-screen bg-app-bg overflow-x-hidden" role="main">
      {/* ─── Hero ─── */}
      <section aria-label="Hero" className="relative min-h-[90vh] flex flex-col items-center justify-center px-6 py-24 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 grid-pattern" />
        <div className="absolute inset-0 hero-glow" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-[120px] animate-glow-pulse" />

        <div className="relative z-10 max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/8 border border-primary/15 text-primary text-xs font-semibold mb-8 animate-fade-in-up">
            <Icon name="science" size={14} />
            <span>A/B Test Decision Engine</span>
            <span className="w-1 h-1 rounded-full bg-primary/40" />
            <span className="text-primary/60">v2.4</span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6 animate-fade-in-up stagger-1">
            <span className="gradient-text">Ship experiments</span>
            <br />
            <span className="gradient-text">with </span>
            <span className="gradient-text-primary">confidence</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg sm:text-xl text-white/45 max-w-2xl mx-auto leading-relaxed mb-10 animate-fade-in-up stagger-2">
            Statistical rigor meets engineering speed. ExperimentOS automates
            health checks, guardrail monitoring, and decision memos for every A/B test.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up stagger-3">
            <button onClick={onGetStarted} className="btn-primary-lg group focus-ring">
              <span className="flex items-center gap-2">
                Start Analyzing
                <Icon name="arrow_forward" size={18} className="group-hover:translate-x-0.5 transition-transform" />
              </span>
            </button>
            <button onClick={onLoadDemo} className="btn-ghost-lg group focus-ring">
              <span className="flex items-center gap-2">
                <Icon name="play_circle" size={18} className="text-white/40 group-hover:text-primary transition-colors" />
                View Demo
              </span>
            </button>
          </div>
        </div>

        {/* Dashboard Preview Card */}
        <div className="relative z-10 mt-16 w-full max-w-5xl mx-auto animate-fade-in-up stagger-4">
          <div className="relative">
            {/* Glow effect behind card */}
            <div className="absolute -inset-4 bg-primary/5 rounded-3xl blur-2xl" />

            {/* Preview card */}
            <div className="relative glass-card overflow-hidden rounded-2xl border border-white/8 shadow-hero">
              {/* Fake browser chrome */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/6 bg-surface-0/80">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-white/10" />
                  <span className="w-3 h-3 rounded-full bg-white/10" />
                  <span className="w-3 h-3 rounded-full bg-white/10" />
                </div>
                <div className="flex-1 flex justify-center">
                  <span className="text-[10px] font-mono text-white/25 bg-white/[0.03] px-4 py-1 rounded-full">app.experimentos.dev</span>
                </div>
              </div>

              {/* Dashboard mockup content */}
              <div className="p-6 sm:p-8 space-y-4">
                {/* Top row: stats cards mockup */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'Primary Lift', value: '+5.23%', color: 'text-primary' },
                    { label: 'P-Value', value: '0.0012', color: 'text-white' },
                    { label: 'Guardrails', value: '3 / 3', color: 'text-primary' },
                  ].map((card) => (
                    <div key={card.label} className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.04]">
                      <div className="text-white/30 text-[10px] font-mono uppercase tracking-wider mb-2">{card.label}</div>
                      <div className={`text-xl sm:text-2xl font-mono font-bold ${card.color}`}>{card.value}</div>
                    </div>
                  ))}
                </div>

                {/* Table mockup */}
                <div className="rounded-xl border border-white/[0.04] overflow-hidden">
                  <div className="grid grid-cols-5 gap-4 px-4 py-2.5 bg-surface-1/80 text-[9px] sm:text-[10px] font-mono uppercase tracking-widest text-white/25">
                    <span>Metric</span><span className="text-right">Baseline</span><span className="text-right">Variant</span><span className="text-right">Delta</span><span className="text-right">Status</span>
                  </div>
                  {[
                    { name: 'Conversion Rate', baseline: '4.21%', variant: '4.43%', delta: '+5.23%', status: 'sig' },
                    { name: 'Revenue / User', baseline: '$2.41', variant: '$2.38', delta: '-1.24%', status: 'ok' },
                    { name: 'Bounce Rate', baseline: '32.1%', variant: '31.8%', delta: '-0.93%', status: 'ok' },
                  ].map((row) => (
                    <div key={row.name} className="grid grid-cols-5 gap-4 px-4 py-3 border-t border-white/[0.03] text-xs sm:text-sm">
                      <span className="text-white/70 font-medium truncate">{row.name}</span>
                      <span className="text-right text-white/35 font-mono">{row.baseline}</span>
                      <span className="text-right text-white/60 font-mono">{row.variant}</span>
                      <span className={`text-right font-mono font-semibold ${row.delta.startsWith('+') ? 'text-primary' : 'text-white/40'}`}>{row.delta}</span>
                      <span className="text-right">
                        <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                          row.status === 'sig' ? 'bg-primary/15 text-primary' : 'bg-white/5 text-white/35'
                        }`}>
                          {row.status === 'sig' ? 'Significant' : 'Stable'}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Stats Bar ─── */}
      <section aria-label="Key statistics" className="relative py-16 border-y border-white/[0.04]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-4">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary/8 mb-3">
                  <Icon name={stat.icon} size={20} className="text-primary/70" />
                </div>
                <div className="text-3xl sm:text-4xl font-bold font-mono text-white tracking-tight mb-1">{stat.value}</div>
                <div className="text-sm text-white/35">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section aria-label="Features" className="relative py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-primary text-xs font-bold uppercase tracking-[0.2em] mb-3">Capabilities</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight gradient-text mb-4">
              Everything you need for rigorous experimentation
            </h2>
            <p className="text-white/40 text-base max-w-xl mx-auto">
              From data validation to final decision — one platform covers the entire A/B test lifecycle.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feature) => (
              <div key={feature.title} className="feature-card group">
                <div className={`inline-flex items-center justify-center w-11 h-11 rounded-xl border mb-5 ${accentColor[feature.accent]}`}>
                  <Icon name={feature.icon} size={22} />
                </div>
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-primary transition-colors">{feature.title}</h3>
                <p className="text-sm text-white/40 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How it Works ─── */}
      <section aria-label="How it works" className="relative py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-primary text-xs font-bold uppercase tracking-[0.2em] mb-3">Workflow</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight gradient-text">
              Three steps to a data-driven decision
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((step, i) => (
              <div key={step.num} className="relative text-center md:text-left">
                {/* Connector line (desktop only) */}
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[calc(100%+0.5rem)] w-[calc(100%-3rem)] border-t border-dashed border-white/10" />
                )}

                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/8 border border-primary/15 mb-5">
                  <span className="text-primary font-mono font-bold text-lg">{step.num}</span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-white/40 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section aria-label="Call to action" className="relative py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="relative overflow-hidden rounded-2xl border border-white/8 bg-gradient-to-b from-surface-1 to-surface-0 p-12 text-center">
            {/* Background glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-48 bg-primary/8 blur-[80px] rounded-full" />

            <div className="relative z-10">
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight gradient-text mb-4">
                Ready to make data-driven decisions?
              </h2>
              <p className="text-white/40 text-base mb-8 max-w-md mx-auto">
                Stop guessing. Let ExperimentOS handle the statistical rigor
                while you focus on building great products.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <button onClick={onGetStarted} className="btn-primary-lg focus-ring">
                  Get Started Free
                </button>
                <button onClick={onLoadDemo} className="btn-ghost-lg focus-ring">
                  View Demo
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-white/[0.04] py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
              <Icon name="science" className="text-primary" size={18} />
            </div>
            <span className="text-sm font-bold text-white/60">ExperimentOS</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-white/30">
            <span>Statistical Analysis</span>
            <span className="w-1 h-1 rounded-full bg-white/15" />
            <span>Guardrail Monitoring</span>
            <span className="w-1 h-1 rounded-full bg-white/15" />
            <span>Decision Automation</span>
          </div>
          <p className="text-xs text-white/20 font-mono">&copy; 2025 ExperimentOS</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
