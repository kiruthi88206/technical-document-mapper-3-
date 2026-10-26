import React from 'react';
import { X, Download, FileJson, FileSpreadsheet, FileText, CheckCircle2 } from 'lucide-react';
import api from '../services/api';

export default function ExportModal({ isOpen, onClose, documentId, docMetadata }) {
  if (!isOpen || !documentId) return null;

  const handleDownload = (format) => {
    let url = '';
    if (format === 'pdf') {
      url = api.getPdfExportUrl(documentId);
    } else {
      url = api.getExportUrl(documentId, format);
    }
    window.open(url, '_blank');
  };

  const exportOptions = [
    {
      format: 'json',
      title: 'Knowledge Graph JSON',
      desc: 'Complete nodes, edges, properties, weights, and graph topology for D3/Neo4j.',
      icon: FileJson,
      color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
      btnText: 'Download JSON',
    },
    {
      format: 'csv',
      title: 'Terminology Glossary CSV',
      desc: 'Extracted technical terms, categories, frequencies, TF-IDF scores, and definitions.',
      icon: FileSpreadsheet,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      btnText: 'Download CSV',
    },
    {
      format: 'pdf',
      title: 'Executive PDF Summary Report',
      desc: 'Professional multi-page PDF with document metrics, top concepts, and relationship tables.',
      icon: FileText,
      color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
      btnText: 'Generate & Download PDF',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl p-6 text-slate-100 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-extrabold text-white tracking-tight">Export Analysis Artifacts</h3>
            <p className="text-xs text-slate-400 mt-1">
              Document: <b className="text-slate-200">{docMetadata?.filename || 'Uploaded Document'}</b>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Options Grid */}
        <div className="space-y-3">
          {exportOptions.map((opt) => {
            const Icon = opt.icon;
            return (
              <div
                key={opt.format}
                className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-all flex items-center justify-between group"
              >
                <div className="flex items-start space-x-3.5 pr-3">
                  <div className={`p-2.5 rounded-xl border ${opt.color} shrink-0 mt-0.5`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 group-hover:text-white transition-colors">
                      {opt.title}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{opt.desc}</p>
                  </div>
                </div>

                <button
                  onClick={() => handleDownload(opt.format)}
                  className="px-3 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-indigo-600 active:scale-95 text-slate-200 hover:text-white border border-slate-700 hover:border-indigo-500 transition-all shrink-0 flex items-center space-x-1.5 shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{opt.btnText}</span>
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
          <span>Session ID: {documentId}</span>
          <button onClick={onClose} className="hover:text-slate-300 font-medium">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
