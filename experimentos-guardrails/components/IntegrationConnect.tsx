import React, { useState } from 'react';
import Icon from './Icon';

const PROVIDERS = [
    { id: 'statsig', name: 'Statsig' },
    { id: 'growthbook', name: 'GrowthBook' },
    { id: 'hackle', name: 'Hackle' },
] as const;

export const IntegrationConnect: React.FC = () => {
    const [provider, setProvider] = useState<string>(PROVIDERS[0].id);
    const [apiKey, setApiKey] = useState('');
    const [isConnected, setIsConnected] = useState(() => {
        const storedKey = localStorage.getItem('integration_api_key');
        const storedProvider = localStorage.getItem('integration_provider');
        return !!(storedKey && storedProvider);
    });
    const [savedProvider, setSavedProvider] = useState(() => {
        const storedKey = localStorage.getItem('integration_api_key');
        const storedProvider = localStorage.getItem('integration_provider');
        return storedKey && storedProvider ? storedProvider : '';
    });

    const handleConnect = () => {
        if (!apiKey) return;
        localStorage.setItem('integration_api_key', apiKey);
        localStorage.setItem('integration_provider', provider);
        setIsConnected(true);
        setSavedProvider(provider);
        setApiKey('');
    };

    const handleDisconnect = () => {
        localStorage.removeItem('integration_api_key');
        localStorage.removeItem('integration_provider');
        setIsConnected(false);
        setSavedProvider('');
        setProvider(PROVIDERS[0].id as string);
    };

    const getProviderName = (id: string) => PROVIDERS.find(p => p.id === id)?.name || id;

    return (
        <div data-tour="integration" className="w-full glass-card p-5">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    <Icon name="power" size={16} className="text-white/40" />
                    Connect Integration
                </h2>
                {isConnected && (
                    <span className="status-badge-positive">
                        Connected
                    </span>
                )}
            </div>

            {!isConnected ? (
                <div className="flex flex-col gap-4">
                    <p className="text-white/35 text-xs">
                        Connect an external experiment provider to import results directly.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className="flex flex-col gap-1.5">
                            <label className="section-label">Provider</label>
                            <select
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                                className="input-field"
                            >
                                {PROVIDERS.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex flex-col gap-1.5 md:col-span-2">
                            <label className="section-label">API Key / Console Key</label>
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    placeholder="Paste your secret key here..."
                                    className="input-field flex-1"
                                />
                                <button
                                    onClick={handleConnect}
                                    disabled={!apiKey}
                                    className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                                >
                                    Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="flex items-center justify-between bg-surface-1/50 p-4 rounded-xl border border-white/[0.04]">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/15 flex items-center justify-center">
                            <Icon name="link" size={18} className="text-primary" />
                        </div>
                        <div>
                            <p className="font-medium text-sm text-white">
                                Connected to <span className="text-primary">{getProviderName(savedProvider)}</span>
                            </p>
                            <p className="text-xs text-white/25 flex items-center gap-1.5 mt-0.5">
                                API Key: <span className="font-mono bg-white/[0.04] px-1.5 py-0.5 rounded text-[10px] tracking-widest">&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;</span>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleDisconnect}
                        className="text-white/35 hover:text-danger hover:bg-danger/[0.06] px-3 py-1.5 rounded-lg transition-all text-xs font-medium"
                    >
                        Disconnect
                    </button>
                </div>
            )}
        </div>
    );
};
