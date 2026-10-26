import os
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from ..config import Config

class PDFReportService:
    """
    Generates downloadable analytical PDF reports of processed technical documents.
    """

    @classmethod
    def generate_report(
        cls,
        document_dict: Dict[str, Any],
        concepts: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        terminologies: List[Dict[str, Any]],
        output_filename: str = None
    ) -> str:
        if not output_filename:
            safe_name = document_dict.get("original_filename", "document").replace(" ", "_")
            output_filename = f"report_{document_dict.get('id', 'doc')[:8]}_{safe_name}.pdf"

        output_path = os.path.join(Config.EXPORT_FOLDER, output_filename)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'H2Style',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=14,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155")
        )
        evidence_style = ParagraphStyle(
            'Evidence',
            parent=styles['Normal'],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#475569")
        )

        story = []

        # Header Title
        story.append(Paragraph("Technical Document Terminology & Concept Analysis Report", title_style))
        story.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Document ID: {document_dict.get('id')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        # Document Overview Metadata Table
        story.append(Paragraph("1. Document Ingestion Overview", h2_style))
        meta_data = [
            ["Document Name:", document_dict.get("original_filename", "N/A"), "Status:", document_dict.get("status", "N/A").upper()],
            ["File Type:", str(document_dict.get("file_type", "N/A")).upper(), "File Size:", f"{document_dict.get('file_size', 0):,} bytes"],
            ["Word Count:", f"{document_dict.get('word_count', 0):,}", "Sentence Count:", f"{document_dict.get('sentence_count', 0):,}"],
            ["Concepts Identified:", str(len(concepts)), "Relationships:", str(len(relationships))]
        ]
        meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#475569")),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor("#475569")),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Warning Message if any
        if document_dict.get("warning_message"):
            warn_p = Paragraph(f"<b>Warning Notice:</b> {document_dict['warning_message']}", ParagraphStyle(
                'WarnP', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor("#b45309")
            ))
            story.append(warn_p)
            story.append(Spacer(1, 8))

        # Top Technical Terminology & Definitions
        story.append(Paragraph("2. Top Extracted Terminology & Definitions", h2_style))
        term_rows = [["Term", "Type", "Confidence", "Definition Preview"]]
        for t in terminologies[:15]:
            term_rows.append([
                Paragraph(f"<b>{t.get('term', '')}</b>", body_style),
                Paragraph(t.get('definition_type', '').replace('_', ' ').capitalize(), body_style),
                f"{t.get('confidence_score', 0):.2f}",
                Paragraph(t.get('definition', '')[:140] + ("..." if len(t.get('definition', '')) > 140 else ""), body_style)
            ])
        
        if len(term_rows) > 1:
            term_table = Table(term_rows, colWidths=[120, 80, 60, 280])
            term_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8.5),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(term_table)
        else:
            story.append(Paragraph("No terminology extracted.", body_style))

        story.append(Spacer(1, 12))

        # Extracted Concept Relationships
        story.append(Paragraph("3. Concept Relationships & Evidence", h2_style))
        rel_rows = [["Source Concept", "Relation", "Target Concept", "Conf.", "Supporting Sentence"]]
        for r in relationships[:18]:
            rel_rows.append([
                Paragraph(f"<b>{r.get('source_name', '')}</b>", body_style),
                Paragraph(f"<font color='#2563eb'><b>{r.get('relation_type', '')}</b></font>", body_style),
                Paragraph(f"<b>{r.get('target_name', '')}</b>", body_style),
                f"{r.get('confidence_score', 0):.2f}",
                Paragraph(r.get('supporting_sentence', '')[:120] + ("..." if len(r.get('supporting_sentence', '')) > 120 else ""), evidence_style)
            ])

        if len(rel_rows) > 1:
            rel_table = Table(rel_rows, colWidths=[110, 80, 110, 45, 195])
            rel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8.5),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(rel_table)
        else:
            story.append(Paragraph("No relationships detected.", body_style))

        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        story.append(Paragraph("Technical Document Mapper - End-to-End Extraction & Graph Architecture Report", subtitle_style))

        doc.build(story)
        return output_path
