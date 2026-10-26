import React, { useState, useEffect } from 'react';
import {
  Search,
  BookOpen,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  X,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import api from '../services/api';

export default function TerminologyPage() {
  const [terminology, setTerminology] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [search, setSearch] = useState('');
  const [minConfidence, setMinConfidence] = useState(0);
  const [defType, setDefType] = useState('');
  const [sortBy, setSortBy] = useState('frequency');
  const [order, setOrder] = useState('desc');
  const [loading, setLoading] = useState(true);

  // Term detail modal state
  const [selectedTerm, setSelectedTerm] = useState(null);
  const [termDetailLoading, setTermDetailLoading] = useState(false);

  const fetchTerms = async () => {
    try {
      setLoading(true);
      const data = await api.getTerminology({
        search,
        minConfidence: minConfidence > 0 ? minConfidence : undefined,
        definitionType: defType || undefined,
        sortBy,
        order,
        page,
        limit,
      });
      if (data.success) {
        setTerminology(data.terminology || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to load terminology:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTerms();
  }, [page, sortBy, order, defType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTerms();
  };

  const handleOpenTermModal = async (termId) => {
    setTermDetailLoading(true);
    try {
      const data = await api.getTermDetail(termId);
      if (data.success) {
        setSelectedTerm(data.term);
      }
    } catch (err) {
      console.error('Failed to fetch term detail:', err);
    } finally {
      setTermDetailLoading(false);
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Terminology Explorer</h1>
          <p className="text-slate-500 text-sm mt-1">
            Browse, search, and inspect technical terms, contextual definitions, and semantic confidence scores.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-3xl bg-white border border-slate-200/80 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[240px]">
            <Search size={15} className="absolute left-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search terms, definitions, source contexts..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
            />
          </div>

          {/* Definition Type Filter */}
          <select
            value={defType}
            onChange={(e) => {
              setDefType(e.target.value);
              setPage(1);
            }}
            className="px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
          >
            <option value="">All Definition Types</option>
            <option value="explicit_document">Explicit in Document</option>
            <option value="contextual_inference">Contextual Inference</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            className="px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
          >
            <option value="frequency">Sort by Frequency</option>
            <option value="confidence_score">Sort by Confidence</option>
            <option value="term">Sort Alphabetically</option>
          </select>

          {/* Order Toggle */}
          <button
            type="button"
            onClick={() => setOrder(order === 'desc' ? 'asc' : 'desc')}
            className="px-3 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-bold transition-colors flex items-center gap-1.5 cursor-pointer"
            title="Toggle Sort Order"
          >
            <ArrowUpDown size={13} />
            <span className="uppercase">{order}</span>
          </button>

          <button
            type="submit"
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-colors shadow-sm shadow-indigo-600/20 cursor-pointer"
          >
            Search
          </button>
        </form>
      </div>

      {/* Terminology Table */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500 font-semibold">
            Showing <span className="text-slate-900 font-bold">{terminology.length}</span> of <span className="text-slate-900 font-bold">{total}</span> terminology entries
          </span>
        </div>

        {loading ? (
          <div className="p-16 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-2">
            <RefreshCw size={20} className="animate-spin text-indigo-600" />
            <span>Loading terminology directory...</span>
          </div>
        ) : terminology.length === 0 ? (
          <div className="p-16 text-center text-slate-500 text-xs">
            No terminology entries matched your search criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                  <th className="pb-3.5">Technical Term</th>
                  <th className="pb-3.5">Type</th>
                  <th className="pb-3.5">Freq</th>
                  <th className="pb-3.5">Confidence</th>
                  <th className="pb-3.5">Definition Preview</th>
                  <th className="pb-3.5">Location</th>
                  <th className="pb-3.5 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {terminology.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => handleOpenTermModal(t.id)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 font-bold text-slate-900">{t.term}</td>
                    <td className="py-3.5">
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-lg border ${
                        t.definition_type === 'explicit_document'
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : 'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {t.definition_type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 font-mono font-semibold text-slate-800">{t.frequency}x</td>
                    <td className="py-3.5 font-mono text-emerald-600 font-bold">
                      {Math.round(t.confidence_score * 100)}%
                    </td>
                    <td className="py-3.5 max-w-sm truncate text-slate-500 font-medium">
                      {t.definition}
                    </td>
                    <td className="py-3.5 text-slate-500 font-medium">
                      Page {t.page_number} {t.section_heading ? `· ${t.section_heading}` : ''}
                    </td>
                    <td className="py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenTermModal(t.id);
                        }}
                        className="px-3 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 text-[11px] font-bold transition-colors cursor-pointer border border-slate-200/80"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-500 font-medium">
            <span>
              Page <span className="font-bold text-slate-800">{page}</span> of <span className="font-bold text-slate-800">{totalPages}</span>
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-2 rounded-xl bg-slate-100 disabled:opacity-40 text-slate-700 hover:bg-slate-200 border border-slate-200 transition-colors cursor-pointer"
              >
                <ChevronLeft size={15} />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-2 rounded-xl bg-slate-100 disabled:opacity-40 text-slate-700 hover:bg-slate-200 border border-slate-200 transition-colors cursor-pointer"
              >
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Term Detail Modal */}
      {selectedTerm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200">
                  {selectedTerm.definition_type?.replace('_', ' ')}
                </span>
                <h3 className="text-lg font-black text-slate-900">{selectedTerm.term}</h3>
              </div>
              <button
                onClick={() => setSelectedTerm(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              {/* Definition */}
              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Contextual Definition
                </label>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-slate-800 text-sm leading-relaxed font-medium">
                  {selectedTerm.definition}
                </div>
              </div>

              {/* Source Sentence */}
              {selectedTerm.source_sentence && (
                <div>
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Supporting Document Sentence
                  </label>
                  <blockquote className="p-4 rounded-2xl bg-indigo-50/50 border-l-4 border-indigo-600 text-slate-700 italic font-medium">
                    "{selectedTerm.source_sentence}"
                  </blockquote>
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 block mb-0.5 font-bold uppercase text-[10px]">Frequency</span>
                  <span className="font-extrabold text-slate-900 font-mono text-base">{selectedTerm.frequency}x</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 block mb-0.5 font-bold uppercase text-[10px]">Confidence</span>
                  <span className="font-extrabold text-emerald-600 font-mono text-base">
                    {Math.round(selectedTerm.confidence_score * 100)}%
                  </span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 block mb-0.5 font-bold uppercase text-[10px]">Location</span>
                  <span className="font-extrabold text-slate-800 text-base">Page {selectedTerm.page_number}</span>
                </div>
              </div>

              {/* Related Concepts */}
              {selectedTerm.related_concepts && selectedTerm.related_concepts.length > 0 && (
                <div>
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                    Discovered Relationships ({selectedTerm.related_concepts.length})
                  </label>
                  <div className="space-y-2">
                    {selectedTerm.related_concepts.map((rel, idx) => (
                      <div key={idx} className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-xs">
                        <div className="flex items-center justify-between font-bold text-slate-800 mb-1">
                          <span>
                            {rel.direction === 'outgoing' ? selectedTerm.term : rel.source_name}
                            <span className="text-indigo-700 mx-2 uppercase text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-indigo-100">
                              {rel.relation_type}
                            </span>
                            {rel.direction === 'outgoing' ? rel.target_name : selectedTerm.term}
                          </span>
                          <span className="text-emerald-600 text-[11px] font-mono font-bold">
                            {Math.round((rel.confidence_score || 0.5) * 100)}% conf
                          </span>
                        </div>
                        {rel.supporting_sentence && (
                          <p className="text-[11px] text-slate-500 italic font-medium">"{rel.supporting_sentence}"</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50/70 text-right">
              <button
                onClick={() => setSelectedTerm(null)}
                className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
