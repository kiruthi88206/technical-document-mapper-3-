/**
 * API Client Module
 * Provides unified REST communication for the Technical Document Mapper frontend.
 */
const API = {
    async request(url, options = {}) {
        try {
            const response = await fetch(url, options);
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error(`API Error [${url}]:`, error);
            throw error;
        }
    },

    async getStatus() {
        return this.request('/api/status');
    },

    async uploadFile(formData) {
        return this.request('/api/upload', {
            method: 'POST',
            body: formData
        });
    },

    async analyzeDocument(payload) {
        return this.request('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    },

    async getDocuments() {
        return this.request('/api/documents');
    },

    async getDocument(docId) {
        return this.request(`/api/documents/${docId}`);
    },

    async deleteDocument(docId) {
        return this.request(`/api/documents/${docId}`, {
            method: 'DELETE'
        });
    },

    async getGraph(docId) {
        return this.request(`/api/graph/${docId}`);
    },

    async getGlossary(docId) {
        return this.request(`/api/glossary/${docId}`);
    },

    async search(query, docId = null) {
        const url = docId 
            ? `/api/search?q=${encodeURIComponent(query)}&doc_id=${encodeURIComponent(docId)}`
            : `/api/search?q=${encodeURIComponent(query)}`;
        return this.request(url);
    },

    async addNode(docId, nodeData) {
        return this.request(`/api/graph/${docId}/node`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nodeData)
        });
    },

    async editNode(docId, nodeId, nodeData) {
        return this.request(`/api/graph/${docId}/node/${nodeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nodeData)
        });
    },

    async deleteNode(docId, nodeId) {
        return this.request(`/api/graph/${docId}/node/${nodeId}`, {
            method: 'DELETE'
        });
    },

    async addEdge(docId, edgeData) {
        return this.request(`/api/graph/${docId}/edge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(edgeData)
        });
    },

    async deleteEdge(docId, edgeId) {
        return this.request(`/api/graph/${docId}/edge/${edgeId}`, {
            method: 'DELETE'
        });
    },

    async resetGraph(docId) {
        return this.request(`/api/graph/${docId}/reset`, {
            method: 'POST'
        });
    },

    async loadSample(sampleId) {
        return this.request(`/api/sample/${sampleId}`, {
            method: 'POST'
        });
    }
};
