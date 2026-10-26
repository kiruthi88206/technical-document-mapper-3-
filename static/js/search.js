/* ==========================================================================
   QUESTION / CONCEPT SEARCH MODULE
   ========================================================================== */

const SearchManager = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('btn-execute-search')?.addEventListener('click', () => {
            this.executeSearch();
        });

        document.getElementById('search-query-input')?.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') this.executeSearch();
        });

        document.querySelectorAll('.sample-query-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const queryText = e.target.innerText;
                document.getElementById('search-query-input').value = queryText;
                this.executeSearch();
            });
        });
    },

    async executeSearch() {
        const queryInput = document.getElementById('search-query-input');
        const query = queryInput ? queryInput.value.trim() : '';

        if (!query) {
            App.showToast('Please type a question or concept to search.', 'warning');
            return;
        }

        const container = document.getElementById('search-results-container');
        container.innerHTML = `<div class="text-center text-muted py-4"><i class="fa-solid fa-spinner fa-spin fs-3 me-2"></i>Searching MongoDB knowledge base...</div>`;

        try {
            const docIdParam = App.currentDocId ? `&doc_id=${App.currentDocId}` : '';
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}${docIdParam}`);
            const data = await res.json();

            if (res.ok) {
                this.renderResults(data.results, query);
            } else {
                container.innerHTML = `
                    <div class="glass-panel p-4 text-center text-muted">
                        <i class="fa-solid fa-triangle-exclamation text-warning display-4 mb-3"></i>
                        <p class="m-0">${data.error || 'No matching concept found.'}</p>
                    </div>
                `;
            }
        } catch (err) {
            container.innerHTML = `<div class="glass-panel p-4 text-center text-danger">Server error executing search query.</div>`;
        }
    },

    renderResults(results, query) {
        const container = document.getElementById('search-results-container');
        if (!container) return;

        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="glass-panel p-5 text-center">
                    <i class="fa-solid fa-circle-question text-muted display-4 mb-3"></i>
                    <h5 class="text-white fw-bold">No Matching Concepts Found</h5>
                    <p class="text-muted m-0">Try searching for concepts like "NLP", "Machine Learning", or "Knowledge Graph".</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="text-white m-0">Search Results for "<span class="text-info">${query}</span>"</h5>
                <span class="badge bg-secondary">${results.length} Matches Found</span>
            </div>
            ${results.map(r => `
                <div class="glass-panel p-4 mb-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <h4 class="text-white fw-bold m-0">${r.name}</h4>
                            <span class="badge bg-info bg-opacity-20 text-info mt-1">${r.category}</span>
                        </div>
                        <button class="btn btn-primary-custom btn-sm" onclick="SearchManager.focusInGraph('${r.name}')">
                            <i class="fa-solid fa-circle-nodes me-1"></i> View in Graph
                        </button>
                    </div>

                    <p class="text-light mb-3">${r.definition}</p>

                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <div class="d-flex gap-3 text-muted small">
                                <span>Frequency: <strong class="text-info">${r.frequency}</strong></span>
                                <span>Relevance Score: <strong class="text-warning">${parseFloat(r.relevance_score).toFixed(2)}</strong></span>
                            </div>
                        </div>
                        <div class="col-md-6 text-end">
                            ${r.related_concepts && r.related_concepts.length > 0 ? `
                                <div class="d-flex flex-wrap gap-1 justify-content-end align-items-center">
                                    <span class="text-muted small me-2">Related:</span>
                                    ${r.related_concepts.map(rc => `<span class="badge bg-secondary bg-opacity-30 text-light">${rc}</span>`).join('')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('')}
        `;
    },

    focusInGraph(termName) {
        App.switchView('view-graph');
        setTimeout(() => {
            if (GraphManager) {
                GraphManager.focusOnNodeByName(termName);
            }
        }, 300);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    SearchManager.init();
});
