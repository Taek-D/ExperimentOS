import React, { useState } from 'react';
import Icon from './Icon';
import PowerCurve from './charts/PowerCurve';

interface PowerCalculatorProps {
    onApply?: (sampleSize: number) => void;
}

export const PowerCalculator: React.FC<PowerCalculatorProps> = ({ onApply }) => {
    const [metricType, setMetricType] = useState<'conversion' | 'continuous'>('conversion');
    const [baselineRate, setBaselineRate] = useState(10);
    const [stdDev, setStdDev] = useState(100);
    const [mdeRelative, setMdeRelative] = useState(10);
    const [mdeAbsolute, setMdeAbsolute] = useState(5);
    const [dailyTraffic, setDailyTraffic] = useState(1000);
    const [alpha, setAlpha] = useState(0.05);
    const [power, setPower] = useState(0.8);
    const [result, setResult] = useState<{
        sampleSizePerVariation: number;
        totalSampleSize: number;
        estimatedDays: number;
    } | null>(null);

    const proportionEffectSize = (p1: number, p2: number): number => {
        return 2 * (Math.asin(Math.sqrt(p2)) - Math.asin(Math.sqrt(p1)));
    };

    const getZValue = (alpha: number): number => {
        const zMap: Record<string, number> = {
            '0.10': 1.645,
            '0.05': 1.96,
            '0.01': 2.576,
        };
        return zMap[alpha.toString()] || 1.96;
    };

    const calculateSampleSizeConversion = (): number => {
        const p1 = baselineRate / 100;
        let p2 = p1 * (1 + mdeRelative / 100);
        if (p2 > 1.0) p2 = 1.0;
        if (p2 < 0.0) p2 = 0.0;
        const h = Math.abs(proportionEffectSize(p1, p2));
        if (h === 0) return 0;
        const z_alpha = getZValue(alpha / 2);
        const z_beta = getZValue(1 - power);
        const n = Math.pow((z_alpha + z_beta) / h, 2);
        return Math.ceil(n);
    };

    const calculateSampleSizeContinuous = (): number => {
        const d = Math.abs(mdeAbsolute) / stdDev;
        if (d === 0) return 0;
        const z_alpha = getZValue(alpha / 2);
        const z_beta = getZValue(1 - power);
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
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6">
            <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Sample Size Calculator</h2>
                <p className="text-white/40 text-sm mt-1">Calculate required sample size for your experiment</p>
            </div>

            {/* Metric Type Selection */}
            <div className="glass-card p-5">
                <label className="section-label mb-3 block">Metric Type</label>
                <div className="flex gap-2">
                    <button
                        onClick={() => setMetricType('conversion')}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all ${
                            metricType === 'conversion'
                                ? 'bg-primary/15 text-primary border border-primary/20'
                                : 'bg-white/[0.03] text-white/50 hover:bg-white/[0.06] border border-white/[0.06]'
                        }`}
                    >
                        <Icon name="analytics" size={16} />
                        Conversion Rate
                    </button>
                    <button
                        onClick={() => setMetricType('continuous')}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all ${
                            metricType === 'continuous'
                                ? 'bg-primary/15 text-primary border border-primary/20'
                                : 'bg-white/[0.03] text-white/50 hover:bg-white/[0.06] border border-white/[0.06]'
                        }`}
                    >
                        <Icon name="show_chart" size={16} />
                        Continuous (Mean)
                    </button>
                </div>
            </div>

            {/* Input Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {metricType === 'conversion' ? (
                    <>
                        <div className="glass-card p-5">
                            <label className="section-label mb-2 block">Baseline Rate (%)</label>
                            <input
                                type="number"
                                value={baselineRate}
                                onChange={(e) => setBaselineRate(Number(e.target.value))}
                                className="input-field"
                                step="0.1"
                            />
                        </div>
                        <div className="glass-card p-5">
                            <label className="section-label mb-2 block">MDE (Relative Lift %)</label>
                            <input
                                type="number"
                                value={mdeRelative}
                                onChange={(e) => setMdeRelative(Number(e.target.value))}
                                className="input-field"
                                step="0.1"
                            />
                        </div>
                    </>
                ) : (
                    <>
                        <div className="glass-card p-5">
                            <label className="section-label mb-2 block">Standard Deviation</label>
                            <input
                                type="number"
                                value={stdDev}
                                onChange={(e) => setStdDev(Number(e.target.value))}
                                className="input-field"
                                step="1"
                            />
                        </div>
                        <div className="glass-card p-5">
                            <label className="section-label mb-2 block">MDE (Absolute Effect)</label>
                            <input
                                type="number"
                                value={mdeAbsolute}
                                onChange={(e) => setMdeAbsolute(Number(e.target.value))}
                                className="input-field"
                                step="0.1"
                            />
                        </div>
                    </>
                )}
            </div>

            <div className="glass-card p-5">
                <label className="section-label mb-2 block">Est. Daily Traffic (Total Users/Day)</label>
                <input
                    type="number"
                    value={dailyTraffic}
                    onChange={(e) => setDailyTraffic(Number(e.target.value))}
                    className="input-field"
                    step="100"
                />
            </div>

            {/* Advanced Settings */}
            <details className="glass-card overflow-hidden group">
                <summary className="p-4 cursor-pointer text-sm font-medium text-white/70 hover:text-white hover:bg-white/[0.02] transition-all flex items-center gap-2">
                    <Icon name="tune" size={16} className="text-white/35" />
                    Advanced Settings
                </summary>
                <div className="p-5 pt-0 border-t border-white/[0.06] mt-1 grid grid-cols-2 gap-4">
                    <div>
                        <label className="section-label mb-2 block">Significance Level (alpha)</label>
                        <input
                            type="number"
                            value={alpha}
                            onChange={(e) => setAlpha(Number(e.target.value))}
                            className="input-field"
                            step="0.01"
                            min="0.01"
                            max="0.1"
                        />
                    </div>
                    <div>
                        <label className="section-label mb-2 block">Statistical Power (1-beta)</label>
                        <input
                            type="number"
                            value={power}
                            onChange={(e) => setPower(Number(e.target.value))}
                            className="input-field"
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
                className="w-full btn-primary py-3.5 flex items-center justify-center gap-2 text-base"
            >
                <Icon name="calculate" size={20} />
                <span>Calculate</span>
            </button>

            {/* Results */}
            {result && (
                <div className="space-y-5">
                    <div className="glass-card p-6 space-y-5">
                        <h3 className="text-lg font-bold text-white">Result</h3>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.04]">
                                <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1.5">Control</div>
                                <div className="text-white text-2xl font-bold font-mono">{result.sampleSizePerVariation.toLocaleString()}</div>
                                <div className="text-white/25 text-xs mt-1 font-mono">users</div>
                            </div>

                            <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.04]">
                                <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1.5">Treatment</div>
                                <div className="text-white text-2xl font-bold font-mono">{result.sampleSizePerVariation.toLocaleString()}</div>
                                <div className="text-white/25 text-xs mt-1 font-mono">users</div>
                            </div>

                            <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.04]">
                                <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1.5">Total Required</div>
                                <div className="text-white text-2xl font-bold font-mono">{result.totalSampleSize.toLocaleString()}</div>
                                <div className="text-white/25 text-xs mt-1 font-mono">users</div>
                            </div>
                        </div>

                        <div className="bg-primary/[0.06] rounded-xl p-5 border border-primary/15">
                            <div className="text-primary/70 text-[11px] font-semibold uppercase tracking-wider mb-1.5">Estimated Duration</div>
                            <div className="text-white text-3xl font-bold font-mono">{result.estimatedDays} <span className="text-lg text-white/50">days</span></div>
                            <div className="text-white/30 text-xs mt-1 font-mono">
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
