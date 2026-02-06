import React, { useState } from 'react';
import Icon from './Icon';
import PowerCurve from './charts/PowerCurve';

interface PowerCalculatorProps {
    onApply?: (sampleSize: number) => void;
}

export const PowerCalculator: React.FC<PowerCalculatorProps> = ({ onApply }) => {
    const [metricType, setMetricType] = useState<'conversion' | 'continuous'>('conversion');
    const [baselineRate, setBaselineRate] = useState(10); // percentage
    const [stdDev, setStdDev] = useState(100);
    const [mdeRelative, setMdeRelative] = useState(10); // percentage
    const [mdeAbsolute, setMdeAbsolute] = useState(5);
    const [dailyTraffic, setDailyTraffic] = useState(1000);
    const [alpha, setAlpha] = useState(0.05);
    const [power, setPower] = useState(0.8);
    const [result, setResult] = useState<{
        sampleSizePerVariation: number;
        totalSampleSize: number;
        estimatedDays: number;
    } | null>(null);

    // Cohen's h calculation for proportions
    const proportionEffectSize = (p1: number, p2: number): number => {
        return 2 * (Math.asin(Math.sqrt(p2)) - Math.asin(Math.sqrt(p1)));
    };

    // Z-value for confidence level
    const getZValue = (alpha: number): number => {
        // Standard normal distribution critical values
        const zMap: Record<string, number> = {
            '0.10': 1.645,
            '0.05': 1.96,
            '0.01': 2.576,
        };
        return zMap[alpha.toString()] || 1.96;
    };

    // Sample size calculation for conversion rate (proportions)
    const calculateSampleSizeConversion = (): number => {
        const p1 = baselineRate / 100;
        let p2 = p1 * (1 + mdeRelative / 100);

        if (p2 > 1.0) p2 = 1.0;
        if (p2 < 0.0) p2 = 0.0;

        const h = Math.abs(proportionEffectSize(p1, p2));

        if (h === 0) return 0;

        // Simplified approximation using Normal distribution
        const z_alpha = getZValue(alpha / 2); // two-sided
        const z_beta = getZValue(1 - power);

        // Arcsin approximation formula
        const n = Math.pow((z_alpha + z_beta) / h, 2);

        return Math.ceil(n);
    };

    // Sample size calculation for continuous metrics (means)
    const calculateSampleSizeContinuous = (): number => {
        const d = Math.abs(mdeAbsolute) / stdDev; // Cohen's d

        if (d === 0) return 0;

        const z_alpha = getZValue(alpha / 2);
        const z_beta = getZValue(1 - power);

        // Simplified t-test formula (approximation)
        const n = 2 * Math.pow((z_alpha + z_beta) / d, 2);

        return Math.ceil(n);
    };

    const handleCalculate = () => {
        let sampleSize = 0;

        if (metricType === 'conversion') {
            sampleSize = calculateSampleSizeConversion();
        } else {
            sampleSize = calculateSampleSizeContinuous();
        }

        const totalSampleSize = sampleSize * 2;
        const estimatedDays = dailyTraffic > 0 ? Math.ceil(totalSampleSize / dailyTraffic) : 0;

        setResult({
            sampleSizePerVariation: sampleSize,
            totalSampleSize,
            estimatedDays,
        });

        if (onApply) {
            onApply(sampleSize);
        }
    };

    return (
        <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
            <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-white font-display">🔢 Sample Size Calculator</h2>
                <p className="text-white/60 text-sm mt-1">Calculate required sample size for your experiment</p>
            </div>

            {/* Metric Type Selection */}
            <div className="glass-card p-6">
                <label className="block text-white font-semibold mb-3">Metric Type</label>
                <div className="flex gap-3">
                    <button
                        onClick={() => setMetricType('conversion')}
                        className={`flex-1 px-4 py-3 rounded-xl font-medium transition-all ${metricType === 'conversion'
                                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                                : 'bg-white/5 text-white/70 hover:bg-white/10'
                            }`}
                    >
                        📊 Conversion Rate (Proportion)
                    </button>
                    <button
                        onClick={() => setMetricType('continuous')}
                        className={`flex-1 px-4 py-3 rounded-xl font-medium transition-all ${metricType === 'continuous'
                                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                                : 'bg-white/5 text-white/70 hover:bg-white/10'
                            }`}
                    >
                        📈 Continuous (Mean)
                    </button>
                </div>
            </div>

            {/* Input Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {metricType === 'conversion' ? (
                    <>
                        <div className="glass-card p-6">
                            <label className="block text-white font-semibold mb-2">Baseline Rate (%)</label>
                            <input
                                type="number"
                                value={baselineRate}
                                onChange={(e) => setBaselineRate(Number(e.target.value))}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                                step="0.1"
                            />
                        </div>
                        <div className="glass-card p-6">
                            <label className="block text-white font-semibold mb-2">MDE (Relative Lift %)</label>
                            <input
                                type="number"
                                value={mdeRelative}
                                onChange={(e) => setMdeRelative(Number(e.target.value))}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                                step="0.1"
                            />
                        </div>
                    </>
                ) : (
                    <>
                        <div className="glass-card p-6">
                            <label className="block text-white font-semibold mb-2">Standard Deviation</label>
                            <input
                                type="number"
                                value={stdDev}
                                onChange={(e) => setStdDev(Number(e.target.value))}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                                step="1"
                            />
                        </div>
                        <div className="glass-card p-6">
                            <label className="block text-white font-semibold mb-2">MDE (Absolute Effect)</label>
                            <input
                                type="number"
                                value={mdeAbsolute}
                                onChange={(e) => setMdeAbsolute(Number(e.target.value))}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                                step="0.1"
                            />
                        </div>
                    </>
                )}
            </div>

            <div className="glass-card p-6">
                <label className="block text-white font-semibold mb-2">Est. Daily Traffic (Total Users/Day)</label>
                <input
                    type="number"
                    value={dailyTraffic}
                    onChange={(e) => setDailyTraffic(Number(e.target.value))}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                    step="100"
                />
            </div>

            {/* Advanced Settings */}
            <details className="glass-card overflow-hidden">
                <summary className="p-4 cursor-pointer text-white font-semibold hover:bg-white/5 transition-colors">
                    Advanced Settings
                </summary>
                <div className="p-6 border-t border-white/10 grid grid-cols-2 gap-6">
                    <div>
                        <label className="block text-white font-semibold mb-2">Significance Level (α)</label>
                        <input
                            type="number"
                            value={alpha}
                            onChange={(e) => setAlpha(Number(e.target.value))}
                            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                            step="0.01"
                            min="0.01"
                            max="0.1"
                        />
                    </div>
                    <div>
                        <label className="block text-white font-semibold mb-2">Statistical Power (1-β)</label>
                        <input
                            type="number"
                            value={power}
                            onChange={(e) => setPower(Number(e.target.value))}
                            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
                            step="0.05"
                            min="0.7"
                            max="0.95"
                        />
                    </div>
                </div>
            </details>

            {/* Calculate Button */}
            <button
                onClick={handleCalculate}
                className="w-full px-6 py-4 bg-primary text-white rounded-xl font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
            >
                <Icon name="calculate" size={20} />
                <span>Calculate & Apply</span>
            </button>

            {/* Results */}
            {result && (
                <div className="space-y-6">
                    <div className="bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/30 rounded-2xl p-6 space-y-4">
                        <h3 className="text-xl font-bold text-white">Sample Size Calculation Result</h3>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                                <div className="text-white/60 text-sm mb-1">Control</div>
                                <div className="text-white text-2xl font-bold">{result.sampleSizePerVariation.toLocaleString()}</div>
                                <div className="text-white/60 text-xs mt-1">users</div>
                            </div>

                            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                                <div className="text-white/60 text-sm mb-1">Treatment</div>
                                <div className="text-white text-2xl font-bold">{result.sampleSizePerVariation.toLocaleString()}</div>
                                <div className="text-white/60 text-xs mt-1">users</div>
                            </div>

                            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                                <div className="text-white/60 text-sm mb-1">Total Required</div>
                                <div className="text-white text-2xl font-bold">{result.totalSampleSize.toLocaleString()}</div>
                                <div className="text-white/60 text-xs mt-1">users</div>
                            </div>
                        </div>

                        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                            <div className="text-white/60 text-sm mb-1">Estimated Duration</div>
                            <div className="text-white text-3xl font-bold">{result.estimatedDays} days</div>
                            <div className="text-white/60 text-xs mt-1">
                                Based on {dailyTraffic.toLocaleString()} daily users
                            </div>
                        </div>
                    </div>

                    {metricType === 'conversion' && (
                        <PowerCurve
                            baselineRate={baselineRate / 100}
                            mdeRelative={mdeRelative / 100}
                            alpha={alpha}
                            currentN={result.sampleSizePerVariation}
                        />
                    )}
                </div>
            )}
        </div>
    );
};
