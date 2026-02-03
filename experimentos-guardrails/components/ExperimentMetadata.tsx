import React, { useState } from 'react';

interface ExperimentMetadataProps {
    onMetadataChange: (metadata: { name: string; split: string }) => void;
}

export const ExperimentMetadata: React.FC<ExperimentMetadataProps> = ({ onMetadataChange }) => {
    const [experimentName, setExperimentName] = useState('');
    const [trafficSplit, setTrafficSplit] = useState('50:50');

    const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setExperimentName(value);
        onMetadataChange({ name: value, split: trafficSplit });
    };

    const handleSplitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setTrafficSplit(value);
        onMetadataChange({ name: experimentName, split: value });
    };

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                    실험명
                </label>
                <input
                    type="text"
                    value={experimentName}
                    onChange={handleNameChange}
                    placeholder="예: 홈화면 배너 A/B 테스트"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                    기대 트래픽 분배 (control:treatment)
                </label>
                <input
                    type="text"
                    value={trafficSplit}
                    onChange={handleSplitChange}
                    placeholder="50:50"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                />
            </div>
        </div>
    );
};
