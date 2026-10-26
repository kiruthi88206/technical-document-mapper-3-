/* ==========================================================================
   APP STATE & SINGLE PAGE APPLICATION (SPA) ROUTER
   ========================================================================== */

const App = {
    currentDocId: null,
    currentDocName: "No Document Selected",
    documents: [],

    init() {
        this.bindEvents();
        this.loadDashboardData();
    },

    bindEvents() {
        // Navigation links
        document.querySelectorAll('.nav-link-custom').forEach(link => {
            link.addEventListener('click', (e) => {
                const targetView = e.currentTarget.getAttribute('data-view');
                this.switchView(targetView);
            });
        });

        // Quick Viva Demo Mode Button
        document.getElementById('btn-load-sample')?.addEventListener('click', () => {
            this.loadSampleData();
        });

        // Open graph from dashboard button
        document.getElementById('btn-open-latest-graph')?.addEventListener('click', () => {
            if (this.currentDocId) {
                this.switchView('view-graph');
            } else {
                this.showToast('Please upload or select a document first.', 'warning');
            }
        });
    },

    switchView(viewId) {
        // Hide all views
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
        document.querySelectorAll('.nav-link-custom').forEach(link => link.classList.remove('active'));

        // Show target view
        const targetSec = document.getElementById(viewId);
        if (targetSec) {
            targetSec.classList.add('active');
        }

        // Highlight nav link
        const targetLink = document.querySelector(`.nav-link-custom[data-view="${viewId}"]`);
        if (targetLink) {
            targetLink.classList.add('active');
            const titleText = targetLink.innerText.trim();
            document.getElementById('current-view-title').innerText = titleText;
        }

        // Trigger view specific initialization
        if (viewId === 'view-graph') {
            if (window.GraphManager) {
                if (this.currentDocId) {
                    window.GraphManager.loadGraph(this.currentDocId);
                } else {
                    this.loadSampleData();
                }
            }
        } else if (viewId === 'view-glossary') {
            if (window.GlossaryManager) {
                if (this.currentDocId) {
                    window.GlossaryManager.loadGlossary(this.currentDocId);
                } else {
                    this.loadSampleData();
                }
            }
        } else if (viewId === 'view-saved') {
            if (window.SavedDocsManager) {
                window.SavedDocsManager.loadSavedDocs();
            }
        } else if (viewId === 'view-dashboard') {
            this.loadDashboardData();
        }
    },

    setActiveDocument(docId, docName) {
        this.currentDocId = docId;
        this.currentDocName = docName;
        document.getElementById('active-doc-name').innerText = docName;
    },

    async loadDashboardData() {
        try {
            const res = await fetch('/api/documents');
            const docs = await res.json();
            this.documents = docs;

            let totalTerms = 0;
            let totalConcepts = 0;
            let totalRels = 0;

            docs.forEach(d => {
                if (d.stats) {
                    totalTerms += d.stats.terms_count || 0;
                    totalConcepts += d.stats.concepts_count || 0;
                    totalRels += d.stats.relationships_count || 0;
                }
            });

            document.getElementById('metric-docs').innerText = docs.length;
            document.getElementById('metric-terms').innerText = totalTerms;
            document.getElementById('metric-concepts').innerText = totalConcepts;
            document.getElementById('metric-relationships').innerText = totalRels;

            // Set latest doc card
            const analyzedDocs = docs.filter(d => d.status === 'analyzed');
            if (analyzedDocs.length > 0) {
                analyzedDocs.sort((a, b) => new Date(b.upload_date) - new Date(a.upload_date));
                const latest = analyzedDocs[0];
                this.setActiveDocument(latest._id, latest.filename);

                document.getElementById('latest-doc-title').innerText = latest.filename;
                document.getElementById('latest-doc-summary').innerText = latest.summary || "Technical document processed.";
                document.getElementById('latest-terms-cnt').innerText = latest.stats?.terms_count || 0;
                document.getElementById('latest-rels-cnt').innerText = latest.stats?.relationships_count || 0;
            } else {
                // Auto-load sample data if database is empty so output is always visible
                this.loadSampleData();
            }

            this.renderRecentTable(docs);

        } catch (err) {
            console.error("Error loading dashboard data:", err);
        }
    },


    renderRecentTable(docs) {
        const tbody = document.getElementById('recent-docs-tbody');
        if (!tbody) return;

        if (docs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No documents analyzed yet. Upload a PDF, DOCX, or TXT file to begin.</td></tr>`;
            return;
        }

        tbody.innerHTML = docs.map(doc => `
            <tr>
                <td class="fw-bold text-white"><i class="fa-solid fa-file-code text-info me-2"></i>${doc.filename}</td>
                <td><span class="badge bg-primary bg-opacity-20 text-primary">${doc.stats?.terms_count || 0}</span></td>
                <td><span class="badge bg-warning bg-opacity-20 text-warning">${doc.stats?.concepts_count || 0}</span></td>
                <td><span class="badge bg-success bg-opacity-20 text-success">${doc.stats?.relationships_count || 0}</span></td>
                <td class="text-muted small">${doc.upload_date || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-glass text-info me-1" onclick="App.openDocGraph('${doc._id}', '${doc.filename}')" title="Open Graph">
                        <i class="fa-solid fa-circle-nodes"></i> Graph
                    </button>
                    <button class="btn btn-sm btn-glass text-danger" onclick="App.deleteDoc('${doc._id}')" title="Delete">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    },

    openDocGraph(docId, filename) {
        this.setActiveDocument(docId, filename);
        this.switchView('view-graph');
    },

    async deleteDoc(docId) {
        if (!confirm("Are you sure you want to delete this document and its generated graph?")) return;

        try {
            const res = await fetch(`/api/document/${docId}`, { method: 'DELETE' });
            const data = await res.json();
            this.showToast(data.message || 'Document deleted', 'success');
            if (this.currentDocId === docId) {
                this.setActiveDocument(null, 'No Document Selected');
            }
            this.loadDashboardData();
        } catch (err) {
            this.showToast('Failed to delete document', 'danger');
        }
    },

    async loadSampleData() {
        this.showToast('Loading pre-configured Viva sample dataset...', 'info');
        try {
            const res = await fetch('/api/sample', { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                this.showToast(data.message, 'success');
                this.setActiveDocument(data.document_id, 'ai_nlp_sample_demo.txt');
                this.switchView('view-graph');
            } else {
                this.showToast(data.error || 'Failed to load sample', 'danger');
            }
        } catch (err) {
            this.showToast('Error loading sample dataset', 'danger');
        }
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0 show mb-2`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 4000);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
