import React from 'react';
import type { BayesianInsightsUnion } from '../api/client';
import { isMultiVariantBayesian } from '../api/client';
import PosteriorDistribution from './charts/PosteriorDistribution';
import GlossaryTerm from './GlossaryTerm';
import Icon from './Icon';
import { VARIANT_COLORS } from './charts/chartTheme';

interface BayesianInsightsProps {
    insights: BayesianInsightsUnion | null;
}

export const BayesianInsightsComponent: React.FC<BayesianInsightsProps> = ({ insights }) => {
    if (!insights) {
        return (
            <div className="empty-state">
                <Icon name="insights" size={48} className="empty-state-icon" />
                <p className="empty-state-title">No Bayesian analysis available</p>
                <p className="empty-state-description">Bayesian insights will appear here after analysis completes.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-start gap-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                <span className="text-2xl">ℹ️</span>
                <div>
                    <div className="font-medium text-white">Informational Only</div>
                    <div className="text-sm text-white/60 mt-1">
                        Bayesian analysis results do not affect the decision rules (Launch/Hold/Rollback).
                    </div>
                </div>
            </div>

            {isMultiVariantBayesian(insights) ? (
                <MultiVariantBayesianView insights={insights} />
            ) : (
                <TwoVariantBayesianView insights={insights} />
            )}
        </div>
    );
};

// 2-variant view (original)
const TwoVariantBayesianView: React.FC<{ insights: BayesianInsightsUnion }> = ({ insights }) => {
    if (isMultiVariantBayesian(insights)) return null;

    return (
        <>
            {insights.conversion && (
                <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-white">Primary Metric (Conversion)</h4>

                    <div className="space-y-3">
                        <div>
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-white/70"><GlossaryTerm termKey="bayesian-probability">Probability Treatment &gt; Control</GlossaryTerm></span>
                                <span className="text-white font-medium">
                                    {(insights.conversion.prob_treatment_beats_control * 100).toFixed(1)}%
                                </span>
                            </div>
                            <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-primary to-primary/70 transition-all duration-500"
                                    style={{ width: `${insights.conversion.prob_treatment_beats_control * 100}%` }}
                                />
                            </div>
                        </div>

                        <div className="flex justify-between text-sm">
                            <span className="text-white/70"><GlossaryTerm termKey="expected-loss">Expected Loss (Risk)</GlossaryTerm></span>
                            <span className="text-white font-mono">{insights.conversion.expected_loss.toFixed(6)}</span>
                        </div>
                    </div>

                    {insights.conversion.control_posterior && insights.conversion.treatment_posterior && (
                        <PosteriorDistribution
                            control={insights.conversion.control_posterior}
                            treatment={insights.conversion.treatment_posterior}
                        />
                    )}
                </div>
            )}

            {insights.continuous && Object.keys(insights.continuous).length > 0 && (
                <div className="space-y-4">
                    <h4 className="text-lg font-semibold text-white">Continuous Metrics</h4>

                    {Object.entries(insights.continuous).map(([metric, result]) => (
                        <div key={metric} className="space-y-2">
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-white/70">{metric}</span>
                                <span className="text-white font-medium">
                                    {(result.prob_treatment_beats_control * 100).toFixed(1)}%
                                </span>
                            </div>
                            <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
                                    style={{ width: `${result.prob_treatment_beats_control * 100}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
};

// Multi-variant view
import type { MultiVariantBayesianInsights } from '../api/client';

const MultiVariantBayesianView: React.FC<{ insights: MultiVariantBayesianInsights }> = ({ insights }) => {
    const conversion = insights.conversion;

    return (
        <div className="space-y-6">
            {conversion && (
                <>
                    {/* P(variant > control) per variant */}
                    <div className="space-y-4">
                        <h4 className="text-lg font-semibold text-white">P(Variant &gt; Control)</h4>
                        <div className="space-y-3">
                            {Object.entries(conversion.vs_control).map(([vName, data], i) => {
                                const color = VARIANT_COLORS[i % VARIANT_COLORS.length];
                                return (
                                    <div key={vName}>
                                        <div className="flex justify-between text-sm mb-2">
                                            <div className="flex items-center gap-2">
                                                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }}></span>
                                                <span className="text-white/70">{vName}</span>
                                            </div>
                                            <span className="text-white font-medium">
                                                {(data.prob_beats_control * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                                            <div
                                                className="h-full transition-all duration-500 rounded-full"
                                                style={{ width: `${data.prob_beats_control * 100}%`, backgroundColor: color }}
                                            />
                                        </div>
                                        <div className="flex justify-end text-xs text-white/40 mt-1 font-mono">
                                            Expected Loss: {data.expected_loss.toFixed(6)}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* P(being best) */}
                    <div className="space-y-4">
                        <h4 className="text-lg font-semibold text-white">P(Being Best)</h4>
                        <div className="glass-card p-4">
                            <div className="space-y-3">
                                {Object.entries(conversion.prob_being_best).map(([name, prob], i) => {
                                    const isControl = name === 'control';
                                    const color = isControl ? '#60a5fa' : (VARIANT_COLORS[(i - 1 + VARIANT_COLORS.length) % VARIANT_COLORS.length] ?? '#6366f1');
                                    return (
                                        <div key={name} className="flex items-center gap-3">
                                            <span className="w-24 text-sm text-white/70 truncate">{name}</span>
                                            <div className="flex-1 bg-white/10 rounded-full h-6 overflow-hidden relative">
                                                <div
                                                    className="h-full transition-all duration-500 rounded-full flex items-center justify-end pr-2"
                                                    style={{ width: `${Math.max(prob * 100, 2)}%`, backgroundColor: color }}
                                                >
                                                    <span className="text-[10px] font-mono text-white font-bold">
                                                        {(prob * 100).toFixed(1)}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};
