import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Search,
  FileText,
  BookOpen,
  Share2,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import api from '../services/api';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('ALL');

  const executeSearch = async (searchTerm) => {
    if (!searchTerm.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    try {
      const data = await api.searchAll(searchTerm.trim());
      if (data.success) {
        setResults(data);
      }
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      executeSearch(initialQuery);
    }
  }, [initialQuery]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearchParams({ q: query });
    executeSearch(query);
  };

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-200">
      {/* Search Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Global Knowledge Search</h1>
        <p className="text-slate-500 text-sm mt-1">
          Search across documents, technical terms, extracted definitions, source context, and relationship labels.
        </p>
      </div>

      {/* Main Search Input Form */}
      <form onSubmit={handleSubmit} className="relative">
        <Search size={19} className="absolute left-4 top-3.5 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search technical terms, definitions, relationships (e.g. 'Neural Network', 'IS_A', 'Architecture')..."
          className="w-full pl-12 pr-28 py-3.5 bg-white border border-slate-200 rounded-2xl text-sm text-slate-900 placeholder-slate-400 shadow-sm focus:outline-none focus:border-indigo-500 transition-colors"
        />
        <button
          type="submit"
          className="absolute right-2 top-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-colors shadow-sm shadow-indigo-600/20 cursor-pointer"
        >
          Search
        </button>
      </form>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center p-12 text-slate-500 text-xs">
          <RefreshCw className="w-5 h-5 animate-spin text-indigo-600 mr-2" />
          <span className="font-semibold">Searching knowledge repository...</span>
        </div>
      )}

      {/* Results Section */}
      {results && !loading && (
        <div className="space-y-6">
          {/* Tabs Filter */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3 text-xs">
            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-3.5 py-1.5 rounded-xl font-bold transition-colors cursor-pointer ${
                activeTab === 'ALL' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              All Matches ({results.total_matches})
            </button>
            <button
              onClick={() => setActiveTab('DOCUMENTS')}
              className={`px-3.5 py-1.5 rounded-xl font-bold transition-colors cursor-pointer ${
                activeTab === 'DOCUMENTS' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Documents ({results.results?.documents?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('TERMS')}
              className={`px-3.5 py-1.5 rounded-xl font-bold transition-colors cursor-pointer ${
                activeTab === 'TERMS' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Terminology ({results.results?.terms?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('RELATIONSHIPS')}
              className={`px-3.5 py-1.5 rounded-xl font-bold transition-colors cursor-pointer ${
                activeTab === 'RELATIONSHIPS' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Relationships ({results.results?.relationships?.length || 0})
            </button>
          </div>

          {results.total_matches === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs bg-white rounded-3xl border border-slate-200 shadow-sm">
              No entities matched your search query "{results.query}".
            </div>
          ) : (
            <div className="space-y-6">
              {/* Documents Matches */}
              {(activeTab === 'ALL' || activeTab === 'DOCUMENTS') && results.results?.documents?.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <FileText size={15} className="text-indigo-600" />
                    Matched Documents
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {results.results.documents.map((doc) => (
                      <Link
                        key={doc.id}
                        to={`/documents/${doc.id}`}
                        className="p-4 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-md transition-all flex items-center justify-between group shadow-sm"
                      >
                        <div className="truncate pr-3">
                          <span className="font-bold text-slate-900 text-xs block truncate group-hover:text-indigo-600 transition-colors">
                            {doc.original_filename}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {doc.total_concepts} concepts · {doc.total_relationships} relations
                          </span>
                        </div>
                        <ArrowRight size={15} className="text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all shrink-0" />
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Terminology Matches */}
              {(activeTab === 'ALL' || activeTab === 'TERMS') && results.results?.terms?.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <BookOpen size={15} className="text-emerald-600" />
                    Matched Terminology & Definitions
                  </h3>
                  <div className="space-y-2">
                    {results.results.terms.map((t) => (
                      <div key={t.id} className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-xs space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-black text-slate-900 text-sm">{t.term}</span>
                          <span className="text-[10px] text-emerald-700 font-mono font-bold px-2 py-0.5 rounded-lg bg-emerald-50 border border-emerald-200">
                            {Math.round(t.confidence_score * 100)}% conf
                          </span>
                        </div>
                        <p className="text-slate-700 leading-relaxed font-medium">{t.definition}</p>
                        {t.source_sentence && (
                          <p className="text-[11px] text-slate-500 italic bg-slate-50 p-2 rounded-xl">"{t.source_sentence}"</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Relationships Matches */}
              {(activeTab === 'ALL' || activeTab === 'RELATIONSHIPS') && results.results?.relationships?.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Share2 size={15} className="text-purple-600" />
                    Matched Relationships & Evidence
                  </h3>
                  <div className="space-y-2">
                    {results.results.relationships.map((r) => (
                      <div key={r.id} className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-xs space-y-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 font-bold text-slate-900">
                            <span>{r.source_name}</span>
                            <span className="px-2 py-0.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 uppercase text-[10px] font-extrabold tracking-wider">
                              {r.relation_type}
                            </span>
                            <span>{r.target_name}</span>
                          </div>
                          <span className="text-[11px] font-mono font-medium text-slate-400">Page {r.source_page}</span>
                        </div>
                        <blockquote className="text-slate-600 italic border-l-2 border-indigo-500 pl-3 font-medium">
                          "{r.supporting_sentence}"
                        </blockquote>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
