import React from 'react';
import Icon from './Icon';

interface SidebarProps {
  onReset?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onReset }) => {
  return (
    <aside className="hidden lg:flex w-72 flex-col justify-between border-r border-white/[0.06] bg-surface-0/50 backdrop-blur-xl p-5 shrink-0 z-20 relative">
      <div className="flex flex-col gap-10">
        {/* Logo Area */}
        <div className="flex flex-col px-2 pt-2 cursor-pointer" onClick={onReset}>
          <div className="flex items-center gap-3 mb-1.5">
            <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/5 rounded-xl border border-primary/10">
              <Icon name="science" className="text-primary" size={24} />
            </div>
            <h1 className="text-white text-xl font-bold tracking-tight">ExperimentOS</h1>
          </div>
          <p className="text-white/40 text-[10px] font-mono uppercase tracking-widest pl-1">Engineering Platform v2.4</p>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-2">
          <div className="text-xs font-semibold text-white/30 uppercase tracking-wider px-4 mb-2">Menu</div>
          <NavItem icon="dashboard" label="Overview" onClick={onReset} />
          <NavItem icon="shield" label="Guardrails" isActive />
          <NavItem icon="flag" label="Feature Flags" />
          <NavItem icon="database" label="Data Sources" />
          <NavItem icon="history" label="Audit Logs" />
        </nav>
      </div>

      {/* Bottom Actions & User */}
      <div className="flex flex-col gap-4 px-2 pb-2">
        <div className="p-4 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            <span className="text-xs font-medium text-white/80">System Operational</span>
          </div>
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full w-3/4 bg-primary/50 rounded-full"></div>
          </div>
        </div>

        <div className="flex items-center gap-3 px-3 py-3 hover:bg-white/5 rounded-2xl cursor-pointer transition-all duration-300 group border border-transparent hover:border-white/5">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center shadow-lg shadow-primary/20">
            <span className="text-white text-sm font-bold">AC</span>
          </div>
          <div className="flex flex-col">
            <p className="text-white text-sm font-bold group-hover:text-primary transition-colors">Alex Chen</p>
            <p className="text-white/40 text-[11px]">Lead Data Scientist</p>
          </div>
          <Icon name="settings" className="ml-auto text-white/35 group-hover:text-white group-hover:rotate-45 transition-all duration-500" size={18} />
        </div>
      </div>
    </aside>
  );
};

interface NavItemProps {
  icon: string;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon, label, isActive, onClick }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden ${isActive
        ? 'bg-primary text-app-bg font-bold shadow-lg shadow-primary/20'
        : 'hover:bg-white/5 text-white/60 hover:text-white'
        }`}
    >
      {isActive && <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent opacity-50"></div>}
      <Icon
        name={icon}
        size={20}
        className={isActive ? 'text-app-bg' : 'text-white/40 group-hover:text-primary transition-colors'}
      />
      <span className="text-sm z-10">
        {label}
      </span>
      {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-app-bg"></div>}
    </button>
  );
};

export default Sidebar;