
import React, { useState, useCallback } from 'react';
import Icon from './Icon';

interface FileUploadProps {
    onFileSelect: (file: File) => void;
    isUploading: boolean;
}

export const FileUpload = ({ onFileSelect, isUploading }: FileUploadProps) => {
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const file = e.dataTransfer.files[0];
        if (file) {
            onFileSelect(file);
        }
    }, [onFileSelect]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            onFileSelect(file);
        }
    }, [onFileSelect]);

    return (
        <div
            data-tour="file-upload"
            className={`relative w-full rounded-xl border-2 border-dashed transition-all duration-200 ${
                isDragging
                    ? 'border-primary bg-primary/[0.06]'
                    : 'border-white/[0.08] bg-surface-1/30 hover:border-primary/30 hover:bg-surface-1/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <input
                type="file"
                accept=".csv"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                onChange={handleFileInput}
                disabled={isUploading}
            />

            <div className="flex flex-col items-center gap-3 py-12 px-6 text-center pointer-events-none">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200 ${
                    isDragging ? 'bg-primary/15 scale-110' : 'bg-white/[0.04]'
                }`}>
                    <Icon
                        name={isUploading ? "hourglass_empty" : "upload_file"}
                        className={isDragging ? 'text-primary' : 'text-white/30'}
                        size={24}
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <p className="text-sm font-medium text-white">
                        {isUploading ? 'Uploading...' : 'Drop your CSV file here'}
                    </p>
                    <p className="text-xs text-white/30">
                        or click to browse
                    </p>
                </div>

                <span className="text-[10px] font-mono text-white/20 bg-white/[0.03] px-2.5 py-1 rounded-full border border-white/[0.04]">
                    .csv
                </span>
            </div>
        </div>
    );
};
