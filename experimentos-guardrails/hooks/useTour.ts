import { useState, useCallback, useMemo } from 'react';

export interface TourStep {
  id: string;
  target: string | null; // CSS selector or null for center modal
  title: string;
  description: string;
  action?: 'load-demo'; // Special action to trigger on this step
}

const STORAGE_KEY = 'experimentos_tutorial_v1';

const TOUR_STEPS: TourStep[] = [
  // Phase A: Upload screen
  {
    id: 'welcome',
    target: null,
    title: 'Welcome to ExperimentOS',
    description:
      'ExperimentOS helps you make data-driven decisions for A/B tests. This quick tour will show you the key features. Let\'s get started!',
  },
  {
    id: 'experiment-name',
    target: '[data-tour="experiment-metadata"]',
    title: 'Name Your Experiment',
    description:
      'Start by naming your experiment and setting the expected traffic split (e.g., 50:50). This helps detect Sample Ratio Mismatch (SRM) issues.',
  },
  {
    id: 'integration',
    target: '[data-tour="integration"]',
    title: 'Connect an Integration',
    description:
      'Optionally connect Statsig or GrowthBook to import experiment results directly from your platform.',
  },
  {
    id: 'file-upload',
    target: '[data-tour="file-upload"]',
    title: 'Upload Your Data',
    description:
      'Upload a CSV with columns: variant, users, conversions. You can also include guardrail columns like error_count or revenue.',
  },
  {
    id: 'load-demo',
    target: '[data-tour="try-demo"]',
    title: 'Try it Now!',
    description:
      'Click "Load Demo" below to see ExperimentOS in action with sample data. We\'ll load a pre-computed experiment for you.',
    action: 'load-demo',
  },
  // Phase B: Results screen (after demo load)
  {
    id: 'nav-tabs',
    target: '[data-tour="nav-tabs"]',
    title: 'Navigate Between Views',
    description:
      'Switch between Analysis (results & charts), Decision Memo (automated recommendation), and Power Calculator (plan future experiments).',
  },
  {
    id: 'stats-cards',
    target: '[data-tour="stats-cards"]',
    title: 'Key Metrics at a Glance',
    description:
      'See the primary lift, p-value, and guardrail status at a glance. Green means significant positive lift. Red indicates guardrail violations.',
  },
  {
    id: 'dashboard-tabs',
    target: '[data-tour="dashboard-tabs"]',
    title: 'Explore Different Analyses',
    description:
      'Dive deeper with Primary metrics, Guardrails, Continuous metrics, and Bayesian analysis tabs.',
  },
  {
    id: 'metrics-table',
    target: '[data-tour="metrics-table"]',
    title: 'Detailed Metrics Table',
    description:
      'View baseline vs. variant rates, delta, p-values, and status for every metric. Hover over column headers for explanations.',
  },
  {
    id: 'forest-plot',
    target: '[data-tour="forest-plot"]',
    title: 'Forest Plot',
    description:
      'Visualize confidence intervals. When the CI bar does not cross the zero line, the result is statistically significant.',
  },
  {
    id: 'completion',
    target: null,
    title: "You're Ready!",
    description:
      'You now know the basics of ExperimentOS. Check out the Decision Memo tab for an automated launch recommendation, or upload your own data to get started!',
  },
];

interface UseTourReturn {
  isActive: boolean;
  currentIndex: number;
  currentStep: TourStep | null;
  totalSteps: number;
  hasSeenTour: boolean;
  startTour: () => void;
  nextStep: () => void;
  prevStep: () => void;
  skipTour: () => void;
  resetTour: () => void;
}

export function useTour(): UseTourReturn {
  const [isActive, setIsActive] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [hasSeenTour, setHasSeenTour] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'done';
    } catch {
      return false;
    }
  });

  const currentStep = useMemo((): TourStep | null => {
    if (!isActive) return null;
    const step = TOUR_STEPS[currentIndex];
    return step ?? null;
  }, [isActive, currentIndex]);

  const totalSteps = TOUR_STEPS.length;

  const markDone = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, 'done');
    } catch {
      // localStorage unavailable
    }
    setHasSeenTour(true);
  }, []);

  const startTour = useCallback(() => {
    setCurrentIndex(0);
    setIsActive(true);
  }, []);

  const nextStep = useCallback(() => {
    setCurrentIndex((prev) => {
      const next = prev + 1;
      if (next >= totalSteps) {
        setIsActive(false);
        markDone();
        return 0;
      }
      return next;
    });
  }, [totalSteps, markDone]);

  const prevStep = useCallback(() => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
  }, []);

  const skipTour = useCallback(() => {
    setIsActive(false);
    markDone();
  }, [markDone]);

  const resetTour = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // localStorage unavailable
    }
    setHasSeenTour(false);
    setCurrentIndex(0);
  }, []);

  return {
    isActive,
    currentIndex,
    currentStep,
    totalSteps,
    hasSeenTour,
    startTour,
    nextStep,
    prevStep,
    skipTour,
    resetTour,
  };
}
