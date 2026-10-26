import React from 'react';
import { Search, X, Filter } from 'lucide-react';

export const CATEGORIES = [
  { id: 'all', label: 'All Categories', color: '#94a3b8' },
  { id: 'Technology & Framework', label: 'Technology', color: '#3b82f6' },
  { id: 'Algorithm & Method', label: 'Algorithm', color: '#10b981' },
  { id: 'Architecture & Pattern', label: 'Architecture', color: '#8b5cf6' },
  { id: 'Data & Metric', label: 'Data & Metrics', color: '#f59e0b' },
  { id: 'Domain Concept', label: 'Domain Concept', color: '#06b6d4' },
];

export default function SearchFilterBar({ 
  searchQuery, 
  setSearchQuery, 
  selectedCategory, 
  setSelectedCategory,
  totalNodes,
  visibleNodes 
}) {
  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-slate-900/80 p-3 rounded-2xl border border-slate-800">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search concepts (e.g. TF-IDF, Knowledge Graph, Neo4j)..."
          className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-8 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none text-xs">
        <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0 mr-1" />
        {CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl font-medium shrink-0 transition-all ${
                isActive
                  ? 'bg-slate-800 text-white border border-slate-600 shadow-sm'
                  : 'bg-slate-950/60 text-slate-400 hover:text-slate-200 border border-slate-800/80'
              }`}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: cat.color }}
              />
              <span className="text-[11px]">{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* Counter */}
      <div className="text-[11px] text-slate-400 font-mono shrink-0 pl-1">
        Showing <b className="text-indigo-400">{visibleNodes}</b> of {totalNodes}
      </div>
    </div>
  );
}
