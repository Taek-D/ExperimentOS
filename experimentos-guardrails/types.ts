export type Status = 'CRITICAL' | 'STABLE' | 'WARNING';

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