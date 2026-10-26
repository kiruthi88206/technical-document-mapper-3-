import React from 'react';
import { ZoomIn, ZoomOut, Maximize2, Pause, Play, RotateCcw, Camera } from 'lucide-react';

export default function GraphControls({ 
  onZoomIn, 
  onZoomOut, 
  onFit, 
  onTogglePhysics, 
  physicsEnabled, 
  onResetLayout,
  onCaptureImage 
}) {
  return (
    <div className="absolute top-4 right-4 z-20 flex flex-col space-y-2 bg-slate-900/90 backdrop-blur-md p-1.5 rounded-2xl border border-slate-800 shadow-xl shadow-black/40">
      <button
        onClick={onZoomIn}
        title="Zoom In (+)"
        className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors active:scale-95"
      >
        <ZoomIn className="w-4 h-4" />
      </button>

      <button
        onClick={onZoomOut}
        title="Zoom Out (-)"
        className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors active:scale-95"
      >
        <ZoomOut className="w-4 h-4" />
      </button>

      <button
        onClick={onFit}
        title="Fit Graph to Screen"
        className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors active:scale-95"
      >
        <Maximize2 className="w-4 h-4" />
      </button>

      <div className="w-full h-px bg-slate-800 my-0.5" />

      <button
        onClick={onTogglePhysics}
        title={physicsEnabled ? 'Pause Physics Simulation' : 'Enable Physics Simulation'}
        className={`p-2 rounded-xl transition-colors active:scale-95 ${
          physicsEnabled ? 'text-indigo-400 hover:bg-indigo-500/10' : 'text-slate-400 hover:bg-slate-800'
        }`}
      >
        {physicsEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
      </button>

      <button
        onClick={onResetLayout}
        title="Reset Graph Layout"
        className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors active:scale-95"
      >
        <RotateCcw className="w-4 h-4" />
      </button>

      <button
        onClick={onCaptureImage}
        title="Download Graph Snapshot as PNG"
        className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors active:scale-95"
      >
        <Camera className="w-4 h-4" />
      </button>
    </div>
  );
}
