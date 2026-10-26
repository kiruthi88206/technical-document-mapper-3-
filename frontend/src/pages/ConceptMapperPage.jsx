import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Network,
  Download,
  RefreshCw,
  FileSpreadsheet,
} from 'lucide-react';
import GraphViewer from '../components/GraphViewer';
import api from '../services/api';

export default function ConceptMapperPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const docIdParam = searchParams.get('documentId');

  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(docIdParam || '');
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);

  // Fetch document list for dropdown selector
  useEffect(() => {
    api.getDocuments().then((res) => {
      if (res.success && res.documents) {
        setDocuments(res.documents);
        // If no doc selected, pick first processed doc
        if (!selectedDocId && res.documents.length > 0) {
          const firstProcessed = res.documents.find((d) => d.total_concepts > 0) || res.documents[0];
          setSelectedDocId(firstProcessed.id);
          setSearchParams({ documentId: firstProcessed.id });
        }
      }
    });
  }, []);

  // Fetch graph whenever selectedDocId changes
  const fetchGraph = async (id) => {
    if (!id) return;
    setLoading(true);
    setSelectedNode(null);
    try {
      const data = await api.getDocumentGraph(id);
      if (data.success) {
        setGraphData(data);
      }
    } catch (err) {
      console.error('Failed to load concept graph:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDocId) {
      fetchGraph(selectedDocId);
    }
  }, [selectedDocId]);

  const handleDocumentChange = (newDocId) => {
    setSelectedDocId(newDocId);
    setSearchParams({ documentId: newDocId });
  };

  return (
    <div className="h-[calc(100vh-5.5rem)] flex flex-col space-y-3 pb-2 animate-in fade-in duration-200">
      {/* Top Bar: Document Switcher, Stats & Export Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-white border border-slate-200/80 rounded-2xl shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Network size={17} />
            </div>
            <span className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Concept Graph:</span>
          </div>

          {/* Document Selector Dropdown */}
          <select
            value={selectedDocId}
            onChange={(e) => handleDocumentChange(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-slate-800 font-bold focus:outline-none focus:border-indigo-500 max-w-[280px] truncate shadow-sm transition-colors cursor-pointer"
          >
            {documents.length === 0 ? (
              <option value="">No documents available</option>
            ) : (
              documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename} ({d.total_concepts} concepts)
                </option>
              ))
            )}
          </select>

          {/* Quick reload */}
          <button
            onClick={() => fetchGraph(selectedDocId)}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer border border-slate-200"
            title="Reload graph"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Graph Meta Pills & Direct Export Links */}
        <div className="flex items-center gap-2.5 text-xs">
          {graphData?.metrics && (
            <div className="hidden md:flex items-center gap-3 text-slate-500 mr-2 text-[11px] font-mono">
              <span><b className="text-slate-800">{graphData.metrics.nodes_count}</b> concepts</span>
              <span>·</span>
              <span><b className="text-slate-800">{graphData.metrics.edges_count}</b> relationships</span>
              <span>·</span>
              <span>Primary Hub: <b className="text-indigo-600 font-bold">{graphData.metrics.primary_hub}</b></span>
            </div>
          )}

          {selectedDocId && (
            <div className="flex items-center gap-2">
              <a
                href={api.getExportReportUrl(selectedDocId)}
                download
                className="px-3.5 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs border border-indigo-200 transition-colors flex items-center gap-1.5 shadow-sm"
                title="Download Executive PDF Analysis"
              >
                <Download size={13} />
                <span>PDF Report</span>
              </a>

              <a
                href={api.getExportTerminologyUrl(selectedDocId, 'csv')}
                download
                className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs border border-slate-200 transition-colors flex items-center gap-1 shadow-sm"
                title="Download Terminology CSV"
              >
                <FileSpreadsheet size={13} />
                <span>CSV</span>
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Main Interactive React Flow Area */}
      <div className="flex-1 w-full min-h-0 relative rounded-3xl overflow-hidden border border-slate-200/80 shadow-sm bg-white">
        {loading ? (
          <div className="h-full w-full flex flex-col items-center justify-center bg-slate-50 text-slate-500 text-xs gap-3">
            <RefreshCw size={24} className="animate-spin text-indigo-600" />
            <span className="font-semibold text-slate-700">Calculating spring layout and generating concept graph...</span>
          </div>
        ) : (
          <GraphViewer
            graphData={graphData}
            selectedNode={selectedNode}
            setSelectedNode={setSelectedNode}
          />
        )}
      </div>
    </div>
  );
}
