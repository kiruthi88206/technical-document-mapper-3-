import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  BookOpen,
  Network,
  Share2,
  Upload,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import api from '../services/api';

const PIE_COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4', '#64748b'];

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await api.getDashboardStats();
      if (data.success) {
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load dashboard statistics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-16 text-slate-500">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600 mr-3" />
        <span className="font-semibold text-sm">Loading dashboard analytics...</span>
      </div>
    );
  }

  const metrics = stats?.metrics || {
    total_documents: 0,
    total_processed_documents: 0,
    total_terminology: 0,
    total_concepts: 0,
    total_relationships: 0,
  };

  const categoryChartData = Object.entries(stats?.analytics?.categories_distribution || {}).map(
    ([name, count]) => ({ name, count })
  );

  const relChartData = Object.entries(stats?.analytics?.relationship_types_distribution || {}).map(
    ([name, count]) => ({ name, count })
  );

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-200">
      {/* Top Banner (Attractive Light Gradient) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-7 rounded-3xl bg-gradient-to-r from-indigo-50/90 via-white to-blue-50/80 border border-indigo-100 shadow-sm relative overflow-hidden">
        <div className="space-y-1 relative z-10">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-extrabold text-indigo-700 bg-indigo-100/80 px-2.5 py-0.5 rounded-full uppercase tracking-wider inline-flex items-center gap-1">
              <Sparkles size={12} /> Technical Intelligence Platform
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Document Concept & Relationship Dashboard
          </h1>
          <p className="text-slate-600 text-sm max-w-xl leading-relaxed">
            Automatically extracts domain terminology, explicit definitions, and evidence-backed concept relationships into an interactive knowledge graph.
          </p>
        </div>
        <div className="flex items-center gap-3 relative z-10">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2.5 px-3.5 rounded-2xl bg-white hover:bg-slate-50 text-slate-700 transition-all border border-slate-200 shadow-xs flex items-center gap-2 text-xs font-bold"
            title="Refresh statistics"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin text-indigo-600' : ''} />
            <span>Refresh</span>
          </button>
          <Link
            to="/documents"
            className="px-4 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition-colors shadow-lg shadow-indigo-600/25 flex items-center gap-2"
          >
            <Upload size={14} />
            <span>Upload Document</span>
          </Link>
        </div>
      </div>

      {/* Real Statistics Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Documents */}
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Documents</span>
            <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
              <FileText size={19} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900 tracking-tight">
              {metrics.total_documents}
            </span>
            <span className="text-xs text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">
              {metrics.total_processed_documents} processed
            </span>
          </div>
        </div>

        {/* Card 2: Terminology */}
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Terminology Entries</span>
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
              <BookOpen size={19} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900 tracking-tight">
              {metrics.total_terminology}
            </span>
            <span className="text-xs text-slate-500 font-medium">with definitions</span>
          </div>
        </div>

        {/* Card 3: Concepts */}
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Concepts Identified</span>
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
              <Network size={19} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900 tracking-tight">
              {metrics.total_concepts}
            </span>
            <span className="text-xs text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded-full">categorized</span>
          </div>
        </div>

        {/* Card 4: Relationships */}
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Discovered Relations</span>
            <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-100">
              <Share2 size={19} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900 tracking-tight">
              {metrics.total_relationships}
            </span>
            <span className="text-xs text-purple-600 font-bold bg-purple-50 px-2 py-0.5 rounded-full">evidence-backed</span>
          </div>
        </div>
      </div>

      {/* Analytics Charts (Recharts Light Theme) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Concept Categories Distribution */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">Concept Categories Distribution</h3>
              <p className="text-xs text-slate-500">Classification of extracted domain terminology</p>
            </div>
          </div>
          <div className="h-60 w-full">
            {categoryChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '1rem', fontSize: '12px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }}
                    itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                  />
                  <Bar dataKey="count" fill="#4f46e5" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Upload and process a document to view category metrics.
              </div>
            )}
          </div>
        </div>

        {/* Relationship Types Distribution */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">Relationship Types Distribution</h3>
              <p className="text-xs text-slate-500">Linguistic predicates connecting concepts</p>
            </div>
          </div>
          <div className="h-60 w-full">
            {relChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={relChartData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={82}
                    innerRadius={48}
                    paddingAngle={3}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {relChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '1rem', fontSize: '12px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }}
                    itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Upload and process a document to view relationship distribution.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Two Column Section: Recent Documents & Processing Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Documents Table */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-white border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-extrabold text-slate-900">Recent Documents</h3>
            <Link to="/documents" className="text-xs text-indigo-600 hover:text-indigo-700 font-bold flex items-center gap-1">
              View all repository <ArrowRight size={13} />
            </Link>
          </div>

          {stats?.recent_documents?.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              No documents uploaded yet. Start by uploading a PDF, DOCX, TXT, or MD file.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                    <th className="pb-3">Name</th>
                    <th className="pb-3">Type</th>
                    <th className="pb-3">Concepts</th>
                    <th className="pb-3">Relationships</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-600">
                  {stats?.recent_documents?.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3.5 font-bold text-slate-900 max-w-[200px] truncate">
                        {doc.original_filename}
                      </td>
                      <td className="py-3.5">
                        <span className="uppercase text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                          {doc.file_type}
                        </span>
                      </td>
                      <td className="py-3.5 font-bold text-indigo-600">{doc.total_concepts}</td>
                      <td className="py-3.5 font-bold text-purple-600">{doc.total_relationships}</td>
                      <td className="py-3.5">
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
                      <td className="py-3.5 text-right whitespace-nowrap">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition-colors inline-block mr-1.5"
                        >
                          View
                        </Link>
                        {doc.total_concepts > 0 && (
                          <Link
                            to={`/mapper?documentId=${doc.id}`}
                            className="px-2.5 py-1 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold transition-colors inline-block"
                          >
                            Graph
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Processing Activity */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-1.5">
              <Clock size={15} className="text-slate-400" />
              Pipeline Activity
            </h3>
          </div>

          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
            {stats?.recent_activity?.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No recent jobs logged.</p>
            ) : (
              stats?.recent_activity?.map((job) => (
                <div key={job.id} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 capitalize">{job.current_stage?.replace('_', ' ')}</span>
                    <span className="text-[10px] text-indigo-600 font-mono font-bold bg-indigo-50 px-1.5 py-0.5 rounded">
                      {job.progress_percent}%
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px] truncate">{job.stage_message || 'In progress'}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
