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
    <div className={`relative overflow-hidden rounded-xl p-5 transition-all duration-250 group ${
      isDanger
        ? 'bg-danger/[0.06] border border-danger/15 hover:border-danger/25 hover:bg-danger/[0.08]'
        : 'bg-white/[0.025] border border-white/[0.06] hover:border-primary/15 hover:bg-white/[0.04]'
    }`}
      style={{ transition: 'all 0.25s cubic-bezier(0.25, 0.1, 0.25, 1)' }}
    >
      {/* Gradient accent on hover */}
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none ${
        isDanger
          ? 'bg-gradient-to-br from-danger/[0.04] to-transparent'
          : 'bg-gradient-to-br from-primary/[0.03] to-transparent'
      }`} />

      {/* Background icon */}
      <div className={`absolute -top-1 -right-1 transition-all duration-300 ${
        isDanger ? 'opacity-10' : 'opacity-[0.04] group-hover:opacity-[0.08] group-hover:scale-110'
      }`}>
        <Icon name={icon} size={56} className={isDanger ? 'text-danger' : 'text-primary'} />
      </div>

      {/* Top border glow on hover */}
      <div className={`absolute top-0 left-0 right-0 h-px transition-opacity duration-300 opacity-0 group-hover:opacity-100 ${
        isDanger
          ? 'bg-gradient-to-r from-transparent via-danger/40 to-transparent'
          : 'bg-gradient-to-r from-transparent via-primary/30 to-transparent'
      }`} />

      <p className={`relative z-10 text-[11px] font-semibold uppercase tracking-wider mb-3 ${
        isDanger ? 'text-danger/70' : 'text-white/40'
      }`}>
        {title}
      </p>

      <div className="relative z-10 flex items-end gap-3">
        <p className="text-white text-2xl sm:text-3xl font-mono font-bold tracking-tight leading-none">
          {value}
        </p>
        {subValue && (
          <div className="mb-0.5">
            {subValue}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;
