# Technical Document Terminology and Concept Relationship Mapper

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![React Flow](https://img.shields.io/badge/React%20Flow-12.0+-purple.svg)](https://reactflow.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38bdf8.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An intelligent, full-stack natural language processing (NLP) application that ingests complex technical documents (PDF, DOCX, TXT, Markdown), extracts domain-specific terminology, uncovers explicit definitions, identifies directed relationships between concepts, and visualizes an **interactive knowledge graph powered by React Flow**.

---

## 1. Problem Statement & Objectives

Dense technical documentation—such as research papers, software architecture specifications, system manuals, and academic textbooks—contains rich domain terminology and implicit conceptual dependencies. Students, engineers, and researchers often face steep learning curves, slow onboarding, and manual cross-referencing.

The **Technical Document Terminology and Concept Relationship Mapper** addresses this challenge by transforming dense, unstructured technical documents into an **interactive Knowledge Graph**, paired with an **evidence-backed domain glossary** and **exportable analytical reports**.

### Key Objectives
1. **Multi-Format Document Processing**: Seamlessly ingest `.pdf`, `.docx`, `.txt`, and `.md` documents, preserving page numbers, section headers, and character offsets.
2. **Terminology Extraction**: Extract technical candidate terms using linguistic noun chunks (spaCy), technical pattern recognition (acronyms, hyphenated terms), and statistical TF-IDF ranking.
3. **Explicit Definition Extraction**: Detect explicit definitions (`"X is a..."`, `"X refers to..."`, `"X is defined as..."`) and contextual explanations without fabricating quotes.
4. **Directed Concept Relationship Mapping**: Identify evidence-backed relationships (`IS_A`, `PART_OF`, `USES`, `DEPENDS_ON`, `PRODUCES`, `IMPLEMENTS`, `ENABLES`, `CAUSES`, `COMPARED_WITH`) backed by actual document sentences.
5. **Interactive React Flow Graph**: Explore concepts via an accessible, force-directed graph canvas supporting drag-and-drop, zoom/pan, minimap, category and relationship filters, node details drawer, and edge evidence inspection.
6. **Unified Search & Export**: Real-time cross-entity search and export to CSV, JSON, and ReportLab-compiled executive PDF reports.

---

## 2. Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19, TypeScript, Vite | High-performance Single Page Application (SPA) |
| **Routing** | React Router DOM v7 | Seamless client-side routing across views |
| **Graph Visualization** | React Flow (`@xyflow/react`) | Interactive concept knowledge graph with custom nodes, edge labels, and minimap |
| **Analytics & Charts** | Recharts | Distribution charts for concept categories and relationship types |
| **Styling & Icons** | Tailwind CSS v4, Lucide React | Modern dark-themed responsive SaaS interface |
| **API Client** | Axios | RESTful communication with backend |
| **Backend Framework** | Python 3.12, Flask, Flask-CORS | REST API service layer |
| **Database & ORM** | SQLite, SQLAlchemy 2.0 | Relational database with portable models (migratable to PostgreSQL) |
| **Data Validation** | Pydantic v2 | Request/response schema validation |
| **Document Parsing** | PyPDF, python-docx, io | Binary parsing, section extraction, and scanned PDF detection |
| **NLP & Ranking** | spaCy, Scikit-learn (TF-IDF), NetworkX | Linguistic analysis, statistical ranking, degree centrality |
| **Reporting & Export** | ReportLab, Python CSV/JSON | PDF analytical reports, JSON topology, CSV glossaries |

---

## 3. Project Structure

```
technical-document-mapper/
├── backend/
│   ├── app/
│   │   ├── __init__.py             # Flask app factory, CORS, error handlers, SPA mount
│   │   ├── config.py               # Configuration & environment variables
│   │   ├── database.py             # SQLAlchemy scoped session & table initialization
│   │   ├── models/                 # SQLAlchemy 2.0 ORM models
│   │   │   ├── document.py         # Document entity & metadata
│   │   │   ├── chunk.py            # DocumentChunk with page & offset tracking
│   │   │   ├── terminology.py      # Terminology with explicit/contextual definitions
│   │   │   ├── concept.py          # Concept graph node entity with category & centrality
│   │   │   ├── relationship.py     # Directed relationship edge with evidence sentence
│   │   │   └── processing_job.py   # Job progress tracker
│   │   ├── schemas/                # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── document_extractor.py # PDF, DOCX, TXT, MD parser with chunking
│   │   │   └── pdf_report_service.py # ReportLab executive PDF generator
│   │   ├── processors/
│   │   │   ├── terminology_extractor.py # Linguistic noun chunks & TF-IDF ranker
│   │   │   ├── definition_extractor.py  # Explicit pattern & contextual definition matcher
│   │   │   ├── relationship_extractor.py# Grammatical predicate & directed relation engine
│   │   │   └── nlp_processor.py         # End-to-end pipeline orchestrator
│   │   └── routes/                 # REST API Blueprints
│   │       ├── document_routes.py  # /api/documents (upload, list, detail, delete, process, status)
│   │       ├── terminology_routes.py # /api/terminology (list, detail, related concepts)
│   │       ├── concept_routes.py   # /api/concepts (list, detail, relationships)
│   │       ├── graph_routes.py     # /api/documents/<id>/graph (React Flow topology)
│   │       ├── search_routes.py    # /api/search (cross-entity search)
│   │       ├── export_routes.py    # /api/documents/<id>/export (CSV, JSON, PDF)
│   │       └── dashboard_routes.py # /api/dashboard/stats (real metrics & charts)
│   ├── requirements.txt            # Python dependencies
│   └── run.py                      # Standalone backend server runner
├── frontend/
│   ├── package.json
│   ├── vite.config.js              # Vite config with /api proxy to Flask port 5000
│   ├── src/
│   │   ├── App.jsx                 # Central router & layout orchestrator
│   │   ├── index.css               # Tailwind CSS styles
│   │   ├── services/
│   │   │   └── api.js              # Axios REST client
│   │   ├── components/
│   │   │   ├── Sidebar.jsx         # Navigation sidebar (Dashboard, Docs, Terminology, Graph, Search, Settings)
│   │   │   ├── Navbar.jsx          # Header with quick search & upload shortcut
│   │   │   ├── GraphViewer.jsx     # React Flow canvas, minimap, controls, legend
│   │   │   ├── ConceptNode.jsx     # Custom React Flow concept node
│   │   │   ├── NodeDetailsPanel.jsx# Concept details drawer with incoming/outgoing connections
│   │   │   └── EdgeEvidenceModal.jsx # Verbatim supporting sentence modal
│   │   └── pages/
│   │       ├── DashboardPage.jsx   # Metrics cards, Recharts charts, recent docs
│   │       ├── DocumentsPage.jsx   # Drag-and-drop upload & document repository
│   │       ├── DocumentDetailPage.jsx # Chunks preview, terminology table, graph links
│   │       ├── TerminologyPage.jsx # Terminology explorer with filters & detail modal
│   │       ├── ConceptMapperPage.jsx # Dedicated interactive React Flow knowledge graph
│   │       ├── SearchPage.jsx      # Cross-entity unified search
│   │       └── SettingsPage.jsx    # System status & pipeline parameter tuning
├── sample_documents/               # Sample test documents (PDF, DOCX, TXT, MD)
│   ├── machine_learning_system.txt
│   ├── cloud_microservices.md
│   ├── sample_cloud_architecture.docx
│   └── sample_deep_learning_nlp.pdf
├── docs/
│   └── architecture.md             # Detailed technical architecture document
├── tests/
│   └── test_backend.py             # Automated pytest suite (10 comprehensive tests)
├── scripts/
│   └── seed_demo_data.py           # Ingests and processes sample documents into SQLite
├── run.py                          # Unified server runner (Flask + React SPA)
├── run.ps1                         # PowerShell one-click launcher
├── run.bat                         # Windows Batch one-click launcher
├── .env.example                    # Environment configuration template
├── .gitignore
└── README.md                       # Complete documentation
```

---

## 4. Installation & Setup Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **Node.js 18+** and **npm**

### Step 1: Clone and Set Up Backend
```bash
# Navigate to project directory
cd technical-document-mapper

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 5. Running the Application

### Option A: Unified Server (Recommended)
Because the Flask application serves the compiled React Single Page Application directly from `frontend/dist/`, you can run the entire system with a single command:

```powershell
# Windows PowerShell
$env:PYTHONPATH="."
python run.py
```
Or simply double-click **`run.bat`** or execute **`./run.ps1`**.

Open your browser to:
**`http://127.0.0.1:5000`**

### Option B: Separate Frontend & Backend Development Mode
If you wish to modify React components with Vite Hot Module Reloading (HMR):

1. **Terminal 1 (Backend API)**:
   ```bash
   python backend/run.py
   # Runs on http://127.0.0.1:5000
   ```

2. **Terminal 2 (Frontend Dev Server)**:
   ```bash
   cd frontend
   npm run dev
   # Runs on http://localhost:5173 (proxies /api to port 5000)
   ```

---

## 6. Running Automated Tests

A comprehensive automated test suite is provided in `tests/test_backend.py`.

To run the test suite:
```bash
$env:PYTHONPATH="."
python -m pytest tests/test_backend.py -v
```

### Verified Test Coverage
- **TXT Ingestion**: `test_txt_extraction` (Verifies sentence splitting and word count)
- **Markdown Ingestion**: `test_markdown_extraction` (Verifies section header parsing)
- **DOCX Ingestion**: `test_docx_extraction` (Verifies paragraph hierarchy and headings)
- **PDF Ingestion**: `test_pdf_extraction` (Verifies page number tracking and offsets)
- **Validation**: `test_empty_document_rejection` (Rejects 0-byte uploads)
- **Validation**: `test_invalid_file_type_rejection` (Rejects unsupported extensions)
- **NLP Normalization**: `test_terminology_extraction_and_deduplication` (Prevents duplicate casing)
- **Definition Engine**: `test_explicit_definition_extraction` (Verifies explicit patterns)
- **Relationship Engine**: `test_relationship_extraction_and_direction` (Verifies directed links and evidence)
- **End-to-End API**: `test_upload_and_process_pipeline` (Upload, process, graph, search, CSV, JSON, PDF export)

---

## 7. Sample Input & Expected Output

### Sample Input (`machine_learning_system.txt`)
```text
Artificial Intelligence is a broad branch of computer science focused on building smart machines.
Machine Learning is a field within Artificial Intelligence that empowers computers to learn.
Deep Learning is a type of Machine Learning based on artificial neural networks.
A Neural Network is used in Deep Learning to approximate complex non-linear functions.
Model Training uses a Training Dataset to optimize internal weight parameters.
Classification is a supervised learning task where models predict categorical class labels.
```

### Extracted Concepts & Categories
- **`Deep Learning`** (Model & Learning, Conf: 95%)
- **`Machine Learning`** (Model & Learning, Conf: 92%)
- **`Neural Network`** (Model & Learning, Conf: 88%)
- **`Artificial Intelligence`** (Architecture, Conf: 90%)
- **`Training Dataset`** (Data & Storage, Conf: 85%)
- **`Classification`** (Algorithm & Logic, Conf: 82%)

### Extracted Relationships & Evidence
| Source Concept | Relation Type | Target Concept | Confidence | Verbatim Supporting Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **`Deep Learning`** | `IS_A` | **`Machine Learning`** | 95% | *"Deep Learning is a type of Machine Learning based on artificial neural networks."* |
| **`Machine Learning`**| `IS_A` | **`Artificial Intelligence`**| 88% | *"Machine Learning is a field within Artificial Intelligence that empowers computers to learn."*|
| **`Neural Network`** | `USES` | **`Deep Learning`** | 85% | *"A Neural Network is used in Deep Learning to approximate complex non-linear functions."* |
| **`Model Training`** | `USES` | **`Training Dataset`** | 85% | *"Model Training uses a Training Dataset to optimize internal weight parameters."* |
| **`Classification`** | `IS_A` | **`Supervised Learning`** | 88% | *"Classification is a supervised learning task where models predict categorical class labels."* |

---

## 8. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **`GET`** | `/api/health` | Service health status and database engine info |
| **`GET`** | `/api/dashboard/stats` | Aggregated database metrics and chart distributions |
| **`POST`** | `/api/documents/upload` | Multipart file upload (PDF, DOCX, TXT, MD) |
| **`GET`** | `/api/documents` | List uploaded documents with counts and statuses |
| **`GET`** | `/api/documents/<id>` | Document detail with chunk preview |
| **`DELETE`**| `/api/documents/<id>` | Cascading delete of document and all associated data |
| **`POST`** | `/api/documents/<id>/process` | Trigger NLP pipeline (terminology, definitions, relationships) |
| **`GET`** | `/api/documents/<id>/status` | Processing job status and progress percentage |
| **`GET`** | `/api/terminology` | Filterable, paginated terminology list |
| **`GET`** | `/api/terminology/<id>` | Term detail with connected relationships |
| **`GET`** | `/api/concepts` | List concept graph nodes with category filter |
| **`GET`** | `/api/concepts/<id>/relationships` | Incoming and outgoing relationships with evidence |
| **`GET`** | `/api/documents/<id>/graph` | React Flow node-edge graph topology with layout coordinates |
| **`GET`** | `/api/search?q=<query>` | Unified search across documents, terms, definitions, and relationships |
| **`GET`** | `/api/documents/<id>/export/terminology` | Export terminology as CSV or JSON |
| **`GET`** | `/api/documents/<id>/export/relationships` | Export relationships as CSV or JSON |
| **`GET`** | `/api/documents/<id>/export/graph` | Export complete knowledge graph topology as JSON |
| **`GET`** | `/api/documents/<id>/export/report` | Download compiled ReportLab PDF analysis report |

---

## 9. Known Limitations & Future Enhancements

### Known Limitations
- **Scanned PDFs**: Does not perform Optical Character Recognition (OCR) on purely image-based PDFs; scanned pages without text layers are detected and surfaced with warning notices (`completed_with_warnings`).
- **Graph Scalability**: Rendering very large graphs (> 300 nodes) on low-powered mobile devices may cause minor canvas slowdowns; filtering by category or relationship type is recommended.
- **Multilingual Support**: Primary extraction heuristics and spaCy models are configured for English technical documentation.

### Future Enhancements
- Tesseract OCR sidecar integration for scanned PDF page digitizing.
- Optional LLM integration (OpenAI/Anthropic/Ollama) for abstractive summarization.
- Graph export to Neo4j Cypher scripts and GraphML formats.
- Cross-document concept union mapping to visualize knowledge across entire technical libraries.

---

## 10. Production Deployment

The project can be deployed using Docker, Linux VPS (Nginx + Gunicorn), or Cloud PaaS (Render, Railway, Fly.io).

For complete, step-by-step instructions, see:
📖 **[`docs/deployment_guide.md`](file:///C:/Users/HP/.gemini/antigravity/scratch/technical-document-mapper/docs/deployment_guide.md)**

### Quick Docker Deployment:
```bash
docker compose up -d --build
```
Access at: `http://<SERVER_IP>:5000`

---

## 11. License

This project is licensed under the MIT License - see the LICENSE file for details.

