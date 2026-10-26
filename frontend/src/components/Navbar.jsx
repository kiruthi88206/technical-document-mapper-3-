import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Upload, BookOpen, Network, HelpCircle, Sparkles } from 'lucide-react';

export default function Navbar({ user }) {
  const [quickSearch, setQuickSearch] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (quickSearch.trim()) {
      navigate(`/search?q=${encodeURIComponent(quickSearch.trim())}`);
      setQuickSearch('');
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between shrink-0 z-20 shadow-xs">
      {/* Quick Search */}
      <form onSubmit={handleSearchSubmit} className="relative w-72 md:w-96">
        <Search size={15} className="absolute left-3.5 top-2.5 text-slate-400" />
        <input
          type="text"
          value={quickSearch}
          onChange={(e) => setQuickSearch(e.target.value)}
          placeholder="Quick search concepts, terms & definitions..."
          className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:bg-white transition-all font-medium"
        />
      </form>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/documents')}
          className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition-colors flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
        >
          <Upload size={14} />
          <span>Upload</span>
        </button>

        <button
          onClick={() => navigate('/mapper')}
          className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-colors flex items-center gap-1.5 border border-slate-200"
        >
          <Network size={14} className="text-indigo-600" />
          <span>Graph</span>
        </button>

        {user && (
          <div className="hidden sm:flex items-center gap-2 pl-2 border-l border-slate-200">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-indigo-700 text-white font-bold text-xs flex items-center justify-center shadow-xs">
              {user.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <span className="text-xs font-bold text-slate-800 max-w-[120px] truncate">
              {user.name}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
