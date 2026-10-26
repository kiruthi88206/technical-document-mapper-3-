import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { ShieldCheck, Network, Zap } from 'lucide-react';

function ConceptNode({ data, selected }) {
  const color = data.color || '#6366f1';
  const confidencePercent = Math.round((data.confidence_score || 0.5) * 100);
  const totalLinks = (data.incoming_count || 0) + (data.outgoing_count || 0);

  return (
    <div
      className={`px-5 py-4 rounded-2xl transition-all duration-200 cursor-pointer min-w-[220px] max-w-[290px] bg-white border-2 select-none ${
        selected
          ? 'ring-4 ring-indigo-400/30 border-indigo-600 shadow-2xl scale-[1.03]'
          : 'border-slate-200/90 hover:border-indigo-400 shadow-md hover:shadow-xl'
      }`}
      style={{
        borderTopWidth: '5px',
        borderTopColor: color,
      }}
    >
      {/* 4 Multi-Directional Handles for clean graph routing */}
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-indigo-600" />
      <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-indigo-600" />
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-indigo-600" />
      <Handle type="source" position={Position.Right} className="!w-3 !h-3 !bg-indigo-600" />

      {/* Header: Category Badge & Frequency */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span
          className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full text-white shadow-sm"
          style={{ backgroundColor: color }}
        >
          {data.category || 'General'}
        </span>
        <span className="text-[11px] font-bold font-mono text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-md">
          {data.frequency || 1}x freq
        </span>
      </div>

      {/* Concept Name (Bigger, Clear, High-Contrast) */}
      <h3 className="text-base font-extrabold text-slate-900 leading-snug line-clamp-2 mb-2.5 tracking-tight">
        {data.label}
      </h3>

      {/* Confidence Score Bar */}
      <div className="space-y-1 mb-2.5">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-500 font-medium flex items-center gap-1">
            <ShieldCheck size={13} className="text-emerald-600" /> Confidence
          </span>
          <span className="text-emerald-700 font-bold font-mono">
            {confidencePercent}%
          </span>
        </div>
        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-300"
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Footer Details */}
      <div className="flex items-center justify-between text-[11px] pt-2 border-t border-slate-100 text-slate-500">
        <span className="flex items-center gap-1 font-medium text-indigo-600">
          <Network size={12} />
          {totalLinks} relations
        </span>
        <span className="text-slate-400 font-mono text-[10px]">
          in:{data.incoming_count || 0} · out:{data.outgoing_count || 0}
        </span>
      </div>
    </div>
  );
}

export default memo(ConceptNode);
