import React from 'react';
import { X, ArrowRight, BookOpen, ShieldCheck, Tag, Sparkles } from 'lucide-react';

export default function EdgeEvidenceModal({ edge, onClose }) {
  if (!edge || !edge.data) return null;

  const {
    source_name,
    target_name,
    relation_type,
    confidence_score,
    supporting_sentence,
    source_page,
    source_section,
    extraction_method,
    color,
  } = edge.data;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-2.5">
            <span className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: color || '#6366f1' }} />
            <h3 className="font-extrabold text-slate-900 text-base">Verified Concept Relationship</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4">
          {/* Relational Flow Banner */}
          <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-50 border border-slate-200/80 shadow-sm">
            <span className="font-extrabold text-slate-900 text-sm max-w-[130px] truncate">{source_name}</span>
            <div
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider text-white shadow-sm"
              style={{ backgroundColor: color || '#3b82f6' }}
            >
              <span>{relation_type}</span>
              <ArrowRight size={13} />
            </div>
            <span className="font-extrabold text-slate-900 text-sm max-w-[130px] truncate text-right">{target_name}</span>
          </div>

          {/* Supporting Evidence Sentence */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
              <BookOpen size={14} className="text-indigo-600" />
              Source Evidence from Document
            </label>
            <blockquote className="p-4 rounded-2xl bg-indigo-50/50 border-l-4 border-indigo-600 text-slate-800 text-sm leading-relaxed italic font-serif">
              "{supporting_sentence || 'No supporting sentence recorded in source document.'}"
            </blockquote>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70">
              <span className="text-[11px] text-slate-500 font-medium block mb-1 flex items-center gap-1">
                <ShieldCheck size={13} className="text-emerald-600" /> Confidence Score
              </span>
              <span className="text-sm font-bold text-emerald-700 font-mono">
                {Math.round((confidence_score || 0.5) * 100)}% verified
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70">
              <span className="text-[11px] text-slate-500 font-medium block mb-1 flex items-center gap-1">
                <Tag size={13} className="text-blue-600" /> Document Reference
              </span>
              <span className="text-sm font-bold text-slate-800">
                Page {source_page || 1} {source_section ? `· ${source_section}` : ''}
              </span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 text-right">
            Extraction engine: <span className="font-mono font-medium text-slate-600">{extraction_method || 'grammar_predicate'}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50/50 text-right">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-md transition-colors"
          >
            Close Evidence
          </button>
        </div>
      </div>
    </div>
  );
}
