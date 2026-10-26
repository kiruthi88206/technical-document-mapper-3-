import io
import csv
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from ..database.graph_store import graph_store
from ..services.report_generator import ReportGenerator

router = APIRouter(tags=["Export"])

@router.get("/export/{document_id}")
async def export_analysis_data(document_id: str, format: str = Query("json", pattern="^(json|csv)$")):
    """
    Export knowledge graph data or terminology glossary as JSON or CSV.
    """
    graph_data = graph_store.get_graph(document_id)
    if not graph_data:
        raise HTTPException(status_code=404, detail="Document graph not found for export.")

    if format == "json":
        json_str = json.dumps(graph_data, indent=2)
        filename = f"knowledge_graph_{document_id}.json"
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    elif format == "csv":
        # Export Glossary as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Term", "Category", "Frequency", "TF-IDF Score", "Importance Score", "Context Definition"])
        
        for n in graph_data.get("nodes", []):
            writer.writerow([
                n["id"],
                n["label"],
                n["category"],
                n.get("frequency", 1),
                n.get("tfidf_score", 0.0),
                n.get("importance_score", 0.0),
                n.get("definition", "").replace("\n", " ")
            ])

        csv_str = output.getvalue()
        filename = f"glossary_{document_id}.csv"
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

@router.get("/export/pdf/{document_id}")
async def export_pdf_report(document_id: str):
    """Generate and download a professional PDF summary report."""
    graph_data = graph_store.get_graph(document_id)
    if not graph_data:
        raise HTTPException(status_code=404, detail="Document graph not found for PDF generation.")

    try:
        pdf_buffer = ReportGenerator.generate_pdf_report(graph_data)
        filename = f"Knowledge_Report_{document_id}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render PDF: {str(e)}")
