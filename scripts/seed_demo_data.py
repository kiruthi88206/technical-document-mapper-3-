import os
import sys

# Add root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import create_app
from backend.app.database import init_db, db_session
from backend.app.models import Document
from backend.app.services.document_extractor import DocumentExtractor
from backend.app.processors.nlp_processor import DocumentNLPProcessor

def seed_sample_documents():
    app = create_app()
    with app.app_context():
        init_db()
        session = db_session()

        sample_files = [
            ("machine_learning_system.txt", "txt"),
            ("cloud_microservices.md", "md"),
            ("sample_cloud_architecture.docx", "docx"),
            ("sample_deep_learning_nlp.pdf", "pdf")
        ]

        sample_dir = os.path.join(root_dir, "sample_documents")

        print("=" * 60)
        print("SEEDING REPOSITORY WITH SAMPLE TECHNICAL DOCUMENTS")
        print("=" * 60)

        for filename, ext in sample_files:
            file_path = os.path.join(sample_dir, filename)
            if not os.path.exists(file_path):
                print(f"[SKIP] File {filename} not found.")
                continue

            # Check if document already seeded
            existing = session.query(Document).filter_by(original_filename=filename).first()
            if existing and existing.total_concepts > 0:
                print(f"[EXISTS] {filename} (Concepts: {existing.total_concepts}, Relations: {existing.total_relationships})")
                continue

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            print(f"\n[INGESTING] {filename} ({len(file_bytes)} bytes)...")
            is_valid, err_msg, detected_ext = DocumentExtractor.validate_upload(filename, file_bytes)
            if not is_valid:
                print(f" -> Validation error: {err_msg}")
                continue

            stored_filename, saved_path = DocumentExtractor.save_uploaded_file(filename, file_bytes)
            extracted_data = DocumentExtractor.extract_document(saved_path, detected_ext)

            import uuid
            from backend.app.models import DocumentChunk, ProcessingJob

            doc_id = str(uuid.uuid4())
            doc = Document(
                id=doc_id,
                original_filename=filename,
                stored_filename=stored_filename,
                file_type=detected_ext,
                file_size=len(file_bytes),
                storage_path=saved_path,
                status="uploaded",
                warning_message=extracted_data.get("warning_message", ""),
                total_chunks=len(extracted_data["chunks"]),
                word_count=extracted_data["word_count"],
                sentence_count=extracted_data["sentence_count"]
            )
            session.add(doc)

            for chk in extracted_data["chunks"]:
                chunk_obj = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    chunk_index=chk["chunk_index"],
                    section_heading=chk["section_heading"],
                    page_number=chk["page_number"],
                    start_offset=chk["start_offset"],
                    end_offset=chk["end_offset"],
                    text=chk["text"],
                    token_count=chk["token_count"]
                )
                session.add(chunk_obj)

            job = ProcessingJob(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                status="queued",
                progress_percent=0,
                current_stage="queued",
                stage_message="Queued for analysis"
            )
            session.add(job)
            session.commit()

            # Run NLP Processing
            print(f" -> Running NLP extraction pipeline for {filename}...")
            result = DocumentNLPProcessor.process_document(
                document_id=doc_id,
                job_id=job.id,
                max_terms=35,
                min_freq=1
            )
            print(f" -> COMPLETE: {result['total_concepts']} concepts, {result['total_relationships']} relationships.")

        print("\n" + "=" * 60)
        print("SEEDING FINISHED SUCCESSFULLY!")
        print("=" * 60)

if __name__ == "__main__":
    seed_sample_documents()
