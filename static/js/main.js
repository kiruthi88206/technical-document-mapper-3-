/**
 * Main Application Controller for Technical Document Terminology and Concept Relationship Mapper
 */
const App = {
    activeDocId: null,
    activeDocName: null,
    currentGraphData: null,
    currentGlossary: [],
    graphViewer: null,
    selectedFile: null,

    async init() {
        console.log("[DOCMAPPER] Initializing client application...");
        this.graphViewer = new KnowledgeGraphViewer('vis-network-canvas');
        this.graphViewer.setOnNodeSelected((details) => this.renderInspector(details));

        this.bindEvents();
        await this.checkSystemStatus();
        await this.loadDocumentLibrary();

        // If documents exist, load the most recent one. Otherwise, load sample NLP demo so graph is instantly displayed!
        const docList = await API.getDocuments().catch(() => ({ documents: [] }));
        if (docList.documents && docList.documents.length > 0) {
            const firstDoc = docList.documents[0];
            await this.loadExistingDocument(firstDoc.doc_id, firstDoc.filename);
        } else {
            console.log("[DOCMAPPER] First run: auto-loading NLP architecture demonstration sample.");
            await this.loadSample('nlp_architecture', true);
        }
    },

    bindEvents() {
        // Tab Navigation
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                this.switchTab(targetTab);
            });
        });

        // Global Search
        const searchInput = document.getElementById('global-search-input');
        const clearBtn = document.getElementById('search-clear-btn');
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            clearBtn.style.display = query ? 'block' : 'none';
            if (query.length >= 2) {
                const matched = this.graphViewer.highlightSearch(query);
                if (matched) {
                    this.switchTab('dashboard-view');
                }
            }
        });
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            this.graphViewer.resetView();
        });

        // Graph Toolbar
        document.getElementById('btn-zoom-in').addEventListener('click', () => this.graphViewer.zoomIn());
        document.getElementById('btn-zoom-out').addEventListener('click', () => this.graphViewer.zoomOut());
        document.getElementById('btn-zoom-fit').addEventListener('click', () => this.graphViewer.fitToScreen());
        document.getElementById('btn-reset-layout').addEventListener('click', () => {
            this.graphViewer.resetView();
            this.showToast('Graph view reset to initial bounds', 'info');
        });
        document.getElementById('btn-toggle-physics').addEventListener('click', (e) => {
            const enabled = this.graphViewer.togglePhysics();
            this.showToast(enabled ? 'Physics simulation enabled' : 'Physics simulation paused', 'info');
        });
        document.getElementById('btn-toggle-hierarchy').addEventListener('click', () => {
            const isHierarchical = this.graphViewer.toggleHierarchy();
            this.showToast(isHierarchical ? 'Hierarchical tree mode enabled' : 'Force-directed layout enabled', 'info');
        });
        document.getElementById('btn-capture-png').addEventListener('click', () => {
            this.graphViewer.capturePng();
            this.showToast('Knowledge graph captured as PNG image', 'success');
        });

        // Inspector Close
        document.getElementById('btn-close-inspector').addEventListener('click', () => {
            this.clearInspector();
        });

        // Drag and Drop Upload
        const dropZone = document.getElementById('document-drop-zone');
        const fileInput = document.getElementById('file-input');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                this.stageFile(e.dataTransfer.files[0]);
            }
        });
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.stageFile(e.target.files[0]);
            }
        });

        // Staged File Actions
        document.getElementById('btn-cancel-file').addEventListener('click', () => this.unstageFile());
        document.getElementById('btn-process-file').addEventListener('click', () => this.uploadAndAnalyzeStagedFile());

        // Paste Text Action
        document.getElementById('btn-analyze-pasted').addEventListener('click', () => this.analyzePastedText());

        // Glossary Filtering
        const glossaryInput = document.getElementById('glossary-search-input');
        glossaryInput.addEventListener('input', () => this.filterGlossary());

        document.querySelectorAll('#glossary-filter-pills .pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('#glossary-filter-pills .pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.filterGlossary();
            });
        });

        // Modals Open/Close
        document.getElementById('btn-open-add-node').addEventListener('click', () => this.openModal('modal-add-node'));
        document.getElementById('btn-open-add-edge').addEventListener('click', () => {
            this.populateEdgeModalOptions();
            this.openModal('modal-add-edge');
        });

        document.querySelectorAll('[data-close]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modalId = btn.getAttribute('data-close');
                this.closeModal(modalId);
            });
        });

        // Form Submissions
        document.getElementById('btn-submit-add-node').addEventListener('click', () => this.submitAddNode());
        document.getElementById('btn-submit-add-edge').addEventListener('click', () => this.submitAddEdge());

        // Export Actions
        document.getElementById('btn-export-quick').addEventListener('click', () => this.switchTab('export-view'));
        document.getElementById('btn-generate-pdf').addEventListener('click', () => this.exportFile('pdf'));
        document.getElementById('btn-export-csv-tab').addEventListener('click', () => this.exportFile('csv'));
        document.getElementById('btn-download-glossary-csv').addEventListener('click', () => this.exportFile('csv'));
        document.getElementById('btn-export-json').addEventListener('click', () => this.exportFile('json'));
        document.getElementById('btn-export-image-tab').addEventListener('click', () => {
            this.graphViewer.capturePng();
            this.showToast('Knowledge graph image downloaded', 'success');
        });
        document.getElementById('btn-quick-samples').addEventListener('click', () => this.switchTab('upload-view'));
    },

    switchTab(tabId) {
        document.querySelectorAll('.tab-pane').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));

        const targetPane = document.getElementById(tabId);
        if (targetPane) {
            targetPane.classList.add('active');
        }

        const navBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
        if (navBtn) {
            navBtn.classList.add('active');
        }

        if (tabId === 'dashboard-view' && this.graphViewer) {
            setTimeout(() => this.graphViewer.fitToScreen(), 200);
        } else if (tabId === 'library-view') {
            this.loadDocumentLibrary();
        }
    },

    async checkSystemStatus() {
        try {
            const status = await API.getStatus();
            const dot = document.getElementById('system-status-dot');
            const label = document.getElementById('system-status-text');
            const badge = document.getElementById('nlp-model-badge');

            if (status.database.mode === 'mongodb') {
                dot.className = 'status-dot online';
                label.textContent = 'MongoDB Connected';
            } else {
                dot.className = 'status-dot online';
                label.textContent = 'Local Database (Ready)';
            }

            badge.innerHTML = status.spacy_loaded 
                ? '<i class="fa-solid fa-brain"></i> spaCy + TF-IDF Active' 
                : '<i class="fa-solid fa-brain"></i> TF-IDF + Heuristic NLP Active';
        } catch (error) {
            document.getElementById('system-status-text').textContent = 'Offline';
        }
    },

    stageFile(file) {
        const allowed = ['pdf', 'docx', 'txt'];
        const ext = file.name.split('.').pop().toLowerCase();
        if (!allowed.includes(ext)) {
            this.showToast(`Unsupported file type '.${ext}'. Please choose PDF, DOCX, or TXT.`, 'error');
            return;
        }

        this.selectedFile = file;
        document.getElementById('staged-file-name').textContent = file.name;
        document.getElementById('staged-file-size').textContent = `${(file.size / 1024).toFixed(1)} KB`;
        document.getElementById('file-staging-card').style.display = 'flex';
        document.getElementById('document-drop-zone').style.display = 'none';
    },

    unstageFile() {
        this.selectedFile = null;
        document.getElementById('file-staging-card').style.display = 'none';
        document.getElementById('document-drop-zone').style.display = 'block';
        document.getElementById('file-input').value = '';
    },

    async uploadAndAnalyzeStagedFile() {
        if (!this.selectedFile) return;

        const formData = new FormData();
        formData.append('file', this.selectedFile);

        const btn = document.getElementById('btn-process-file');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting & Parsing...';

        try {
            const uploadRes = await API.uploadFile(formData);
            this.showToast(`Extracted ${uploadRes.word_count} words from '${uploadRes.filename}'`, 'success');

            btn.innerHTML = '<i class="fa-solid fa-brain fa-spin"></i> Detecting Concept Relationships...';
            const analyzeRes = await API.analyzeDocument({ doc_id: uploadRes.doc_id });

            this.unstageFile();
            this.activeDocId = uploadRes.doc_id;
            this.activeDocName = uploadRes.filename;

            this.applyAnalysisResults(analyzeRes);
            this.switchTab('dashboard-view');
            this.showToast(`Knowledge graph generated: ${analyzeRes.concepts_count} concepts, ${analyzeRes.relationships_count} links!`, 'success');

        } catch (error) {
            this.showToast(error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-brain"></i> Extract & Map Relationships';
        }
    },

    async analyzePastedText() {
        const title = document.getElementById('paste-doc-title').value.trim() || 'Pasted Technical Text';
        const text = document.getElementById('paste-doc-text').value.trim();

        if (text.length < 30) {
            this.showToast('Please enter at least 30 characters of technical content.', 'error');
            return;
        }

        const btn = document.getElementById('btn-analyze-pasted');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing NLP Pipeline...';

        try {
            const res = await API.analyzeDocument({ text, title });
            this.activeDocId = res.doc_id;
            this.activeDocName = title;

            this.applyAnalysisResults(res);
            this.switchTab('dashboard-view');
            this.showToast(`Successfully analyzed pasted content into knowledge graph!`, 'success');

            document.getElementById('paste-doc-text').value = '';
            document.getElementById('paste-doc-title').value = '';
        } catch (error) {
            this.showToast(error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Analyze Pasted Content';
        }
    },

    async loadSample(sampleId, silent = false) {
        try {
            const sampleRes = await API.loadSample(sampleId);
            if (!silent) {
                this.showToast(`Loaded sample: '${sampleRes.title}'`, 'info');
            }

            const analyzeRes = await API.analyzeDocument({ doc_id: sampleRes.doc_id });
            this.activeDocId = sampleRes.doc_id;
            this.activeDocName = sampleRes.filename;

            this.applyAnalysisResults(analyzeRes);
            this.switchTab('dashboard-view');
            if (!silent) {
                this.showToast(`Graph generated: ${analyzeRes.concepts_count} concepts, ${analyzeRes.relationships_count} links.`, 'success');
            }
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    },

    async loadExistingDocument(docId, filename) {
        try {
            this.activeDocId = docId;
            this.activeDocName = filename;

            const graphData = await API.getGraph(docId);
            const glossaryData = await API.getGlossary(docId);

            this.currentGraphData = graphData;
            this.currentGlossary = glossaryData.glossary || [];

            this.updateHeaderBadge(filename);
            this.updateMetricCards({
                filename,
                concepts_count: graphData.nodes ? graphData.nodes.length : 0,
                relationships_count: graphData.edges ? graphData.edges.length : 0,
                metrics: graphData.metrics || {}
            });

            this.renderGraph(graphData);
            this.renderGlossary(this.currentGlossary);
        } catch (error) {
            console.error("Error loading document:", error);
        }
    },

    applyAnalysisResults(data) {
        this.currentGraphData = data.graph;
        this.currentGlossary = data.glossary || [];

        this.updateHeaderBadge(data.document_title || this.activeDocName);
        this.updateMetricCards(data);
        this.renderGraph(data.graph);
        this.renderGlossary(this.currentGlossary);
    },

    updateHeaderBadge(filename) {
        const badge = document.getElementById('active-doc-badge');
        badge.innerHTML = `<i class="fa-solid fa-file-lines"></i> ${filename}`;
        badge.classList.add('active-doc');
    },

    updateMetricCards(data) {
        document.getElementById('metric-doc-name').textContent = data.filename || data.document_title || '--';
        document.getElementById('metric-concepts-count').textContent = data.concepts_count || (data.graph && data.graph.nodes ? data.graph.nodes.length : 0);
        document.getElementById('metric-relations-count').textContent = data.relationships_count || (data.graph && data.graph.edges ? data.graph.edges.length : 0);

        const metrics = data.metrics || (data.graph ? data.graph.metrics : {}) || {};
        document.getElementById('metric-hub-name').textContent = metrics.primary_hub || '--';
        document.getElementById('metric-graph-density').textContent = `Density: ${metrics.density || '0.00'}`;
    },

    renderGraph(graphData) {
        const overlay = document.getElementById('graph-loading-overlay');
        if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
            overlay.style.display = 'flex';
            return;
        }

        overlay.style.display = 'none';
        this.graphViewer.initNetwork(graphData.nodes, graphData.edges);
    },

    renderInspector(details) {
        const { node, edges, neighbors } = details;
        const container = document.getElementById('inspector-content');

        const categoryPillClass = `badge-${(node.category || 'core').toLowerCase().split(' ')[0]}`;

        let relationsHtml = '';
        if (edges && edges.length > 0) {
            relationsHtml = edges.map(e => {
                const isOut = String(e.from) === String(node.id);
                const neighbor = neighbors ? neighbors.find(n => String(n.id) === (isOut ? String(e.to) : String(e.from))) : null;
                const neighborName = neighbor ? neighbor.label : (isOut ? e.to : e.from);
                const arrowIcon = isOut ? 'fa-arrow-right' : 'fa-arrow-left';

                return `
                    <div class="related-node-pill" onclick="App.graphViewer.focusOnNode('${isOut ? e.to : e.from}')">
                        <span><i class="fa-solid ${arrowIcon}"></i> <b>${neighborName}</b></span>
                        <span class="rel-tag">${e.label || 'related'}</span>
                    </div>
                `;
            }).join('');
        } else {
            relationsHtml = '<div style="font-size:12px; color:#64748B;">No connected relations identified.</div>';
        }

        container.innerHTML = `
            <div class="inspector-card-title">${node.label}</div>
            <span class="inspector-badge" style="background:#1E293B; color:#818CF8; border:1px solid #334155;">${node.category || 'Concept'}</span>

            <div class="inspector-stat-grid">
                <div class="stat-item">
                    <span>Term Frequency</span>
                    <strong>${node.frequency || 1}</strong>
                </div>
                <div class="stat-item">
                    <span>Graph Degree</span>
                    <strong>${node.degree || (edges ? edges.length : 0)}</strong>
                </div>
            </div>

            <div class="inspector-section">
                <h5>Source Definition / Context</h5>
                <p>${node.definition || 'Identified as a salient technical concept within the document corpus.'}</p>
            </div>

            <div class="inspector-section">
                <h5>Connected Concepts (${edges ? edges.length : 0})</h5>
                <div class="related-nodes-list">
                    ${relationsHtml}
                </div>
            </div>

            <div style="margin-top:14px; display:flex; gap:8px;">
                <button class="btn btn-secondary btn-xs" onclick="App.graphViewer.focusOnNode('${node.id}')">
                    <i class="fa-solid fa-crosshairs"></i> Center View
                </button>
                <button class="btn btn-secondary btn-xs" style="color:#EF4444;" onclick="App.deleteNode('${node.id}')">
                    <i class="fa-solid fa-trash"></i> Delete Node
                </button>
            </div>
        `;
    },

    clearInspector() {
        document.getElementById('inspector-content').innerHTML = `
            <div class="empty-inspector">
                <i class="fa-solid fa-mouse-pointer"></i>
                <p>Click any concept node in the graph to inspect definition, TF-IDF ranking, source citations, and relations.</p>
            </div>
        `;
    },

    renderGlossary(glossaryItems) {
        this.currentGlossary = glossaryItems || [];
        this.filterGlossary();
    },

    filterGlossary() {
        const searchTerm = document.getElementById('glossary-search-input').value.toLowerCase().trim();
        const activeCategoryBtn = document.querySelector('#glossary-filter-pills .pill.active');
        const activeCategory = activeCategoryBtn ? activeCategoryBtn.getAttribute('data-category') : 'ALL';

        const container = document.getElementById('glossary-items-container');

        const filtered = this.currentGlossary.filter(item => {
            const matchesSearch = !searchTerm || 
                item.term.toLowerCase().includes(searchTerm) || 
                (item.definition && item.definition.toLowerCase().includes(searchTerm));
            
            const matchesCat = activeCategory === 'ALL' || item.category === activeCategory;
            return matchesSearch && matchesCat;
        });

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1; text-align:center; padding:40px;">
                    <i class="fa-solid fa-magnifying-glass" style="font-size:32px; color:#334155; margin-bottom:12px;"></i>
                    <h3 style="color:#FFF; font-size:16px;">No Glossary Entries Found</h3>
                    <p style="color:#64748B; font-size:13px;">No terms matched your search filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(item => `
            <div class="glossary-card">
                <div class="glossary-card-top">
                    <div class="glossary-term-row">
                        <span class="glossary-term-name">${item.term}</span>
                        <span class="glossary-freq">${item.frequency || 1} occurrences</span>
                    </div>
                    <span style="font-size:11px; background:#101626; border:1px solid #232D48; color:#38BDF8; padding:2px 8px; border-radius:4px;">${item.category || 'Concept'}</span>
                </div>
                <div class="glossary-card-def">${item.definition || 'No explicit definition extracted from text.'}</div>
                <div class="glossary-card-bottom">
                    <span class="glossary-origin-tag"><i class="fa-solid fa-quote-left"></i> ${item.origin || 'Document Text'}</span>
                    <button class="btn btn-outline btn-xs" onclick="App.focusConceptInGraph('${item.term}')">
                        <i class="fa-solid fa-crosshairs"></i> View in Graph
                    </button>
                </div>
            </div>
        `).join('');
    },

    focusConceptInGraph(term) {
        this.switchTab('dashboard-view');
        setTimeout(() => {
            const matched = this.graphViewer.highlightSearch(term);
            if (!matched) {
                this.showToast(`Node '${term}' not found in current graph view`, 'info');
            }
        }, 300);
    },

    async loadDocumentLibrary() {
        const tbody = document.getElementById('documents-table-body');
        try {
            const res = await API.getDocuments();
            if (!res.documents || res.documents.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:24px; color:#64748B;">No stored documents in database.</td></tr>';
                return;
            }

            tbody.innerHTML = res.documents.map(d => `
                <tr>
                    <td><b>${d.filename}</b></td>
                    <td><span style="background:#1E293B; padding:2px 6px; border-radius:4px; font-size:11px;">${d.file_type}</span></td>
                    <td>${d.word_count || 0}</td>
                    <td><span style="color:#38BDF8; font-weight:600;">${d.concept_count || 0}</span></td>
                    <td><span style="color:#10B981; font-weight:600;">${d.relationship_count || 0}</span></td>
                    <td>${d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : '--'}</td>
                    <td><span style="color:${d.status === 'analyzed' ? '#10B981' : '#F59E0B'}">${d.status}</span></td>
                    <td>
                        <button class="btn btn-outline btn-xs" onclick="App.loadExistingDocument('${d.doc_id}', '${d.filename}')">
                            <i class="fa-solid fa-eye"></i> View Graph
                        </button>
                        <button class="btn btn-outline btn-xs" style="color:#EF4444;" onclick="App.deleteDocument('${d.doc_id}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="color:#EF4444;">Failed to load documents.</td></tr>';
        }
    },

    async deleteDocument(docId) {
        if (!confirm('Are you sure you want to delete this document and all its graph analysis?')) return;
        try {
            await API.deleteDocument(docId);
            this.showToast('Document deleted successfully', 'success');
            await this.loadDocumentLibrary();
            if (this.activeDocId === docId) {
                this.activeDocId = null;
                this.graphViewer.initNetwork([], []);
            }
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    },

    // Modal Operations
    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    },

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    },

    populateEdgeModalOptions() {
        if (!this.currentGraphData || !this.currentGraphData.nodes) return;
        const srcSelect = document.getElementById('new-edge-source');
        const dstSelect = document.getElementById('new-edge-target');

        const optionsHtml = this.currentGraphData.nodes.map(n => `<option value="${n.id}">${n.label}</option>`).join('');
        srcSelect.innerHTML = optionsHtml;
        dstSelect.innerHTML = optionsHtml;
    },

    async submitAddNode() {
        if (!this.activeDocId) {
            this.showToast('Please analyze or load a document first.', 'error');
            return;
        }

        const label = document.getElementById('new-node-label').value.trim();
        const category = document.getElementById('new-node-category').value;
        const definition = document.getElementById('new-node-definition').value.trim();

        if (!label) {
            this.showToast('Please enter a concept name.', 'error');
            return;
        }

        try {
            const res = await API.addNode(this.activeDocId, { label, category, definition });
            this.showToast(`Node '${label}' added to knowledge graph!`, 'success');
            this.closeModal('modal-add-node');

            document.getElementById('new-node-label').value = '';
            document.getElementById('new-node-definition').value = '';

            // Reload graph
            await this.loadExistingDocument(this.activeDocId, this.activeDocName);
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    },

    async submitAddEdge() {
        if (!this.activeDocId) {
            this.showToast('Please analyze or load a document first.', 'error');
            return;
        }

        const from = document.getElementById('new-edge-source').value;
        const to = document.getElementById('new-edge-target').value;
        const label = document.getElementById('new-edge-label').value;

        if (from === to) {
            this.showToast('Source and target concepts must be distinct.', 'error');
            return;
        }

        try {
            await API.addEdge(this.activeDocId, { from, to, label });
            this.showToast(`Relationship '${label}' created between concepts!`, 'success');
            this.closeModal('modal-add-edge');

            // Reload graph
            await this.loadExistingDocument(this.activeDocId, this.activeDocName);
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    },

    async deleteNode(nodeId) {
        if (!this.activeDocId) return;
        if (!confirm('Remove this concept node and all connected edges from the graph?')) return;

        try {
            await API.deleteNode(this.activeDocId, nodeId);
            this.showToast('Concept node removed from graph', 'success');
            this.clearInspector();
            await this.loadExistingDocument(this.activeDocId, this.activeDocName);
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    },

    exportFile(format) {
        if (!this.activeDocId) {
            this.showToast('Please analyze or load a document before exporting.', 'error');
            return;
        }

        const url = `/api/export/${this.activeDocId}?format=${format}`;
        window.open(url, '_blank');
        this.showToast(`Generating and downloading ${format.toUpperCase()} export...`, 'info');
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-info');
        toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};

// Initialize App when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
