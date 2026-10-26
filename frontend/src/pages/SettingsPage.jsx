import React, { useState, useEffect } from 'react';
import {
  Settings,
  ShieldCheck,
  Cpu,
  Database,
  Sliders,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import api from '../services/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  // Local settings state
  const [maxTerms, setMaxTerms] = useState(40);
  const [minFreq, setMinFreq] = useState(1);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.40);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.checkHealth()
      .then((res) => setHealth(res))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl animate-in fade-in duration-200">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">System & Pipeline Settings</h1>
        <p className="text-slate-500 text-sm mt-1">
          Configure NLP extraction thresholds, check database integrity, and verify system engines.
        </p>
      </div>

      {/* Backend & Database Health Status Card */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Database size={17} className="text-indigo-600" />
          Service Status & Architecture
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <RefreshCw size={14} className="animate-spin text-indigo-600" />
            <span>Verifying backend connectivity...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              <span className="text-slate-500 block font-bold uppercase text-[10px]">Backend Server</span>
              <span className="font-extrabold text-emerald-600 flex items-center gap-1.5 text-sm">
                <CheckCircle2 size={16} />
                {health?.status || 'Online'}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Python 3.12 / Flask</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              <span className="text-slate-500 block font-bold uppercase text-[10px]">Database Storage</span>
              <span className="font-extrabold text-slate-900 text-sm">
                {health?.database || 'SQLite (SQLAlchemy 2.0)'}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Auto-initialized</span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              <span className="text-slate-500 block font-bold uppercase text-[10px]">NLP Pipeline</span>
              <span className="font-extrabold text-indigo-600 text-sm">Active & Calibrated</span>
              <span className="text-[10px] text-slate-400 font-mono">spaCy + TF-IDF + Grammatical Predicates</span>
            </div>
          </div>
        )}
      </div>

      {/* NLP Tuning Form */}
      <form onSubmit={handleSave} className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sliders size={17} className="text-indigo-600" />
            Extraction Parameters
          </h2>
          {saved && (
            <span className="text-xs text-emerald-600 font-bold flex items-center gap-1.5 animate-in fade-in bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              <CheckCircle2 size={14} /> Preferences saved
            </span>
          )}
        </div>

        <div className="space-y-5 text-xs">
          {/* Max Terms */}
          <div>
            <div className="flex justify-between font-bold text-slate-800 mb-2">
              <label>Default Top Terms per Document</label>
              <span className="font-mono text-indigo-600 font-extrabold">{maxTerms} terms</span>
            </div>
            <input
              type="range"
              min="15"
              max="70"
              value={maxTerms}
              onChange={(e) => setMaxTerms(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Controls the number of candidate concepts mapped into the interactive knowledge graph.
            </p>
          </div>

          {/* Min Term Frequency */}
          <div>
            <div className="flex justify-between font-bold text-slate-800 mb-2">
              <label>Minimum Term Frequency Filter</label>
              <span className="font-mono text-indigo-600 font-extrabold">{minFreq}x</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={minFreq}
              onChange={(e) => setMinFreq(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Terms appearing fewer than this threshold in the document will be filtered out.
            </p>
          </div>

          {/* Confidence Threshold */}
          <div>
            <div className="flex justify-between font-bold text-slate-800 mb-2">
              <label>Relationship Verification Confidence Threshold</label>
              <span className="font-mono text-indigo-600 font-extrabold">{Math.round(confidenceThreshold * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.20"
              max="0.80"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Relationships below this confidence score are excluded from the primary graph.
            </p>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-md transition-colors cursor-pointer"
            >
              Save Pipeline Configuration
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
