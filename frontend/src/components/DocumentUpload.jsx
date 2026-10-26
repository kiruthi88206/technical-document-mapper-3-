import React, { useState, useRef } from 'react';
import { Upload, FileUp, FileText, CheckCircle2, AlertCircle, Loader2, Sparkles, Sliders, ArrowRight } from 'lucide-react';

export default function DocumentUpload({ 
  onUpload, 
  onAnalyze, 
  uploadedDoc, 
  loading, 
  analyzing, 
  pipelineStep, 
  error,
  options,
  setOptions
}) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      onUpload(file);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      onUpload(file);
    }
  };

  const PIPELINE_STAGES = [
    { id: 1, name: 'Document Ingestion', desc: 'PDF / DOCX / TXT text extraction' },
    { id: 2, name: 'NLP Preprocessing', desc: 'Sentence segmentation & tokenization' },
    { id: 3, name: 'Term Extraction', desc: 'TF-IDF & Noun phrase ranking' },
    { id: 4, name: 'Relationship Detection', desc: 'Co-occurrence & semantic embeddings' },
    { id: 5, name: 'Graph Construction', desc: 'Interactive visual mapping' },
  ];

  return (
    <div className="space-y-4">
      {/* Upload Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-all ${
          dragOver 
            ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]' 
            : 'border-slate-700/80 hover:border-slate-600 bg-slate-900/60 hover:bg-slate-900'
        } ${uploadedDoc ? 'border-emerald-500/50 bg-emerald-950/10' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="flex flex-col items-center justify-center space-y-2.5">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${
            uploadedDoc 
              ? 'bg-emerald-500/20 text-emerald-400' 
              : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
          }`}>
            {loading ? (
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            ) : uploadedDoc ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            ) : (
              <FileUp className="w-6 h-6" />
            )}
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-200">
              {uploadedDoc ? uploadedDoc.filename : 'Drag & drop technical document'}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Supports <span className="text-indigo-400 font-medium">PDF</span>,{' '}
              <span className="text-indigo-400 font-medium">DOCX</span>, or{' '}
              <span className="text-indigo-400 font-medium">TXT</span> (up to 25MB)
            </p>
          </div>

          {!uploadedDoc && (
            <button
              type="button"
              className="text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 mt-1 pointer-events-none"
            >
              Browse Local Files
            </button>
          )}
        </div>
      </div>

      {/* Uploaded File Details Card */}
      {uploadedDoc && (
        <div className="bg-slate-900/80 rounded-xl p-3 border border-slate-800 space-y-2 text-xs">
          <div className="flex items-center justify-between text-slate-300 font-medium">
            <span className="flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span className="truncate max-w-[180px]">{uploadedDoc.filename}</span>
            </span>
            <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
              {(uploadedDoc.file_size_bytes / 1024).toFixed(1)} KB
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-1 border-t border-slate-800/80 text-[11px] text-slate-400">
            <div>
              <span className="block text-slate-500 text-[10px]">Words</span>
              <span className="font-semibold text-slate-200">{uploadedDoc.word_count || 0}</span>
            </div>
            <div>
              <span className="block text-slate-500 text-[10px]">Sentences</span>
              <span className="font-semibold text-slate-200">{uploadedDoc.sentence_count || 0}</span>
            </div>
            <div>
              <span className="block text-slate-500 text-[10px]">Read Time</span>
              <span className="font-semibold text-slate-200">{uploadedDoc.estimated_read_time_minutes || 1}m</span>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Config & Sliders */}
      <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
          <span className="flex items-center space-x-1.5">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            <span>Extraction Parameters</span>
          </span>
        </div>

        {/* Max Concepts */}
        <div className="space-y-1">
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Max Concepts</span>
            <span className="font-mono text-indigo-400 font-semibold">{options.maxTerms}</span>
          </div>
          <input
            type="range"
            min="10"
            max="60"
            step="5"
            value={options.maxTerms}
            onChange={(e) => setOptions({ ...options, maxTerms: parseInt(e.target.value) })}
            className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
        </div>

        {/* Semantic Similarity Threshold */}
        <div className="space-y-1">
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Semantic Similarity Cutoff</span>
            <span className="font-mono text-indigo-400 font-semibold">{options.simThreshold.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.40"
            max="0.85"
            step="0.05"
            value={options.simThreshold}
            onChange={(e) => setOptions({ ...options, simThreshold: parseFloat(e.target.value) })}
            className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
        </div>
      </div>

      {/* Analyze CTA Button */}
      <button
        onClick={onAnalyze}
        disabled={!uploadedDoc || analyzing}
        className="w-full py-3 px-4 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 text-white shadow-lg shadow-indigo-600/30 hover:opacity-95 active:scale-[0.99] transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
      >
        {analyzing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing Document Pipeline...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            <span>Analyze & Map Concepts</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </>
        )}
      </button>

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Analysis Failed</p>
            <p className="text-[11px] text-rose-200/80 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* 5-Stage Pipeline Progress Tracker */}
      {analyzing && (
        <div className="bg-slate-900/90 rounded-xl p-3 border border-indigo-500/30 space-y-2">
          <p className="text-[11px] font-semibold text-indigo-300 uppercase tracking-wider">
            Pipeline Execution
          </p>
          <div className="space-y-1.5">
            {PIPELINE_STAGES.map((st) => {
              const isDone = pipelineStep > st.id;
              const isCurrent = pipelineStep === st.id;
              return (
                <div key={st.id} className="flex items-center space-x-2 text-xs">
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isDone 
                      ? 'bg-emerald-500 text-slate-950' 
                      : isCurrent 
                      ? 'bg-indigo-500 text-white animate-pulse' 
                      : 'bg-slate-800 text-slate-500'
                  }`}>
                    {isDone ? '✓' : st.id}
                  </div>
                  <span className={`${isCurrent ? 'text-white font-medium' : isDone ? 'text-slate-300' : 'text-slate-500'}`}>
                    {st.name}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
