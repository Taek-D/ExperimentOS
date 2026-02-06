import React, { useState, useRef, useEffect } from 'react';
import { DecisionMemoResponse, generateDecisionMemo, HealthCheckResult, AnalysisResult, BayesianInsights } from '../api/client';
import Icon from './Icon';

interface DecisionMemoProps {
    experimentName: string;
    health: HealthCheckResult | null;
    analysisResult: AnalysisResult | null;
    bayesianInsights: BayesianInsights | null;
}

export const DecisionMemo: React.FC<DecisionMemoProps> = ({ experimentName, health, analysisResult, bayesianInsights }) => {
    const [memo, setMemo] = useState<DecisionMemoResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const resultRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (memo && resultRef.current) {
            // Give a small delay to ensure DOM render
            setTimeout(() => {
                resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
        if (decision === 'Launch') return 'text-green-400 bg-green-400/10 border-green-400/30';
        if (decision === 'Rollback') return 'text-red-400 bg-red-400/10 border-red-400/30';
        return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
    };

    const getDecisionIcon = (decision: string) => {
        if (decision === 'Launch') return '🚀';
        if (decision === 'Rollback') return '🔙';
        return '⏸️';
    };

    return (
        <div className="max-w-5xl mx-auto p-6 space-y-6 pb-20">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold text-white font-display">Decision Memo</h2>
                    <p className="text-white/60 text-sm mt-1">Generate a comprehensive decision memo for your experiment</p>
                </div>

                <button
                    onClick={handleGenerate}
                    disabled={loading || !health || !analysisResult}
                    className="px-6 py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {loading ? (
                        <>
                            <span className="animate-spin">⚙️</span>
                            <span>Generating...</span>
                        </>
                    ) : (
                        <>
                            <span>📝</span>
                            <span>Generate Memo</span>
                        </>
                    )}
                </button>
            </div>

            {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                    {error}
                </div>
            )}

            {memo && (
                <div ref={resultRef} className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 scroll-mt-32">
                    {/* Decision Banner */}
                    <div className={`p-6 rounded-2xl border ${getDecisionColor(memo.decision.decision)}`}>
                        <div className="flex items-center gap-3 mb-3">
                            <span className="text-3xl">{getDecisionIcon(memo.decision.decision)}</span>
                            <div>
                                <h3 className="text-2xl font-bold">Decision: {memo.decision.decision}</h3>
                                <p className="text-sm opacity-80 mt-1">{memo.decision.reason}</p>
                            </div>
                        </div>
                        {memo.decision.details && memo.decision.details.length > 0 && (
                            <ul className="mt-4 space-y-1 text-sm">
                                {memo.decision.details.map((detail, idx) => (
                                    <li key={idx} className="flex items-start gap-2">
                                        <span>•</span>
                                        <span>{detail}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Download Buttons */}
                    <div className="flex gap-3">
                        <button
                            onClick={downloadMarkdown}
                            className="flex-1 px-6 py-4 bg-white/5 border border-white/10 rounded-xl text-white hover:bg-white/10 transition-colors flex items-center justify-center gap-3"
                        >
                            <Icon name="download" size={20} />
                            <span className="font-medium">Download Markdown</span>
                        </button>
                        <button
                            onClick={downloadHTML}
                            className="flex-1 px-6 py-4 bg-white/5 border border-white/10 rounded-xl text-white hover:bg-white/10 transition-colors flex items-center justify-center gap-3"
                        >
                            <Icon name="download" size={20} />
                            <span className="font-medium">Download HTML</span>
                        </button>
                    </div>

                    {/* Memo Preview */}
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                        <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
                            <h4 className="text-white font-semibold">Memo Preview</h4>
                            <span className="text-xs text-white/40">Scroll to see full content</span>
                        </div>
                        <div className="p-6 prose prose-invert prose-sm max-w-none max-h-[800px] overflow-y-auto custom-scrollbar">
                            <div dangerouslySetInnerHTML={{ __html: memo.memo_html }} />
                        </div>
                    </div>
                </div>
            )}

            {!memo && !loading && (
                <div className="text-center py-20 text-white/50">
                    <p className="text-lg mb-2">No memo generated yet</p>
                    <p className="text-sm">Click "Generate Memo" to create a decision memo for this experiment</p>
                </div>
            )}
        </div>
    );
};
