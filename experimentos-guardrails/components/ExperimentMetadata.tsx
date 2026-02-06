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
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-white/35 mb-2">
                    Experiment Name
                </label>
                <input
                    type="text"
                    value={experimentName}
                    onChange={handleNameChange}
                    placeholder="e.g. Homepage Banner A/B Test"
                    className="input-field"
                />
            </div>

            <div>
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-white/35 mb-2">
                    Expected Traffic Split (control:treatment)
                </label>
                <input
                    type="text"
                    value={trafficSplit}
                    onChange={handleSplitChange}
                    placeholder="50:50"
                    className="input-field"
                />
            </div>
        </div>
    );
};
