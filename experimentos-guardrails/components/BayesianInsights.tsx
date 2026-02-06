import React from 'react';
import type { BayesianInsights } from '../api/client';
import PosteriorDistribution from './charts/PosteriorDistribution';
import GlossaryTerm from './GlossaryTerm';

interface BayesianInsightsProps {
    insights: BayesianInsights | null;
}

export const BayesianInsightsComponent: React.FC<BayesianInsightsProps> = ({ insights }) => {
    if (!insights) {
        return (
            <div className="text-center py-12 text-white/50">
                <p>Bayesian 분석 결과가 없습니다</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-start gap-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                <span className="text-2xl">ℹ️</span>
                <div>
                    <div className="font-medium text-white">참고용 (Informational Only)</div>
                    <div className="text-sm text-white/60 mt-1">
                        베이지안 분석 결과는 의사결정 규칙(Launch/Hold/Rollback)에 영향을 주지 않습니다.
                    </div>
                </div>
            </div>

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
        </div>
    );
};
