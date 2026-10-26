import React, { useState, useEffect } from 'react';
import { X, Network, BookOpen, ShieldCheck, Hash, ArrowRight, ArrowLeft, ExternalLink, Activity, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function NodeDetailsPanel({ selectedNode, onClose, onFocusConcept }) {
  const [relationships, setRelationships] = useState({ outgoing: [], incoming: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedNode?.id) return;
    let isMounted = true;
    setLoading(true);

    api.getConceptRelationships(selectedNode.id)
      .then((data) => {
        if (isMounted && data.success) {
          setRelationships({
            outgoing: data.outgoing || [],
            incoming: data.incoming || [],
          });
        }
      })
      .catch(() => {
        if (isMounted) {
          setRelationships({ outgoing: [], incoming: [] });
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedNode?.id]);

  if (!selectedNode) return null;

  const color = selectedNode.color || '#6366f1';
  const confidencePercent = Math.round((selectedNode.confidence_score || 0.5) * 100);

  return (
    <aside className="w-80 md:w-96 bg-white/95 backdrop-blur-xl border-l border-slate-200 p-5 text-xs space-y-4 h-full overflow-y-auto shrink-0 shadow-2xl z-20 animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1.5 pr-2">
          <span
            className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white shadow-sm"
            style={{ backgroundColor: color }}
          >
            {selectedNode.category || 'General Concept'}
          </span>
          <h3 className="text-lg font-black text-slate-900 leading-snug tracking-tight">{selectedNode.label}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-xl text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Close details"
        >
          <X size={18} />
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-3 gap-2 bg-slate-50 p-3 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <span className="text-[10px] text-slate-500 font-medium block mb-0.5">Frequency</span>
          <span className="font-extrabold text-slate-900 font-mono text-sm">{selectedNode.frequency || 1}x</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 font-medium block mb-0.5">Confidence</span>
          <span className="font-extrabold text-emerald-600 font-mono text-sm">{confidencePercent}%</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 font-medium block mb-0.5">Centrality</span>
          <span className="font-extrabold text-indigo-600 font-mono text-sm">
            {(selectedNode.centrality_score || 0).toFixed(2)}
          </span>
        </div>
      </div>

      {/* Extracted Definition */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-1.5 text-slate-800 font-bold text-xs">
          <BookOpen size={14} className="text-indigo-600" />
          <span>Extracted Definition</span>
        </div>
        <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 text-slate-800 text-xs leading-relaxed font-sans shadow-sm">
          {selectedNode.definition || 'No explicit definition extracted from document.'}
        </div>
      </div>

      {/* Source Context Sentence */}
      {selectedNode.description && selectedNode.description !== selectedNode.definition && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-slate-600 font-semibold text-xs">
            <Activity size={13} className="text-slate-500" />
            <span>Document Context</span>
          </div>
          <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-200/80 text-slate-600 text-[11px] italic leading-normal">
            "{selectedNode.description}"
          </div>
        </div>
      )}

      {/* Outgoing Relationships */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-slate-800 font-bold text-xs">
          <span className="flex items-center gap-1.5">
            <ArrowRight size={13} className="text-blue-600" />
            Outgoing Relationships ({relationships.outgoing.length})
          </span>
        </div>

        {relationships.outgoing.length === 0 ? (
          <p className="text-[11px] text-slate-400 italic">No outgoing connections.</p>
        ) : (
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {relationships.outgoing.map((rel, idx) => (
              <div
                key={rel.id || idx}
                onClick={() => onFocusConcept && onFocusConcept(rel.target_name)}
                className="p-2.5 bg-slate-50 hover:bg-indigo-50/70 rounded-xl border border-slate-200/90 cursor-pointer transition-all flex items-center justify-between gap-2 shadow-sm"
              >
                <div className="truncate">
                  <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">
                    {rel.relation_type}
                  </span>
                  <span className="text-slate-800 font-bold truncate block">{rel.target_name}</span>
                </div>
                <ArrowRight size={13} className="text-slate-400 shrink-0" />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Incoming Relationships */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-slate-800 font-bold text-xs">
          <span className="flex items-center gap-1.5">
            <ArrowLeft size={13} className="text-emerald-600" />
            Incoming Relationships ({relationships.incoming.length})
          </span>
        </div>

        {relationships.incoming.length === 0 ? (
          <p className="text-[11px] text-slate-400 italic">No incoming connections.</p>
        ) : (
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {relationships.incoming.map((rel, idx) => (
              <div
                key={rel.id || idx}
                onClick={() => onFocusConcept && onFocusConcept(rel.source_name)}
                className="p-2.5 bg-slate-50 hover:bg-emerald-50/70 rounded-xl border border-slate-200/90 cursor-pointer transition-all flex items-center justify-between gap-2 shadow-sm"
              >
                <div className="truncate">
                  <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">
                    {rel.relation_type}
                  </span>
                  <span className="text-slate-800 font-bold truncate block">{rel.source_name}</span>
                </div>
                <ArrowLeft size={13} className="text-slate-400 shrink-0" />
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
