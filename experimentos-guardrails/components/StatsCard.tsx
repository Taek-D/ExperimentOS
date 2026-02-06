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
    <div className={`flex flex-col p-5 rounded-2xl relative overflow-hidden group transition-all duration-300 backdrop-blur-md ${isDanger
        ? 'bg-danger/10 border border-danger/30 shadow-glow-red hover:bg-danger/15'
        : 'bg-white/5 border border-white/5 hover:border-white/10 hover:bg-white/10'
      }`}>
      {/* Background Gradient Effect */}
      <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl transition-opacity duration-500 pointer-events-none ${isDanger ? 'bg-danger/20 opacity-40' : 'bg-primary/10 opacity-0 group-hover:opacity-100'
        }`}></div>

      <div className={`absolute top-0 right-0 p-5 transition-transform duration-300 ${isDanger ? 'opacity-20' : 'opacity-10 group-hover:opacity-30 group-hover:scale-110 group-hover:-rotate-12'
        }`}>
        <Icon name={icon} size={48} className={isDanger ? 'text-danger' : 'text-white'} />
      </div>

      <p className={`text-sm font-medium mb-2 uppercase tracking-wide z-10 ${isDanger ? 'text-danger' : 'text-white/60'}`}>
        {title}
      </p>

      <div className="flex items-end gap-3 z-10 mt-auto">
        <p className="text-white text-2xl sm:text-4xl font-mono font-bold tracking-tighter">
          {value}
        </p>
        {subValue && (
          <div className="mb-1.5">
            {subValue}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;