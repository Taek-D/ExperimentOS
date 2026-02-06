
import React, { useState, useCallback } from 'react';

const IconWrapper = ({ name, className = "", size = 24 }: { name: string, className?: string, size?: number }) => (
    <span className={`material-symbols-rounded ${className}`} style={{ fontSize: size }}>
        {name}
    </span>
);


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
            className={`relative w-full h-64 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center transition-all duration-300 ${isDragging
                ? 'border-primary bg-primary/10'
                : 'border-border-dark/50 bg-secondary-dark/30 hover:border-primary/50'
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

            <div className="flex flex-col items-center gap-3 text-center pointer-events-none">
                <div className={`p-4 rounded-full transition-transform duration-300 ${isDragging ? 'scale-110 bg-primary/20' : 'bg-background-dark shadow-glow'}`}>
                    <IconWrapper name="upload_file" className={isDragging ? 'text-primary' : 'text-[#93c8b6]'} size={32} />
                </div>

                <div className="flex flex-col gap-1">
                    <p className="text-lg font-bold text-white">
                        {isUploading ? 'Uploading...' : 'Drop your CSV file here'}
                    </p>
                    <p className="text-sm text-gray-400">
                        or click to browse
                    </p>
                </div>

                <div className="mt-2 px-3 py-1 rounded-full bg-background-dark/50 border border-border-dark text-xs text-gray-500 font-mono">
                    Supported: .csv
                </div>
            </div>
        </div>
    );
};
