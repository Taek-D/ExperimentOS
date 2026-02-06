import React, { useState, useRef, useEffect } from 'react';
import { DecisionMemoResponse, generateDecisionMemo, HealthCheckResult, AnalysisResult } from '../api/client';
import type { BayesianInsightsUnion } from '../api/client';
import Icon from './Icon';

interface DecisionMemoProps {
    experimentName: string;
    health: HealthCheckResult | null;
    analysisResult: AnalysisResult | null;
    bayesianInsights: BayesianInsightsUnion | null;
}

export const DecisionMemo: React.FC<DecisionMemoProps> = ({ experimentName, health, analysisResult, bayesianInsights }) => {
    const [memo, setMemo] = useState<DecisionMemoResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const resultRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (memo && resultRef.current) {
            setTimeout(() => {
                const scrollParent = resultRef.current?.closest('.overflow-y-auto');
                if (scrollParent && resultRef.current) {
                    scrollParent.scrollTo({ top: resultRef.current.offsetTop - 20, behavior: 'smooth' });
                }
            }, 100);
        }
    }, [memo]);

    const handleGenerate = async () => {
        if (!health || !analysisResult) {
            setError('Missing required data. Please complete analysis first.');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await generateDecisionMemo({
                experiment_name: experimentName || 'Experiment',
                health_result: health.result,
                primary_result: analysisResult.primary_result,
                guardrail_results: analysisResult.guardrail_results,
                bayesian_insights: bayesianInsights || undefined,
            });

            setMemo(response);
        } catch (err: unknown) {
            const errObj = err as { response?: { data?: { detail?: string } } };
            setError(errObj.response?.data?.detail || 'Failed to generate memo');
        } finally {
            setLoading(false);
        }
    };

    const downloadMarkdown = () => {
        if (!memo) return;

        const blob = new Blob([memo.memo_markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${experimentName || 'experiment'}_decision_memo.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const downloadHTML = () => {
        if (!memo) return;

        const blob = new Blob([memo.memo_html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${experimentName || 'experiment'}_decision_memo.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const getDecisionColor = (decision: string) => {
        if (decision === 'Launch') return 'bg-primary/[0.08] border-primary/20 text-primary';
        if (decision === 'Rollback') return 'bg-danger/[0.08] border-danger/20 text-danger';
        return 'bg-warning/[0.08] border-warning/20 text-warning';
    };

    const getDecisionIcon = (decision: string) => {
        if (decision === 'Launch') return 'rocket_launch';
        if (decision === 'Rollback') return 'undo';
        return 'pause_circle';
    };

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6 pb-20">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Decision Memo</h2>
                    <p className="text-white/40 text-sm mt-1">Generate a comprehensive decision memo for your experiment</p>
                </div>

                <button
                    onClick={handleGenerate}
                    disabled={loading || !health || !analysisResult}
                    className="btn-primary flex items-center gap-2 shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <>
                            <span className="w-4 h-4 border-2 border-surface-0/30 border-t-surface-0 rounded-full animate-spin" />
                            <span>Generating...</span>
                        </>
                    ) : (
                        <>
                            <Icon name="description" size={18} />
                            <span>Generate Memo</span>
                        </>
                    )}
                </button>
            </div>

            {error && (
                <div className="p-4 bg-danger/[0.08] border border-danger/20 rounded-xl text-danger text-sm">
                    {error}
                </div>
            )}

            {memo && (
                <div ref={resultRef} className="space-y-5 scroll-mt-32">
                    {/* Decision Banner */}
                    <div className={`p-6 rounded-xl border ${getDecisionColor(memo.decision.decision)}`}>
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                                <Icon name={getDecisionIcon(memo.decision.decision)} size={22} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold">Decision: {memo.decision.decision}</h3>
                                <p className="text-sm opacity-70 mt-0.5">{memo.decision.reason}</p>
                            </div>
                        </div>
                        {memo.decision.details && memo.decision.details.length > 0 && (
                            <ul className="mt-4 space-y-1.5 text-sm">
                                {memo.decision.details.map((detail, idx) => (
                                    <li key={idx} className="flex items-start gap-2 opacity-80">
                                        <span className="text-[10px] mt-1.5">&#9679;</span>
                                        <span>{detail}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Download Buttons */}
                    <div className="flex flex-col sm:flex-row gap-3">
                        <button
                            onClick={downloadMarkdown}
                            className="flex-1 btn-ghost flex items-center justify-center gap-2.5 py-3.5"
                        >
                            <Icon name="download" size={18} className="text-white/40" />
                            <span>Download Markdown</span>
                        </button>
                        <button
                            onClick={downloadHTML}
                            className="flex-1 btn-ghost flex items-center justify-center gap-2.5 py-3.5"
                        >
                            <Icon name="download" size={18} className="text-white/40" />
                            <span>Download HTML</span>
                        </button>
                    </div>

                    {/* Memo Preview */}
                    <div className="glass-card overflow-hidden">
                        <div className="px-5 py-3.5 border-b border-white/[0.06] flex justify-between items-center">
                            <h4 className="text-sm font-semibold text-white">Memo Preview</h4>
                            <span className="text-[10px] text-white/25 font-mono">Scroll to see full content</span>
                        </div>
                        <div className="p-6 prose prose-invert prose-sm max-w-none max-h-[800px] overflow-y-auto custom-scrollbar">
                            <div dangerouslySetInnerHTML={{ __html: memo.memo_html }} />
                        </div>
                    </div>
                </div>
            )}

            {!memo && !loading && (
                <div className="empty-state py-24">
                    <Icon name="description" size={48} className="empty-state-icon" />
                    <p className="empty-state-title">No memo generated yet</p>
                    <p className="empty-state-description">Click "Generate Memo" to create a decision memo for this experiment</p>
                </div>
            )}
        </div>
    );
};
