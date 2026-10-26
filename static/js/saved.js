/* ==========================================================================
   SAVED DOCUMENTS MANAGER MODULE
   ========================================================================== */

const SavedDocsManager = {
    async loadSavedDocs() {
        try {
            const res = await fetch('/api/documents');
            const docs = await res.json();
            this.renderTable(docs);
        } catch (err) {
            console.error("Error loading saved documents:", err);
        }
    },

    renderTable(docs) {
        const tbody = document.getElementById('saved-docs-tbody');
        if (!tbody) return;

        if (!docs || docs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        <i class="fa-solid fa-folder-open display-4 mb-2"></i>
                        <p class="m-0">No documents saved in MongoDB database.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = docs.map(doc => `
            <tr>
                <td class="fw-bold text-white"><i class="fa-solid fa-file-lines text-info me-2"></i>${doc.filename}</td>
                <td><span class="badge bg-secondary text-uppercase">${doc.file_type}</span></td>
                <td class="text-muted small">${(doc.file_size / 1024).toFixed(1)} KB</td>
                <td class="text-muted small">${doc.upload_date}</td>
                <td>
                    <span class="badge ${doc.status === 'analyzed' ? 'bg-success' : 'bg-warning'} bg-opacity-20 ${doc.status === 'analyzed' ? 'text-success' : 'text-warning'}">
                        ${doc.status}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary-custom me-1" onclick="SavedDocsManager.openGraph('${doc._id}', '${doc.filename}')">
                        <i class="fa-solid fa-circle-nodes me-1"></i> Open Graph
                    </button>
                    <button class="btn btn-sm btn-glass text-danger" onclick="SavedDocsManager.deleteDoc('${doc._id}')">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    },

    openGraph(docId, filename) {
        App.setActiveDocument(docId, filename);
        App.switchView('view-graph');
    },

    async deleteDoc(docId) {
        if (!confirm('Are you sure you want to delete this document and all extracted graph data?')) return;

        try {
            const res = await fetch(`/api/document/${docId}`, { method: 'DELETE' });
            const data = await res.json();
            App.showToast(data.message || 'Document deleted', 'success');
            this.loadSavedDocs();
            App.loadDashboardData();
        } catch (err) {
            App.showToast('Failed to delete document', 'danger');
        }
    }
};
