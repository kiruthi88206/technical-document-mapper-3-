import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from config import Config
from models.document_model import DocumentModel
from models.concept_model import ConceptModel
from models.relationship_model import RelationshipModel
from database.mongodb import db_manager
from services.document_processor import DocumentProcessor
from services.nlp_processor import NLPProcessor
from services.terminology_extractor import TerminologyExtractor
from services.relationship_mapper import RelationshipMapper
from services.glossary_generator import GlossaryGenerator

document_bp = Blueprint('document_bp', __name__)
nlp_processor = NLPProcessor()
term_extractor = TerminologyExtractor()
rel_mapper = RelationshipMapper()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@document_bp.route('/api/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file format. Please upload PDF, DOCX, or TXT.'}), 400

    try:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Quick check: extract snippet
        text_snippet = DocumentProcessor.extract_text(file_path, ext)[:300]

        # Save metadata to DB
        doc_data = DocumentModel.create(
            filename=filename,
            file_path=file_path,
            file_type=ext,
            file_size=file_size,
            summary=text_snippet
        )

        return jsonify({
            'message': 'Document uploaded successfully. Ready for analysis.',
            'document': doc_data
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to upload document: {str(e)}'}), 500


@document_bp.route('/api/analyze/<doc_id>', methods=['POST'])
def analyze_document(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    try:
        file_path = doc['file_path']
        file_type = doc['file_type']

        # 1. Text Extraction
        text = DocumentProcessor.extract_text(file_path, file_type)
        
        # 2. NLP Preprocessing
        nlp_result = nlp_processor.process_text(text)
        
        # 3. Terminology Identification
        concepts_list = term_extractor.extract_terms(text, nlp_result, max_terms=25)
        
        # Attach doc_id
        for c in concepts_list:
            c['document_id'] = doc_id
            
        # 4. Save Concepts to DB
        # First clear old if re-analyzing
        db_manager.get_collection('concepts').delete_many({'document_id': doc_id})
        saved_concepts = ConceptModel.create_many(concepts_list)
        
        # 5. Calculate Semantic & Co-occurrence Relationships
        relationships_list = rel_mapper.discover_relationships(
            saved_concepts, 
            nlp_result['sentences'], 
            text
        )
        for r in relationships_list:
            r['document_id'] = doc_id
            
        db_manager.get_collection('relationships').delete_many({'document_id': doc_id})
        saved_rels = RelationshipModel.create_many(relationships_list)
        
        # 6. Technical Glossary Generation
        glossary_items = GlossaryGenerator.generate_glossary(saved_concepts, saved_rels)
        db_manager.get_collection('glossary').delete_many({'document_id': doc_id})
        coll_g = db_manager.get_collection('glossary')
        for item in glossary_items:
            item['_id'] = str(uuid.uuid4())
            coll_g.insert_one(item)

        # 7. Update Document Status & Stats
        stats = {
            'terms_count': len(saved_concepts),
            'concepts_count': len(saved_concepts),
            'relationships_count': len(saved_rels)
        }
        summary_excerpt = text[:280] + "..." if len(text) > 280 else text
        DocumentModel.update_status(doc_id, 'analyzed', stats, summary_excerpt)

        return jsonify({
            'message': 'Document analysis completed successfully!',
            'document_id': doc_id,
            'stats': stats,
            'steps_completed': [
                'Step 1 - Extracting text ✓',
                'Step 2 - Preprocessing ✓',
                'Step 3 - Identifying terminology ✓',
                'Step 4 - Finding concepts ✓',
                'Step 5 - Calculating semantic relationships ✓',
                'Step 6 - Generating knowledge graph ✓',
                'Step 7 - Saving results ✓'
            ]
        }), 200

    except Exception as e:
        DocumentModel.update_status(doc_id, 'error')
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500


@document_bp.route('/api/documents', methods=['GET'])
def get_all_documents():
    docs = list(DocumentModel.get_all())
    return jsonify(docs), 200


@document_bp.route('/api/document/<doc_id>', methods=['GET'])
def get_document(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    return jsonify(doc), 200


@document_bp.route('/api/document/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    # Remove file from disk
    if os.path.exists(doc.get('file_path', '')):
        try:
            os.remove(doc['file_path'])
        except Exception:
            pass

    DocumentModel.delete(doc_id)
    return jsonify({'message': 'Document and all associated data deleted successfully.'}), 200


@document_bp.route('/api/sample', methods=['POST'])
def load_sample_dataset():
    """Load pre-configured sample technical document for instant Viva demo."""
    sample_text = """
    # Technical Survey: Artificial Intelligence, NLP, and Knowledge Graphs
    
    Natural Language Processing (NLP) is a core subfield of Artificial Intelligence and Computer Science that enables computers to understand, interpret, and generate human language. Modern NLP pipelines combine statistical Machine Learning models with Deep Learning architectures.
    
    Machine Learning algorithms learn feature representations from large datasets. Deep Learning models, such as Neural Networks, utilize multiple processing layers to extract high-level representations from unstructured text.
    
    Word Embedding techniques transform raw text tokens into dense continuous vector spaces where semantic similarity can be measured via cosine distance. Advanced architectures like the Transformer rely on self-attention mechanisms to model long-range context dependencies.
    
    A Knowledge Graph represents domain knowledge using entity nodes and relationship edges. Integrating Knowledge Graphs with Semantic Similarity calculations enables efficient Question Answering, Tokenization, TF-IDF ranking, and contextual concept retrieval.
    """
    
    # Save as sample text file
    sample_filename = "ai_nlp_sample_demo.txt"
    sample_path = os.path.join(Config.UPLOAD_FOLDER, sample_filename)
    with open(sample_path, 'w', encoding='utf-8') as f:
        f.write(sample_text)
        
    doc_data = DocumentModel.create(
        filename=sample_filename,
        file_path=sample_path,
        file_type='txt',
        file_size=len(sample_text),
        summary="Sample AI, NLP & Knowledge Graph Demonstration Document"
    )
    
    # Analyze sample document directly
    doc_id = doc_data['_id']
    analyze_document(doc_id)
    
    return jsonify({
        'message': 'Sample technical dataset loaded and analyzed successfully!',
        'document_id': doc_id
    }), 200
