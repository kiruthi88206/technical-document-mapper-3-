import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import ConceptNode from './ConceptNode';
import EdgeEvidenceModal from './EdgeEvidenceModal';
import NodeDetailsPanel from './NodeDetailsPanel';
import {
  Search,
  Filter,
  Maximize2,
  RefreshCw,
  Download,
  Layers,
  Sparkles,
  Info,
  CheckCircle2,
} from 'lucide-react';

const nodeTypes = {
  conceptNode: ConceptNode,
};

export default function GraphViewer({
  graphData,
  onNodeSelect,
  selectedNode,
  setSelectedNode,
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedRelationType, setSelectedRelationType] = useState('ALL');
  const [activeEdge, setActiveEdge] = useState(null);
  const [showMinimap, setShowMinimap] = useState(true);

  // Sync graph data into React Flow nodes and edges
  useEffect(() => {
    if (!graphData || !graphData.nodes) {
      setNodes([]);
      setEdges([]);
      return;
    }

    setNodes(graphData.nodes || []);
    setEdges(graphData.edges || []);
  }, [graphData, setNodes, setEdges]);

  // Filtered nodes and edges based on search, category, and relation type
  const { filteredNodes, filteredEdges } = useMemo(() => {
    if (!nodes.length) return { filteredNodes: [], filteredEdges: [] };

    const query = searchQuery.trim().toLowerCase();

    // 1. Filter Nodes
    const activeNodes = nodes.map((node) => {
      const matchCat = selectedCategory === 'ALL' || (node.data.category || '').toLowerCase() === selectedCategory.toLowerCase();
      const matchQuery = !query || (node.data.label || '').toLowerCase().includes(query);
      const isDimmed = !matchCat || !matchQuery;

      return {
        ...node,
        style: {
          opacity: isDimmed ? 0.22 : 1.0,
          transition: 'opacity 0.2s ease',
        },
      };
    });

    const activeNodeIds = new Set(
      activeNodes.filter((n) => n.style.opacity > 0.5).map((n) => n.id)
    );

    // 2. Filter Edges
    const activeEdges = edges.map((edge) => {
      const matchRel = selectedRelationType === 'ALL' || (edge.data?.relation_type || '') === selectedRelationType;
      const connectsActive = activeNodeIds.has(edge.source) && activeNodeIds.has(edge.target);
      const isVisible = matchRel && connectsActive;

      return {
        ...edge,
        hidden: !isVisible,
      };
    });

    return { filteredNodes: activeNodes, filteredEdges: activeEdges };
  }, [nodes, edges, searchQuery, selectedCategory, selectedRelationType]);

  // Handle Node Click
  const handleNodeClick = useCallback((event, node) => {
    setSelectedNode(node.data);
    if (onNodeSelect) onNodeSelect(node.data);
  }, [setSelectedNode, onNodeSelect]);

  // Handle Edge Click -> opens Evidence Modal
  const handleEdgeClick = useCallback((event, edge) => {
    setActiveEdge(edge);
  }, []);

  // Reset Filters & View
  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('ALL');
    setSelectedRelationType('ALL');
    setSelectedNode(null);
  };

  // Categories and Relationship types list from graph data
  const categoriesList = useMemo(() => {
    if (!graphData?.metrics?.categories) return [];
    return Object.keys(graphData.metrics.categories);
  }, [graphData]);

  const relationTypesList = useMemo(() => {
    if (!graphData?.metrics?.relationship_types) return [];
    return Object.keys(graphData.metrics.relationship_types);
  }, [graphData]);

  // Handle Export topology
  const handleExportPNG = () => {
    const jsonStr = JSON.stringify({ nodes, edges }, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `graph_topology_${graphData?.document_id?.slice(0, 8) || 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Empty State
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center p-8 text-center bg-white rounded-3xl border-2 border-dashed border-slate-200">
        <div className="w-16 h-16 rounded-3xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4 shadow-md">
          <Layers size={32} />
        </div>
        <h3 className="text-lg font-extrabold text-slate-900 mb-1">Concept Knowledge Graph</h3>
        <p className="text-sm text-slate-500 max-w-md mb-6 leading-relaxed">
          No concepts or relationships extracted yet. Select or upload a technical document and click <b>Process Document</b> to build the interactive graph.
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-slate-50 rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden flex">
      {/* React Flow Canvas */}
      <div className="flex-1 h-full relative">
        <ReactFlow
          nodes={filteredNodes}
          edges={filteredEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.15}
          maxZoom={2.8}
          attributionPosition="bottom-left"
          className="bg-slate-50"
        >
          <Background color="#cbd5e1" gap={24} size={1.2} />
          <Controls className="!bg-white !border-slate-200 !shadow-xl !fill-slate-600 !rounded-xl overflow-hidden" />
          {showMinimap && (
            <MiniMap
              nodeColor={(n) => n.data?.color || '#6366f1'}
              maskColor="rgba(241, 245, 249, 0.75)"
              className="!bg-white !border-slate-200 !rounded-2xl overflow-hidden !shadow-xl"
            />
          )}

          {/* Top Floating Control Bar */}
          <Panel position="top-left" className="m-4 flex flex-wrap items-center gap-2.5 bg-white/95 backdrop-blur-md p-2.5 rounded-2xl border border-slate-200 shadow-xl max-w-[850px]">
            {/* Concept Search */}
            <div className="relative">
              <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search concepts..."
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 w-44 font-medium"
              />
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-slate-800 font-semibold focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Categories</option>
              {categoriesList.map((cat) => (
                <option key={cat} value={cat}>
                  {cat} ({graphData.metrics.categories[cat]})
                </option>
              ))}
            </select>

            {/* Relationship Type Filter */}
            <select
              value={selectedRelationType}
              onChange={(e) => setSelectedRelationType(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-slate-800 font-semibold focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Relationships</option>
              {relationTypesList.map((rel) => (
                <option key={rel} value={rel}>
                  {rel} ({graphData.metrics.relationship_types[rel]})
                </option>
              ))}
            </select>

            {/* Reset Filter Button */}
            {(searchQuery || selectedCategory !== 'ALL' || selectedRelationType !== 'ALL') && (
              <button
                onClick={handleResetFilters}
                className="p-1.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors flex items-center gap-1 font-medium"
                title="Reset filters"
              >
                <RefreshCw size={12} />
                <span>Reset</span>
              </button>
            )}

            <div className="h-4 w-[1px] bg-slate-200 mx-1" />

            {/* Export JSON / Topo */}
            <button
              onClick={handleExportPNG}
              className="p-1.5 px-2.5 text-xs text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors flex items-center gap-1.5 font-bold shadow-sm"
              title="Download Graph JSON topology"
            >
              <Download size={13} />
              <span>Topology</span>
            </button>

            {/* Toggle Minimap */}
            <button
              onClick={() => setShowMinimap(!showMinimap)}
              className={`p-1.5 px-2 rounded-xl text-xs font-semibold transition-colors ${
                showMinimap ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-100 text-slate-500'
              }`}
              title="Toggle Minimap"
            >
              <Layers size={13} />
            </button>
          </Panel>

          {/* Bottom Floating Legend */}
          <Panel position="bottom-right" className="m-4 bg-white/95 backdrop-blur-md px-4 py-3 rounded-2xl border border-slate-200 text-xs shadow-xl hidden md:block max-w-sm">
            <div className="font-bold text-slate-800 mb-2 flex items-center gap-1.5">
              <Info size={14} className="text-indigo-600" />
              Graph Legend (Click Edge for Verbatim Evidence)
            </div>
            <div className="flex flex-wrap gap-2 text-[11px] text-slate-600 font-medium">
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> IS_A
              </span>
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> USES
              </span>
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> PART_OF
              </span>
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> DEPENDS_ON
              </span>
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500" /> PRODUCES
              </span>
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/70">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" /> IMPLEMENTS
              </span>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <NodeDetailsPanel
          selectedNode={selectedNode}
          onClose={() => setSelectedNode(null)}
          onFocusConcept={(conceptName) => {
            const target = nodes.find((n) => (n.data?.label || '').toLowerCase() === conceptName.toLowerCase());
            if (target) {
              setSelectedNode(target.data);
            }
          }}
        />
      )}

      {/* Edge Evidence Modal */}
      {activeEdge && (
        <EdgeEvidenceModal
          edge={activeEdge}
          onClose={() => setActiveEdge(null)}
        />
      )}
    </div>
  );
}
