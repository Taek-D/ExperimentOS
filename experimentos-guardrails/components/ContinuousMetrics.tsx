import React from 'react';
import Icon from './Icon';

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
            <div className="empty-state">
                <Icon name="show_chart" size={48} className="empty-state-icon" />
                <p className="empty-state-title">No continuous metrics found</p>
                <p className="empty-state-description">Add _sum and _sum_sq columns to your CSV for automatic continuous metric analysis.</p>
            </div>
        );
    }

    return (
        <div className="space-y-5">
            <p className="text-white/35 text-xs font-mono uppercase tracking-wider">
                Welch's t-test
            </p>

            {metrics.map((metric, idx) => (
                <div key={idx} className="glass-card p-5">
                    <h4 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                        <Icon name="show_chart" size={18} className="text-white/30" />
                        {metric.metric_name}
                    </h4>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1">Control Mean</div>
                            <div className="text-white text-lg font-mono font-medium">{metric.control_mean.toFixed(2)}</div>
                        </div>

                        <div>
                            <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1">Treatment Mean</div>
                            <div className="text-white text-lg font-mono font-medium">
                                {metric.treatment_mean.toFixed(2)}
                                <span className={`ml-2 text-sm ${metric.absolute_lift > 0 ? 'text-primary' : 'text-danger'}`}>
                                    {metric.absolute_lift > 0 ? '+' : ''}{metric.absolute_lift.toFixed(2)}
                                </span>
                            </div>
                        </div>

                        <div>
                            <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1">Relative Lift</div>
                            <div className={`text-lg font-mono font-medium ${metric.relative_lift > 0 ? 'text-primary' : 'text-danger'}`}>
                                {(metric.relative_lift * 100).toFixed(1)}%
                            </div>
                        </div>

                        <div>
                            <div className="text-white/35 text-[11px] font-semibold uppercase tracking-wider mb-1">Significance</div>
                            <div className="flex items-center gap-2">
                                <span className={metric.is_significant ? 'status-badge-positive' : 'status-badge-neutral'}>
                                    {metric.is_significant ? 'Sig.' : 'Not Sig.'}
                                </span>
                                <span className="text-white/30 text-xs font-mono">p={metric.p_value.toFixed(3)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};
