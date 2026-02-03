import React from 'react';

interface ContinuousMetric {
    metric_name: string;
    control_mean: number;
    treatment_mean: number;
    absolute_lift: number;
    relative_lift: number;
    p_value: number;
    is_significant: boolean;
}

interface ContinuousMetricsProps {
    metrics: ContinuousMetric[];
}

export const ContinuousMetrics: React.FC<ContinuousMetricsProps> = ({ metrics }) => {
    if (!metrics || metrics.length === 0) {
        return (
            <div className="text-center py-12 text-white/50">
                <p>연속형 지표가 없습니다</p>
                <p className="text-sm mt-2">CSV에 _sum, _sum_sq 컬럼이 있다면 자동으로 분석됩니다</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <p className="text-white/60 text-sm">
                Continuous Metrics Analysis (Welch's t-test)
            </p>

            {metrics.map((metric, idx) => (
                <div key={idx} className="p-6 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-xl">
                    <h4 className="text-lg font-semibold text-white mb-4">📊 {metric.metric_name}</h4>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <div className="text-white/50 text-xs mb-1">Control Mean</div>
                            <div className="text-white text-lg font-medium">{metric.control_mean.toFixed(2)}</div>
                        </div>

                        <div>
                            <div className="text-white/50 text-xs mb-1">Treatment Mean</div>
                            <div className="text-white text-lg font-medium">
                                {metric.treatment_mean.toFixed(2)}
                                <span className={`ml-2 text-sm ${metric.absolute_lift > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {metric.absolute_lift > 0 ? '+' : ''}{metric.absolute_lift.toFixed(2)}
                                </span>
                            </div>
                        </div>

                        <div>
                            <div className="text-white/50 text-xs mb-1">Relative Lift</div>
                            <div className={`text-lg font-medium ${metric.relative_lift > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {(metric.relative_lift * 100).toFixed(1)}%
                            </div>
                        </div>

                        <div>
                            <div className="text-white/50 text-xs mb-1">Significance</div>
                            <div className="flex items-center gap-2">
                                <span className={`text-lg ${metric.is_significant ? 'text-green-400' : 'text-white/50'}`}>
                                    {metric.is_significant ? '✅' : '❌'}
                                </span>
                                <span className="text-white/50 text-sm">p={metric.p_value.toFixed(3)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};
