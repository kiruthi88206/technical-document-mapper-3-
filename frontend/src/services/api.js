import axios from 'axios';

const API_BASE = '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('techmapper_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Authentication
  login: async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },

  register: async (email, name, password) => {
    const res = await apiClient.post('/auth/register', { email, name, password });
    return res.data;
  },

  getCurrentUser: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Dashboard
  getDashboardStats: async () => {
    const res = await apiClient.get('/dashboard/stats');
    return res.data;
  },

  // Documents
  uploadDocument: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return res.data;
  },

  getDocuments: async (page = 1, limit = 50) => {
    const res = await apiClient.get(`/documents?page=${page}&limit=${limit}`);
    return res.data;
  },

  getDocument: async (documentId) => {
    const res = await apiClient.get(`/documents/${documentId}`);
    return res.data;
  },

  deleteDocument: async (documentId) => {
    const res = await apiClient.delete(`/documents/${documentId}`);
    return res.data;
  },

  processDocument: async (documentId, options = {}) => {
    const res = await apiClient.post(`/documents/${documentId}/process`, {
      max_terms: options.maxTerms || 35,
      min_term_freq: options.minFreq || 1,
    });
    return res.data;
  },

  getDocumentStatus: async (documentId) => {
    const res = await apiClient.get(`/documents/${documentId}/status`);
    return res.data;
  },

  // Terminology
  getTerminology: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.documentId) query.append('document_id', params.documentId);
    if (params.search) query.append('search', params.search);
    if (params.minConfidence) query.append('min_confidence', params.minConfidence);
    if (params.definitionType) query.append('definition_type', params.definitionType);
    if (params.sortBy) query.append('sort_by', params.sortBy);
    if (params.order) query.append('order', params.order);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);

    const res = await apiClient.get(`/terminology?${query.toString()}`);
    return res.data;
  },

  getTermDetail: async (termId) => {
    const res = await apiClient.get(`/terminology/${termId}`);
    return res.data;
  },

  // Concepts
  getConcepts: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.documentId) query.append('document_id', params.documentId);
    if (params.category) query.append('category', params.category);
    if (params.search) query.append('search', params.search);
    const res = await apiClient.get(`/concepts?${query.toString()}`);
    return res.data;
  },

  getConceptDetail: async (conceptId) => {
    const res = await apiClient.get(`/concepts/${conceptId}`);
    return res.data;
  },

  getConceptRelationships: async (conceptId) => {
    const res = await apiClient.get(`/concepts/${conceptId}/relationships`);
    return res.data;
  },

  // Graph
  getDocumentGraph: async (documentId) => {
    const res = await apiClient.get(`/documents/${documentId}/graph`);
    return res.data;
  },

  // Global Search
  searchAll: async (query) => {
    const res = await apiClient.get(`/search?q=${encodeURIComponent(query)}`);
    return res.data;
  },

  // Export URLs
  getExportTerminologyUrl: (documentId, format = 'csv') => {
    return `${API_BASE}/documents/${documentId}/export/terminology?format=${format}`;
  },

  getExportRelationshipsUrl: (documentId, format = 'csv') => {
    return `${API_BASE}/documents/${documentId}/export/relationships?format=${format}`;
  },

  getExportGraphUrl: (documentId) => {
    return `${API_BASE}/documents/${documentId}/export/graph`;
  },

  getExportReportUrl: (documentId) => {
    return `${API_BASE}/documents/${documentId}/export/report`;
  },
};

export default api;
