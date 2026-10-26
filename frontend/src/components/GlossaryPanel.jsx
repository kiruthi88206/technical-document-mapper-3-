import React, { useState } from 'react';
import { Search, Download, ExternalLink, ArrowUpDown, Bookmark, FileSpreadsheet } from 'lucide-react';
import api from '../services/api';

export default function GlossaryPanel({ glossary, documentId, onSelectConcept }) {
  const [query, setQuery] = useState('');
  const [sortField, setSortField] = useState('importance_score');
  const [sortAsc, setSortAsc] = useState(false);

  if (!glossary || glossary.length === 0) {
    return (
      <div className="flex-1 bg-slate-950 rounded-2xl border border-slate-800 p-8 flex flex-col items-center justify-center text-center">
        <Bookmark className="w-10 h-10 text-slate-600 mb-3" />
        <h3 className="text-base font-bold text-slate-300">No Glossary Terms Yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Upload and analyze a technical document to automatically generate a domain-specific glossary.
        </p>
      </div>
    );
  }

  // Filter & Sort
  const filtered = glossary.filter((item) => {
    const q = query.toLowerCase();
    return (
      item.term.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      item.definition.toLowerCase().includes(q)
    );
  });

  const sorted = [...filtered].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    if (typeof valA === 'string') {
      return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return sortAsc ? (valA || 0) - (valB || 0) : (valB || 0) - (valA || 0);
  });

  const handleExportCsv = () => {
    if (!documentId) return;
    window.open(api.getExportUrl(documentId, 'csv'), '_blank');
  };

  return (
    <div className="flex-1 bg-slate-950 rounded-2xl border border-slate-800 p-6 flex flex-col overflow-hidden">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Extracted Terminology Glossary</span>
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-mono">
              {glossary.length} terms
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Key concepts ranked by statistical TF-IDF score and document frequency.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter glossary..."
              className="bg-slate-900 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44 sm:w-56"
            />
          </div>

          {/* Export CSV */}
          <button
            onClick={handleExportCsv}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all active:scale-95 shrink-0"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto mt-4 pr-1">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider select-none">
              <th
                onClick={() => {
                  setSortField('term');
                  setSortAsc(!sortAsc);
                }}
                className="pb-3 font-semibold cursor-pointer hover:text-white"
              >
                <div className="flex items-center space-x-1">
                  <span>Concept Term</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="pb-3 font-semibold">Category</th>
              <th
                onClick={() => {
                  setSortField('frequency');
                  setSortAsc(!sortAsc);
                }}
                className="pb-3 font-semibold text-center cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-center space-x-1">
                  <span>Occurrences</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => {
                  setSortField('tfidf_score');
                  setSortAsc(!sortAsc);
                }}
                className="pb-3 font-semibold text-center cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-center space-x-1">
                  <span>TF-IDF Score</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="pb-3 font-semibold">Contextual Excerpt</th>
              <th className="pb-3 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {sorted.map((item, idx) => (
              <tr key={item.id || idx} className="hover:bg-slate-900/40 transition-colors group">
                <td className="py-3 pr-3 font-bold text-slate-200 group-hover:text-indigo-300 transition-colors">
                  {item.term}
                </td>
                <td className="py-3 pr-3">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-900 border border-slate-800 text-slate-300">
                    {item.category}
                  </span>
                </td>
                <td className="py-3 pr-3 text-center font-mono text-slate-300">
                  {item.frequency || 1}
                </td>
                <td className="py-3 pr-3 text-center font-mono text-indigo-400 font-semibold">
                  {(item.tfidf_score || 0).toFixed(3)}
                </td>
                <td className="py-3 pr-3 text-slate-400 italic text-[11px] max-w-md truncate">
                  "{item.definition}"
                </td>
                <td className="py-3 text-right">
                  <button
                    onClick={() => onSelectConcept(item)}
                    title="View & Highlight in Knowledge Graph"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-indigo-600 transition-all inline-flex items-center space-x-1 text-[11px] font-medium"
                  >
                    <span>View in Graph</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
