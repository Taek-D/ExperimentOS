/**
 * Chart utility functions:
 * - Beta PDF computation (Lanczos gamma approximation)
 * - Power calculation helpers
 */

// ---------- Lanczos Gamma Approximation ----------

const LANCZOS_G = 7;
const LANCZOS_C = [
  0.99999999999980993,
  676.5203681218851,
  -1259.1392167224028,
  771.32342877765313,
  -176.61502916214059,
  12.507343278686905,
  -0.13857109526572012,
  9.9843695780195716e-6,
  1.5056327351493116e-7,
];

function gammaLn(z: number): number {
  if (z < 0.5) {
    // Reflection formula
    return Math.log(Math.PI / Math.sin(Math.PI * z)) - gammaLn(1 - z);
  }
  z -= 1;
  let x = LANCZOS_C[0]!;
  for (let i = 1; i < LANCZOS_G + 2; i++) {
    x += LANCZOS_C[i]! / (z + i);
  }
  const t = z + LANCZOS_G + 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

function betaLn(a: number, b: number): number {
  return gammaLn(a) + gammaLn(b) - gammaLn(a + b);
}

/** Compute Beta distribution PDF at point x given parameters alpha, beta */
export function betaPdf(x: number, alpha: number, beta: number): number {
  if (x <= 0 || x >= 1) return 0;
  const logPdf = (alpha - 1) * Math.log(x) + (beta - 1) * Math.log(1 - x) - betaLn(alpha, beta);
  return Math.exp(logPdf);
}

/**
 * Generate an array of {x, y} points for a Beta PDF curve.
 * Clamps the range to avoid near-zero tails.
 */
export function generateBetaCurve(
  alpha: number,
  beta: number,
  points: number = 200
): { x: number; y: number }[] {
  // Determine meaningful range (avoid extreme tails)
  const mean = alpha / (alpha + beta);
  const variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1));
  const sd = Math.sqrt(variance);
  const lo = Math.max(0.0001, mean - 5 * sd);
  const hi = Math.min(0.9999, mean + 5 * sd);
  const step = (hi - lo) / (points - 1);

  const result: { x: number; y: number }[] = [];
  for (let i = 0; i < points; i++) {
    const x = lo + i * step;
    result.push({ x, y: betaPdf(x, alpha, beta) });
  }
  return result;
}

// ---------- Power Calculation Helpers ----------

/** Standard normal CDF (Abramowitz & Stegun approximation) */
function normalCdf(z: number): number {
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;

  const sign = z < 0 ? -1 : 1;
  const x = Math.abs(z) / Math.sqrt(2);
  const t = 1.0 / (1.0 + p * x);
  const y = 1.0 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return 0.5 * (1.0 + sign * y);
}

/** Inverse normal CDF (rational approximation, good for 0.0001 < p < 0.9999) */
function normalQuantile(p: number): number {
  if (p <= 0) return -Infinity;
  if (p >= 1) return Infinity;
  if (p === 0.5) return 0;

  const a = [
    -3.969683028665376e1,
    2.209460984245205e2,
    -2.759285104469687e2,
    1.383577518672690e2,
    -3.066479806614716e1,
    2.506628277459239e0,
  ];
  const b = [
    -5.447609879822406e1,
    1.615858368580409e2,
    -1.556989798598866e2,
    6.680131188771972e1,
    -1.328068155288572e1,
  ];
  const c = [
    -7.784894002430293e-3,
    -3.223964580411365e-1,
    -2.400758277161838e0,
    -2.549732539343734e0,
    4.374664141464968e0,
    2.938163982698783e0,
  ];
  const d = [
    7.784695709041462e-3,
    3.224671290700398e-1,
    2.445134137142996e0,
    3.754408661907416e0,
  ];

  const pLow = 0.02425;
  const pHigh = 1 - pLow;

  let q: number;
  let r: number;

  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0]! * q + c[1]!) * q + c[2]!) * q + c[3]!) * q + c[4]!) * q + c[5]!) /
      ((((d[0]! * q + d[1]!) * q + d[2]!) * q + d[3]!) * q + 1);
  } else if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (((((a[0]! * r + a[1]!) * r + a[2]!) * r + a[3]!) * r + a[4]!) * r + a[5]!) * q /
      (((((b[0]! * r + b[1]!) * r + b[2]!) * r + b[3]!) * r + b[4]!) * r + 1);
  } else {
    q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0]! * q + c[1]!) * q + c[2]!) * q + c[3]!) * q + c[4]!) * q + c[5]!) /
      ((((d[0]! * q + d[1]!) * q + d[2]!) * q + d[3]!) * q + 1);
  }
}

/** Cohen's h effect size for two proportions */
function cohenH(p1: number, p2: number): number {
  return 2 * (Math.asin(Math.sqrt(p2)) - Math.asin(Math.sqrt(p1)));
}

/**
 * Calculate statistical power for a given sample size (conversion metric).
 * Uses arcsin approximation (two-sided test).
 */
export function powerForSampleSize(
  n: number,
  baselineRate: number,
  mdeRelative: number,
  alpha: number = 0.05
): number {
  const p1 = baselineRate;
  let p2 = p1 * (1 + mdeRelative);
  p2 = Math.max(0, Math.min(1, p2));

  const h = Math.abs(cohenH(p1, p2));
  if (h === 0 || n <= 0) return 0;

  const zAlpha = normalQuantile(1 - alpha / 2);
  const ncp = h * Math.sqrt(n); // non-centrality parameter
  return 1 - normalCdf(zAlpha - ncp);
}

/**
 * Generate power curve data points.
 * Returns array of {n, power} for sample sizes from minN to maxN.
 */
export function generatePowerCurve(
  baselineRate: number,
  mdeRelative: number,
  alpha: number = 0.05,
  currentN?: number,
  points: number = 60
): { n: number; power: number }[] {
  // Default range: 50 to 5x required sample size (or centered on currentN)
  const centerN = currentN ?? 1000;
  const minN = Math.max(10, Math.round(centerN * 0.1));
  const maxN = Math.round(centerN * 3);
  const step = Math.max(1, Math.round((maxN - minN) / (points - 1)));

  const result: { n: number; power: number }[] = [];
  for (let i = 0; i < points; i++) {
    const n = minN + i * step;
    result.push({ n, power: powerForSampleSize(n, baselineRate, mdeRelative, alpha) });
  }
  return result;
}
