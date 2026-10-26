import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  BookOpen,
  Network,
  Search,
  Settings,
  Sparkles,
  LogOut,
  User,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Documents', path: '/documents', icon: FileText },
  { name: 'Terminology', path: '/terminology', icon: BookOpen },
  { name: 'Concept Mapper', path: '/mapper', icon: Network },
  { name: 'Search', path: '/search', icon: Search },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export default function Sidebar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('techmapper_token');
    localStorage.removeItem('techmapper_user');
    if (onLogout) onLogout();
    navigate('/login');
  };

  return (
    <aside className="w-64 bg-white border-r border-slate-200/90 flex flex-col justify-between shrink-0 select-none z-30 shadow-sm">
      <div className="p-5 space-y-6">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-lg shadow-indigo-600/30">
            <Network size={22} />
          </div>
          <div>
            <h1 className="text-sm font-black text-slate-900 tracking-tight leading-none">
              DocMapper
            </h1>
            <span className="text-[10px] text-indigo-600 font-bold tracking-wider uppercase">
              Concept Graph AI
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 shadow-sm border-l-4 border-indigo-600'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                <Icon size={17} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User Profile & Footer */}
      <div className="p-3 border-t border-slate-100 m-3 rounded-2xl bg-slate-50/80 space-y-3">
        {/* User Card */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 truncate pr-1">
            <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-xs shadow-sm shrink-0">
              {user?.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <div className="truncate">
              <span className="font-extrabold text-slate-900 text-xs block truncate leading-tight">
                {user?.name || 'Researcher'}
              </span>
              <span className="text-[10px] text-slate-500 truncate block">
                {user?.email || 'demo@docmapper.ai'}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Sign Out"
          >
            <LogOut size={15} />
          </button>
        </div>

        {/* System Status Pill */}
        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-200/60 font-medium">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Backend Active
          </span>
          <span className="font-mono text-[10px] text-slate-400">v2.0</span>
        </div>
      </div>
    </aside>
  );
}
