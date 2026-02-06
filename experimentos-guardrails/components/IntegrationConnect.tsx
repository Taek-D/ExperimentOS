import React, { useState } from 'react';

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
        setApiKey(''); // Clear input
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
        <div data-tour="integration" className="w-full max-w-2xl mx-auto mb-8 p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    🔌 Connect Integration
                </h2>
                {isConnected && (
                    <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-medium border border-green-500/30">
                        Connected
                    </span>
                )}
            </div>

            {!isConnected ? (
                <div className="flex flex-col gap-4">
                    <p className="text-gray-400 text-sm">
                        Connect an external experiment provider to import results directly.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-gray-300">Provider</label>
                            <select
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                                className="bg-app-bg border border-white/10 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                            >
                                {PROVIDERS.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2 md:col-span-2">
                            <label className="text-sm font-medium text-gray-300">API Key / Console Key</label>
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    placeholder="Paste your secret key here..."
                                    className="flex-1 bg-app-bg border border-white/10 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                                />
                                <button
                                    onClick={handleConnect}
                                    disabled={!apiKey}
                                    className="bg-primary hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-6 py-2.5 rounded-lg transition-all shadow-lg shadow-primary/20 active:scale-95"
                                >
                                    Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="flex items-center justify-between bg-app-bg/50 p-4 rounded-xl border border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center text-2xl">
                            🚀
                        </div>
                        <div>
                            <p className="font-medium text-white">
                                Connected to <span className="text-primary">{getProviderName(savedProvider)}</span>
                            </p>
                            <p className="text-sm text-gray-500 flex items-center gap-2">
                                API Key: <span className="font-mono bg-white/5 px-2 py-0.5 rounded text-xs tracking-widest">●●●●●●●●●●●●</span>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleDisconnect}
                        className="text-gray-400 hover:text-danger hover:bg-danger/10 px-4 py-2 rounded-lg transition-all text-sm font-medium"
                    >
                        Disconnect
                    </button>
                </div>
            )}
        </div>
    );
};
