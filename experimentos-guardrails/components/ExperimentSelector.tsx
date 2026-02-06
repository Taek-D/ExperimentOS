import React, { useState, useEffect, useCallback } from 'react';
import { listExperiments, Experiment } from '../api/client';

interface ExperimentSelectorProps {
    onSelectExperiment: (experimentId: string, autoSync: boolean) => void;
    isLoading: boolean;
}

export const ExperimentSelector: React.FC<ExperimentSelectorProps> = ({ onSelectExperiment, isLoading }) => {
    const [experiments, setExperiments] = useState<Experiment[]>([]);
    const [selectedId, setSelectedId] = useState<string>('');
    const [loadingList, setLoadingList] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [autoSync, setAutoSync] = useState(false);

    const provider = localStorage.getItem('integration_provider');

    const loadExperiments = useCallback(async () => {
        if (!provider) return;
        setLoadingList(true);
        setError(null);
        try {
            const list = await listExperiments(provider);
            setExperiments(list);
            const first = list[0];
            if (first) {
                setSelectedId(first.id);
            }
        } catch (err: unknown) {
            console.error('Failed to load experiments', err);
            setError('Failed to load experiments. Please check your connection and API key.');
        } finally {
            setLoadingList(false);
        }
    }, [provider]);

    useEffect(() => {
        if (provider) {
            loadExperiments();
        }
    }, [provider, loadExperiments]);

    const handleAnalyze = () => {
        if (selectedId) {
            onSelectExperiment(selectedId, autoSync);
        }
    };

    if (!provider) return null;

    return (
        <div className="w-full max-w-2xl mx-auto glass-card p-5">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    Select Experiment
                </h2>
                <button
                    onClick={loadExperiments}
                    className="text-xs text-white/40 hover:text-white transition-colors"
                    disabled={loadingList}
                >
                    {loadingList ? 'Refreshing...' : 'Refresh List'}
                </button>
            </div>

            {error && (
                <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm">
                    {error}
                </div>
            )}

            <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                    <label className="section-label">Available Experiments ({provider})</label>
                    <select
                        value={selectedId}
                        onChange={(e) => setSelectedId(e.target.value)}
                        disabled={loadingList || experiments.length === 0}
                        className="input-field disabled:opacity-50"
                    >
                        {experiments.length === 0 && !loadingList ? (
                            <option value="">No experiments found</option>
                        ) : (
                            experiments.map(exp => (
                                <option key={exp.id} value={exp.id}>
                                    {exp.name} ({exp.status})
                                </option>
                            ))
                        )}
                    </select>
                </div>

                <div className="flex items-center justify-between pt-2">
                    <label className="flex items-center gap-2 cursor-pointer group">
                        <div className="relative">
                            <input
                                type="checkbox"
                                checked={autoSync}
                                onChange={(e) => setAutoSync(e.target.checked)}
                                className="peer sr-only"
                            />
                            <div className="w-10 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-white/10 after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                        </div>
                        <span className="text-sm text-white/40 group-hover:text-white transition-colors">
                            Auto-sync (Poll every 30s)
                        </span>
                    </label>

                    <button
                        onClick={handleAnalyze}
                        disabled={!selectedId || isLoading || experiments.length === 0}
                        className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <span>Analyze</span>
                                <span className="text-lg">→</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
