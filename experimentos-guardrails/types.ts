export type Status = 'CRITICAL' | 'STABLE' | 'WARNING';

// ===== Sequential Testing Types =====
export interface SequentialResult {
  can_stop: boolean;
  decision: 'reject_null' | 'continue' | 'fail_to_reject';
  z_stat: number;
  z_boundary: number;
  alpha_spent_this_look: number;
  cumulative_alpha_spent: number;
  info_fraction: number;
  current_look: number;
  max_looks: number;
  message: string;
}

export interface BoundaryPoint {
  look: number;
  info_fraction: number;
  z_boundary: number;
  p_boundary?: number;
  alpha_spent?: number;
  cumulative_alpha?: number;
}

export interface SequentialProgress {
  current_sample: number;
  target_sample: number;
  info_fraction: number;
  percentage: number;
}

export interface SequentialParams {
  controlUsers: number;
  controlConversions: number;
  treatmentUsers: number;
  treatmentConversions: number;
  targetSampleSize: number;
  currentLook: number;
  maxLooks: number;
  alpha: number;
  boundaryType: 'obrien_fleming' | 'pocock';
  previousLooks?: Array<{
    look: number;
    z_stat: number;
    info_fraction: number;
    cumulative_alpha_spent: number;
  }>;
}

export interface SequentialAnalysisResponse {
  status: string;
  sequential_result: SequentialResult;
  primary_result: {
    control_rate: number;
    treatment_rate: number;
    absolute_lift: number;
    relative_lift: number | null;
    z_stat: number;
    p_value: number;
    is_significant: boolean;
  };
  boundaries: BoundaryPoint[];
  progress: SequentialProgress;
}

export interface Metric {
  id: string;
  name: string;
  key: string;
  baseline: string;
  variant: string;
  delta: string;
  deltaValue: number; // Numeric value for logic
  pValue: number;
  power: number; // Percentage 0-100
  status: Status;
}

export interface NavItem {
  icon: string;
  label: string;
  isActive?: boolean;
}