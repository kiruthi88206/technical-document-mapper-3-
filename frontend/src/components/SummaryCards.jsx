import React from 'react';
import { Network, GitFork, Activity, FileText } from 'lucide-react';

export default function SummaryCards({ graphData }) {
  if (!graphData) return null;

  const nodeCount = graphData.nodes?.length || 0;
  const edgeCount = graphData.edges?.length || 0;
  const meta = graphData.metadata || {};
  const density = meta.density !== undefined ? (meta.density * 100).toFixed(1) + '%' : '0.0%';
  const wordCount = meta.word_count || 0;

  const cards = [
    {
      title: 'Extracted Concepts',
      value: nodeCount,
      sub: `${meta.connected_components || 1} connected clusters`,
      icon: Network,
      color: 'from-blue-500/20 to-indigo-500/20 text-indigo-400 border-indigo-500/30'
    },
    {
      title: 'Identified Relationships',
      value: edgeCount,
      sub: `${nodeCount > 0 ? (edgeCount / nodeCount).toFixed(1) : 0} avg links / concept`,
      icon: GitFork,
      color: 'from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30'
    },
    {
      title: 'Graph Network Density',
      value: density,
      sub: 'Inter-concept connectivity',
      icon: Activity,
      color: 'from-purple-500/20 to-violet-500/20 text-purple-400 border-purple-500/30'
    },
    {
      title: 'Source Corpus Volume',
      value: wordCount.toLocaleString(),
      sub: `${meta.sentence_count || 0} parsed sentences`,
      icon: FileText,
      color: 'from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/30'
    }
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className={`p-3.5 rounded-2xl bg-gradient-to-br ${c.color} bg-slate-900/80 border backdrop-blur-sm shadow-sm flex items-center space-x-3.5`}
          >
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] font-medium text-slate-400">{c.title}</p>
              <p className="text-xl font-extrabold text-white tracking-tight">{c.value}</p>
              <p className="text-[10px] text-slate-400/80">{c.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
