import React from 'react';
import Icon from './Icon';

interface StatsCardProps {
  title: string;
  value: string;
  subValue?: string | React.ReactNode;
  icon: string;
  variant?: 'default' | 'danger';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, subValue, icon, variant = 'default' }) => {
  const isDanger = variant === 'danger';

  return (
    <div className={`relative overflow-hidden rounded-xl p-5 transition-all duration-200 group ${
      isDanger
        ? 'bg-danger/[0.08] border border-danger/20 hover:border-danger/30'
        : 'bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.1] hover:bg-white/[0.05]'
    }`}>
      {/* Subtle gradient accent */}
      <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl pointer-events-none ${
        isDanger ? 'bg-danger/10' : 'bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500'
      }`} />

      <div className={`absolute top-4 right-4 transition-all duration-300 ${
        isDanger ? 'opacity-15' : 'opacity-[0.06] group-hover:opacity-[0.12] group-hover:scale-110'
      }`}>
        <Icon name={icon} size={40} className={isDanger ? 'text-danger' : 'text-white'} />
      </div>

      <p className={`text-[11px] font-semibold uppercase tracking-wider mb-3 z-10 relative ${
        isDanger ? 'text-danger/80' : 'text-white/40'
      }`}>
        {title}
      </p>

      <div className="flex items-end gap-3 z-10 relative">
        <p className="text-white text-2xl sm:text-3xl font-mono font-bold tracking-tight">
          {value}
        </p>
        {subValue && (
          <div className="mb-1">
            {subValue}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;
