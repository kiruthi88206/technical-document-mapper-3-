import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FileText,
  Play,
  Network,
  Download,
  AlertTriangle,
  BookOpen,
  Layers,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  RefreshCw,
  Clock,
  HardDrive,
  FileCode,
} from 'lucide-react';
import api from '../services/api';

export default function DocumentDetailPage() {
  const { id } = useParams();

  const [document, setDocument] = useState(null);
  const [terminology, setTerminology] = useState([]);
  const [concepts, setConcepts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('chunks'); // chunks, terms
  const [expandedChunk, setExpandedChunk] = useState(null);

  const fetchDocumentData = async () => {
    try {
      setLoading(true);
      const [docRes, termRes, concRes] = await Promise.all([
        api.getDocument(id),
        api.getTerminology({ documentId: id, limit: 100 }),
        api.getConcepts({ documentId: id }),
      ]);

      if (docRes.success) setDocument(docRes.document);
      if (termRes.success) setTerminology(termRes.terminology || []);
      if (concRes.success) setConcepts(concRes.concepts || []);
    } catch (err) {
      console.error('Failed to load document details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocumentData();
  }, [id]);

  const handleReprocess = async () => {
    setProcessing(true);
    try {
      await api.processDocument(id, { maxTerms: 40, minFreq: 1 });
      await fetchDocumentData();
    } catch (err) {
      alert(`Processing error: ${err.response?.data?.error || err.message}`);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
        <span className="text-sm font-semibold">Loading document intelligence...</span>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="p-12 text-center bg-white rounded-3xl border border-slate-200/80 shadow-sm max-w-lg mx-auto my-12">
        <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mx-auto mb-4">
          <FileText size={24} />
        </div>
        <h3 className="text-base font-bold text-slate-800 mb-1">Document not found</h3>
        <p className="text-xs text-slate-500 mb-6">The requested document record does not exist or has been removed.</p>
        <Link to="/documents" className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition-colors">
          Back to Documents
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-200">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm">
        <div className="space-y-1.5">
          <Link to="/documents" className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1.5 font-bold mb-1 group">
            <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
            <span>All Documents</span>
          </Link>
          <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
              <FileText size={20} />
            </div>
            <span className="truncate max-w-xl">{document.original_filename}</span>
          </h1>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1 font-medium">
            <span className="uppercase font-mono text-[11px] font-bold px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-100">
              {document.file_type}
            </span>
            <span className="flex items-center gap-1"><HardDrive size={12} className="text-slate-400" />{Math.round((document.file_size || 0) / 1024)} KB</span>
            <span>·</span>
            <span className="flex items-center gap-1"><FileCode size={12} className="text-slate-400" />{document.word_count || 0} words</span>
            <span>·</span>
            <span className="flex items-center gap-1"><Clock size={12} className="text-slate-400" />Uploaded {document.upload_date ? new Date(document.upload_date).toLocaleString() : 'N/A'}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleReprocess}
            disabled={processing}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs transition-colors shadow-md shadow-indigo-600/20 flex items-center gap-2 cursor-pointer"
          >
            <Play size={13} className={processing ? 'animate-spin' : ''} />
            <span>{document.total_concepts > 0 ? 'Reprocess NLP' : 'Process NLP'}</span>
          </button>

          {document.total_concepts > 0 && (
            <Link
              to={`/mapper?documentId=${document.id}`}
              className="px-4 py-2.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/80 font-bold text-xs transition-colors flex items-center gap-2 shadow-sm"
            >
              <Network size={14} />
              <span>Interactive Graph</span>
            </Link>
          )}

          {document.total_concepts > 0 && (
            <a
              href={api.getExportReportUrl(document.id)}
              download
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-sm"
              title="Download Executive PDF Analysis Report"
            >
              <Download size={15} />
            </a>
          )}
        </div>
      </div>

      {/* Warning Notice if any */}
      {document.warning_message && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-3">
          <AlertTriangle size={17} className="text-amber-600 shrink-0" />
          <span className="font-medium">{document.warning_message}</span>
        </div>
      )}

      {/* Processing Error if failed */}
      {document.status === 'failed' && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-3">
          <AlertTriangle size={17} className="text-rose-600 shrink-0" />
          <div>
            <b>Processing Failed:</b> {document.error_message || 'Unknown processing error occurred.'}
          </div>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Text Chunks</span>
          <span className="text-3xl font-black text-slate-900 font-mono">{document.total_chunks || 0}</span>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Extracted Terms</span>
          <span className="text-3xl font-black text-emerald-600 font-mono">{document.total_terms || 0}</span>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Concepts Mapped</span>
          <span className="text-3xl font-black text-indigo-600 font-mono">{document.total_concepts || 0}</span>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Discovered Relations</span>
          <span className="text-3xl font-black text-purple-600 font-mono">{document.total_relationships || 0}</span>
        </div>
      </div>

      {/* Content Tabs */}
      <div className="space-y-4">
        <div className="flex border-b border-slate-200 gap-4 px-1">
          <button
            onClick={() => setActiveTab('chunks')}
            className={`pb-3.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
              activeTab === 'chunks'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Layers size={15} />
            <span>Extracted Chunks ({document.chunks_preview?.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('terms')}
            className={`pb-3.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
              activeTab === 'terms'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <BookOpen size={15} />
            <span>Extracted Terminology ({terminology.length})</span>
          </button>
        </div>

        {/* Tab 1: Chunks Preview */}
        {activeTab === 'chunks' && (
          <div className="space-y-3">
            {document.chunks_preview?.map((chk) => (
              <div
                key={chk.id}
                className="rounded-2xl bg-white border border-slate-200/80 shadow-sm overflow-hidden text-xs transition-shadow hover:shadow-md"
              >
                <div
                  onClick={() => setExpandedChunk(expandedChunk === chk.id ? null : chk.id)}
                  className="px-5 py-4 flex items-center justify-between cursor-pointer hover:bg-slate-50/70 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded-lg border border-indigo-100">
                      #{chk.chunk_index}
                    </span>
                    <span className="font-bold text-slate-800">
                      {chk.section_heading || `Section ${chk.chunk_index}`}
                    </span>
                    <span className="text-[11px] text-slate-400 font-medium">· Page {chk.page_number} · {chk.token_count} words</span>
                  </div>
                  {expandedChunk === chk.id ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
                </div>

                {expandedChunk === chk.id && (
                  <div className="p-5 bg-slate-50/70 border-t border-slate-100 text-slate-700 text-xs leading-relaxed font-mono whitespace-pre-wrap">
                    {chk.text}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Terminology List */}
        {activeTab === 'terms' && (
          <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                    <th className="pb-3.5">Term</th>
                    <th className="pb-3.5">Type</th>
                    <th className="pb-3.5">Freq</th>
                    <th className="pb-3.5">Confidence</th>
                    <th className="pb-3.5">Definition Preview</th>
                    <th className="pb-3.5">Page</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {terminology.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 font-bold text-slate-900">{t.term}</td>
                      <td className="py-3.5">
                        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-lg bg-slate-100 text-slate-700 capitalize border border-slate-200">
                          {t.definition_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3.5 font-mono font-semibold text-slate-800">{t.frequency}</td>
                      <td className="py-3.5 font-mono font-bold text-emerald-600">
                        {Math.round(t.confidence_score * 100)}%
                      </td>
                      <td className="py-3.5 max-w-md truncate text-slate-500 font-medium">
                        {t.definition}
                      </td>
                      <td className="py-3.5 text-slate-500 font-medium">Page {t.page_number}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
