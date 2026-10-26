import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Upload,
  FileText,
  Trash2,
  Play,
  Network,
  Download,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
  FileCode,
  FileSpreadsheet,
  Sparkles,
} from 'lucide-react';
import api from '../services/api';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [processingId, setProcessingId] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const fetchDocs = async () => {
    try {
      const data = await api.getDocuments();
      if (data.success) {
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploadError('');
    setUploading(true);
    setUploadProgress(10);

    try {
      const res = await api.uploadDocument(file, (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percent);
      });

      if (res.success) {
        fetchDocs();
      }
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Upload failed.';
      setUploadError(message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleProcess = async (docId) => {
    setProcessingId(docId);
    try {
      await api.processDocument(docId, { maxTerms: 35, minFreq: 1 });
      await fetchDocs();
    } catch (err) {
      alert(`Processing error: ${err.response?.data?.error || err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All associated terminology, concepts, and relationships will be permanently removed.`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      alert(`Delete error: ${err.response?.data?.error || err.message}`);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Technical Document Library</h1>
          <p className="text-slate-500 text-sm mt-1">
            Ingest PDF, DOCX, TXT, or Markdown documents to segment sections and extract concept graphs.
          </p>
        </div>
        <button
          onClick={fetchDocs}
          className="p-2.5 px-3.5 rounded-2xl bg-white hover:bg-slate-50 text-slate-700 transition-all border border-slate-200 shadow-xs flex items-center gap-2 text-xs font-bold self-start md:self-auto"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin text-indigo-600' : ''} />
          <span>Refresh Library</span>
        </button>
      </div>

      {/* Drag & Drop Upload Zone (Crisp White with Indigo Border) */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`p-10 rounded-3xl border-2 border-dashed transition-all duration-200 cursor-pointer text-center relative overflow-hidden bg-white shadow-sm ${
          isDragOver
            ? 'border-indigo-600 bg-indigo-50/50 scale-[1.005]'
            : 'border-slate-300/80 hover:border-indigo-500 hover:bg-slate-50/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center space-y-3.5">
          <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center shadow-md">
            <Upload size={30} />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-slate-900 mb-1">
              Drag & drop technical document here, or <span className="text-indigo-600 underline">browse computer</span>
            </h3>
            <p className="text-xs text-slate-500">
              Supports PDF, DOCX, TXT, and Markdown (.md) documents up to 25 MB.
            </p>
          </div>
        </div>

        {/* Upload Progress Bar */}
        {uploading && (
          <div className="mt-5 max-w-sm mx-auto">
            <div className="flex justify-between text-xs text-slate-600 font-bold mb-1.5">
              <span>Extracting & Segmenting Chunks...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
              <div
                className="h-full bg-indigo-600 transition-all duration-200 rounded-full"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Validation / Upload Error Banner */}
      {uploadError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-2 font-medium">
            <AlertCircle size={17} className="text-rose-600 shrink-0" />
            <span>{uploadError}</span>
          </div>
          <button
            onClick={() => setUploadError('')}
            className="text-slate-500 hover:text-slate-800 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Documents Table List */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-extrabold text-slate-900">
            Ingested Documents ({documents.length})
          </h2>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs font-medium">
            Loading document repository...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No documents in repository. Use the upload box above to ingest your first technical file.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                  <th className="pb-3">Document</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Size</th>
                  <th className="pb-3">Chunks</th>
                  <th className="pb-3">Concepts</th>
                  <th className="pb-3">Relationships</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-600">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-4">
                      <div className="font-extrabold text-slate-900 max-w-[240px] truncate">
                        {doc.original_filename}
                      </div>
                      <div className="text-[10px] text-slate-400 font-medium">
                        {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Recent'} · {doc.word_count || 0} words
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="uppercase text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="py-4 text-slate-500 font-mono text-[11px]">
                      {Math.round(doc.file_size / 1024)} KB
                    </td>
                    <td className="py-4 font-mono text-[11px] text-slate-700 font-bold">
                      {doc.total_chunks}
                    </td>
                    <td className="py-4 font-mono text-[11px] text-indigo-600 font-extrabold">
                      {doc.total_concepts}
                    </td>
                    <td className="py-4 font-mono text-[11px] text-purple-600 font-extrabold">
                      {doc.total_relationships}
                    </td>
                    <td className="py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        doc.status === 'completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        doc.status === 'completed_with_warnings' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                        doc.status === 'processing' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                        doc.status === 'failed' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-4 text-right space-x-1.5 whitespace-nowrap">
                      {/* Process/Reprocess */}
                      <button
                        onClick={() => handleProcess(doc.id)}
                        disabled={processingId === doc.id}
                        className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-[11px] transition-colors inline-flex items-center gap-1 shadow-sm"
                        title="Run NLP terminology & relationship extraction"
                      >
                        <Play size={11} className={processingId === doc.id ? 'animate-spin' : ''} />
                        <span>{doc.total_concepts > 0 ? 'Reprocess' : 'Process'}</span>
                      </button>

                      {/* View Details */}
                      <Link
                        to={`/documents/${doc.id}`}
                        className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-[11px] transition-colors inline-block"
                      >
                        Detail
                      </Link>

                      {/* Open Concept Map */}
                      {doc.total_concepts > 0 && (
                        <Link
                          to={`/mapper?documentId=${doc.id}`}
                          className="px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-[11px] font-bold transition-colors inline-flex items-center gap-1"
                        >
                          <Network size={11} />
                          <span>Graph</span>
                        </Link>
                      )}

                      {/* Export PDF Report */}
                      {doc.total_concepts > 0 && (
                        <a
                          href={api.getExportReportUrl(doc.id)}
                          download
                          className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors inline-block"
                          title="Download Executive PDF Analysis Report"
                        >
                          <Download size={13} />
                        </a>
                      )}

                      {/* Delete */}
                      <button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        className="p-1.5 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors inline-block"
                        title="Delete Document"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
