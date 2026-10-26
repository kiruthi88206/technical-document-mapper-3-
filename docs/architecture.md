# Technical Architecture: Document to Concept Knowledge Graph

## 1. System Pipeline Overview

```
[ Uploaded Document (PDF, DOCX, TXT, MD) ]
                    │
                    ▼
   [ 1. Ingestion & Section Segmentation ]
   - Validate extensions, magic bytes, size limits (< 25MB)
   - PyPDF page extraction & scanned PDF detection
   - python-docx style & heading hierarchy parsing
   - Markdown header (# / ##) & code block parsing
   - Segmentation into 300-500 word cohesive chunks
   - Offset and page index tracking
                    │
                    ▼
     [ 2. Linguistic Candidate Extraction ]
   - spaCy Part-of-Speech (POS) noun phrase chunking
   - Named Entity Recognition (ORG, PRODUCT, WORK_OF_ART)
   - Technical pattern regex (Acronyms, Hyphenated compounds)
   - Multi-word bigram and trigram phrase patterns
                    │
                    ▼
   [ 3. Statistical Ranking & Normalization ]
   - Lowercase canonical mapping (prevent duplicate "Deep Learning" / "deep learning")
   - TF-IDF sparse matrix computation across document sentences
   - Composite confidence score:
     Score = 0.40 * TF-IDF + 0.30 * Frequency + 0.30 * Specificity
                    │
                    ▼
     [ 4. Definition Extraction Engine ]
   - Explicit pattern matching:
     * "X is a type/kind/class of Y"
     * "X refers to / describes Y"
     * "X is defined as Y"
     * "X consists of / comprises Y"
   - Contextual explanatory sentence extraction when explicit pattern absent
   - Origin attribution: explicit_document vs contextual_inference
                    │
                    ▼
   [ 5. Concept Categorization & Mapping ]
   - Domain keyword taxonomies (Architecture, Model & Learning, Data, Algorithm, Metric, Component)
   - Concept entity creation in SQLite (SQLAlchemy 2.0 ORM)
                    │
                    ▼
   [ 6. Directed Relationship Extraction ]
   - Grammatical predicate bridge rules between concept pairs:
     * IS_A, PART_OF, USES, DEPENDS_ON, PRODUCES, IMPLEMENTS, ENABLES, CAUSES, COMPARED_WITH, RELATED_TO
   - Forward and backward sentence span matching (e.g. "X uses Y" vs "Y is used in X")
   - Verbatim sentence evidence preservation with page and section offsets
   - Minimum verification threshold filter
                    │
                    ▼
    [ 7. Graph Topology & Centrality Calculation ]
   - NetworkX directed graph model
   - Spring-force layout 2D coordinate calculation for comfortable viewing
   - Degree centrality calculation (hub identification)
                    │
                    ▼
     [ 8. Interactive Knowledge Graph UI ]
   - React Flow custom nodes with category colors, confidence pills, connection metrics
   - Directed arrow edges with relation type labels
   - Interactive node selection drawer
   - Clickable edge evidence modal displaying exact source citation
   - Filter by relationship type, category, and real-time concept search
```

---

## 2. Ingestion & Chunking Strategy

### PDF Extraction
- Utilizes `pypdf.PdfReader` to extract text page-by-page.
- Tracks page numbers and character offsets.
- **Scanned PDF Handling**: Detects pages where no selectable text layer is found. Emits clear warning indicators (`completed_with_warnings` status) rather than silently returning empty output.

### DOCX & Markdown Extraction
- Analyzes paragraph styles, bold headings, and markdown heading tokens (`#`, `##`, `###`).
- Clusters related paragraphs into cohesive chunks of ~350 words while preserving section titles.

---

## 3. Terminology & Normalization Engine

### Multi-Strategy Candidate Sourcing
1. **Linguistic Noun Chunks**: Leverages spaCy's dependency parser and POS tagger to identify valid noun phrases.
2. **Technical Acronyms & Hyphenated Compounds**: Regex matches for expressions like `TF-IDF`, `API-Gateway`, `Self-Attention`.
3. **Compound Computer Science N-Grams**: Multi-word domain sequences stripped of leading/trailing stopwords.

### Canonical Deduplication
- Capitalization differences (e.g., `Neural Network` vs `neural network`) are unified under a single normalized key.
- Canonical display case is determined by frequency and Title Case dominance.

---

## 4. Directed Relationship Extraction & Evidence Preservation

### Relationship Taxonomy
| Relation Type | Forward Linguistic Indicator | Meaning |
| :--- | :--- | :--- |
| **`IS_A`** | `is a type of`, `is a subclass of`, `is a` | Taxonomic specialization |
| **`PART_OF`** | `is part of`, `component of`, `consists of` | Compositional hierarchy |
| **`USES`** | `uses`, `utilizes`, `leverages`, `applies` | Functional dependency |
| **`DEPENDS_ON`** | `depends on`, `relies on`, `requires`, `needs` | Structural prerequisite |
| **`PRODUCES`** | `produces`, `generates`, `outputs`, `yields` | Generative outcome |
| **`IMPLEMENTS`**| `implements`, `realizes`, `constructs`, `instantiates` | Concrete realization |
| **`ENABLES`** | `enables`, `facilitates`, `allows`, `permits` | Capability empowerment |
| **`CAUSES`** | `causes`, `leads to`, `results in`, `triggers` | Direct causality |
| **`COMPARED_WITH`**| `compared with`, `differs from`, `similar to` | Comparative evaluation |
| **`RELATED_TO`** | Close semantic co-occurrence | General associative context |

### Directionality & Evidence
- When `"A Neural Network is used in Deep Learning"` is parsed:
  - Direction: `Neural Network` $\to$ `USES` $\to$ `Deep Learning`
- Every relationship stores:
  - Source Concept ID & Target Concept ID
  - Supporting verbatim sentence
  - Source page number & section header
  - Calibrated confidence score

---

## 5. Storage & Database Schema

The database uses **SQLAlchemy 2.0** ORM over SQLite locally, with standard ANSI SQL datatypes and constraints that allow seamless migration to PostgreSQL by setting the `DATABASE_URL` environment variable.

- `documents`: Document metadata, upload/processing timestamps, word/chunk counts, status, and warnings.
- `document_chunks`: Chunk index, section heading, page number, offsets, and chunk text.
- `terminologies`: Canonical term, definition, definition type, frequency, confidence, and source sentence.
- `concepts`: Unique concept node, category, description, definition, frequency, confidence, and centrality score.
- `relationships`: Directed edge between concepts with relation type, confidence, and supporting evidence sentence.
- `processing_jobs`: Lifecycle tracking for asynchronous and synchronous ingestion steps.
