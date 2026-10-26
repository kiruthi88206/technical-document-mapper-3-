/* ==========================================================================
   TECHNICAL GLOSSARY MODULE
   ========================================================================== */

const GlossaryManager = {
    currentDocId: null,

    init() {
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('glossary-search-input')?.addEventListener('input', () => {
            if (this.currentDocId) this.loadGlossary(this.currentDocId);
        });

        document.getElementById('glossary-sort-select')?.addEventListener('change', () => {
            if (this.currentDocId) this.loadGlossary(this.currentDocId);
        });
    },

    async loadGlossary(docId) {
        this.currentDocId = docId;
        const searchVal = document.getElementById('glossary-search-input')?.value.trim() || '';
        const sortVal = document.getElementById('glossary-sort-select')?.value || 'alphabetical';

        try {
            const res = await fetch(`/api/glossary/${docId}?sort=${sortVal}&search=${encodeURIComponent(searchVal)}`);
            const data = await res.json();

            if (res.ok) {
                this.renderGlossaryGrid(data.glossary);
            } else {
                App.showToast(data.error || 'Failed to load glossary', 'danger');
            }
        } catch (err) {
            console.error("Error loading glossary:", err);
        }
    },

    renderGlossaryGrid(items) {
        const grid = document.getElementById('glossary-grid');
        if (!grid) return;

        if (!items || items.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center text-muted py-5">
                    <i class="fa-solid fa-book-open display-4 mb-3"></i>
                    <p class="m-0">No technical terms found in glossary for this document.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = items.map(item => `
            <div class="col-md-6 col-lg-4">
                <div class="glass-panel p-4 h-100 d-flex flex-direction-column justify-content-between">
                    <div>
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="text-white fw-bold m-0">${item.term}</h5>
                            <span class="badge badge-category badge-core">${item.category || 'Concept'}</span>
                        </div>
                        <p class="text-light small mb-3">${item.definition}</p>
                    </div>

                    <div>
                        <div class="d-flex justify-content-between align-items-center p-2 rounded bg-dark border border-secondary border-opacity-20 mb-3">
                            <span class="text-muted small">Frequency: <strong class="text-info">${item.frequency}</strong></span>
                            <span class="text-muted small">Relevance: <strong class="text-warning">${parseFloat(item.relevance_score).toFixed(2)}</strong></span>
                        </div>

                        ${item.related_concepts && item.related_concepts.length > 0 ? `
                            <div>
                                <span class="text-muted small fw-semibold">Related Concepts:</span>
                                <div class="d-flex flex-wrap gap-1 mt-1">
                                    ${item.related_concepts.map(rc => `
                                        <span class="badge bg-secondary bg-opacity-30 text-light me-1" style="cursor:pointer;" onclick="GlossaryManager.openInGraph('${rc}')">${rc}</span>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    },

    openInGraph(termName) {
        App.switchView('view-graph');
        setTimeout(() => {
            if (GraphManager) {
                GraphManager.focusOnNodeByName(termName);
            }
        }, 300);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    GlossaryManager.init();
});
