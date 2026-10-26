"""
PDF Report Generation Service.
Generates an academic-grade, publication-ready PDF report using ReportLab
summarizing document metadata, extracted terminology, concept relationships, and glossary.
"""
import os
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config import Config


class PDFReportGenerator:
    """Generates structured PDF project reports for analyzed technical documents."""

    @classmethod
    def generate_report(
        cls,
        document_meta: Dict[str, Any],
        concepts: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        glossary: List[Dict[str, Any]],
        graph_metrics: Dict[str, Any],
        output_filename: str
    ) -> str:
        """Create PDF file in EXPORT_FOLDER and return its absolute filepath."""
        filepath = os.path.join(Config.EXPORT_FOLDER, output_filename)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Brand Styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            alignment=TA_LEFT
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#475569'),
            alignment=TA_LEFT
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=14,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.white
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )

        story = []

        # Header Title
        story.append(Paragraph("Technical Document Terminology & Concept Mapper", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Analysis Report for: <b>{document_meta.get('filename', 'Technical Document')}</b>", subtitle_style))
        story.append(Spacer(1, 6))
        
        # Meta badge line
        date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        story.append(Paragraph(f"<font color='#64748B'>Generated: {date_str} | College Final-Year Project Demonstration Report</font>", body_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F46E5'), spaceAfter=14))

        # 1. Summary Cards Table
        summary_data = [
            [
                Paragraph(f"<b>File Size</b><br/>{round(document_meta.get('file_size', 0)/1024, 1)} KB", table_cell_style),
                Paragraph(f"<b>Words</b><br/>{document_meta.get('word_count', 0)}", table_cell_style),
                Paragraph(f"<b>Sentences</b><br/>{document_meta.get('sentence_count', 0)}", table_cell_style),
                Paragraph(f"<b>Key Concepts</b><br/>{len(concepts)}", table_cell_style),
                Paragraph(f"<b>Relationships</b><br/>{len(relationships)}", table_cell_style),
                Paragraph(f"<b>Primary Hub</b><br/>{graph_metrics.get('primary_hub', 'N/A')}", table_cell_style)
            ]
        ]
        sum_table = Table(summary_data, colWidths=[90, 85, 90, 90, 95, 90])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 14))

        # 2. Extracted Technical Concepts Table (Top 12)
        story.append(Paragraph("1. Primary Extracted Technical Concepts", section_heading))
        concept_table_data = [
            [
                Paragraph("Rank", table_header_style),
                Paragraph("Concept / Term", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Frequency", table_header_style),
                Paragraph("TF-IDF Score", table_header_style),
                Paragraph("Graph Centrality", table_header_style)
            ]
        ]
        
        for c in concepts[:12]:
            concept_table_data.append([
                Paragraph(str(c.get("rank", 1)), table_cell_style),
                Paragraph(f"<b>{c.get('name', '')}</b>", table_cell_style),
                Paragraph(c.get("category", "Core Concepts"), table_cell_style),
                Paragraph(str(c.get("frequency", 1)), table_cell_style),
                Paragraph(str(c.get("tfidf_score", 0)), table_cell_style),
                Paragraph(str(c.get("centrality", 0.1)), table_cell_style)
            ])

        concept_table = Table(concept_table_data, colWidths=[38, 140, 140, 65, 75, 82])
        concept_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(concept_table)
        story.append(Spacer(1, 14))

        # 3. Concept Relationships Table (Top 12)
        story.append(Paragraph("2. Mapped Concept Relationships", section_heading))
        rel_table_data = [
            [
                Paragraph("Source Concept", table_header_style),
                Paragraph("Relationship", table_header_style),
                Paragraph("Target Concept", table_header_style),
                Paragraph("Methodology", table_header_style),
                Paragraph("Confidence", table_header_style)
            ]
        ]

        for r in relationships[:12]:
            conf_str = f"{int(r.get('confidence', 0.7) * 100)}%"
            rel_table_data.append([
                Paragraph(f"<b>{r.get('source_name', r.get('from', ''))}</b>", table_cell_style),
                Paragraph(f"<i>{r.get('relation_type', '').replace('_', ' ')}</i>", table_cell_style),
                Paragraph(f"<b>{r.get('target_name', r.get('to', ''))}</b>", table_cell_style),
                Paragraph(r.get("method", "Contextual NLP"), table_cell_style),
                Paragraph(conf_str, table_cell_style)
            ])

        rel_table = Table(rel_table_data, colWidths=[120, 110, 120, 120, 70])
        rel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(rel_table)
        story.append(Spacer(1, 14))

        # 4. Auto-Generated Glossary (First 6 terms)
        story.append(Paragraph("3. Auto-Generated Document Glossary", section_heading))
        glossary_table_data = [
            [
                Paragraph("Term", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Extracted Definition / Contextual Evidence", table_header_style),
                Paragraph("Source Type", table_header_style)
            ]
        ]

        for g in glossary[:8]:
            glossary_table_data.append([
                Paragraph(f"<b>{g.get('term', '')}</b>", table_cell_style),
                Paragraph(g.get("category", ""), table_cell_style),
                Paragraph(g.get("definition", "")[:180] + "...", table_cell_style),
                Paragraph(f"<font size='7' color='#4F46E5'>{g.get('origin', 'Context')}</font>", table_cell_style)
            ])

        glossary_table = Table(glossary_table_data, colWidths=[100, 100, 250, 90])
        glossary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(glossary_table)
        story.append(Spacer(1, 14))

        # Footer note
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        story.append(Paragraph(
            "<font size='7.5' color='#64748B'>Report created by Technical Document Terminology and Concept Relationship Mapper. "
            "Pipeline: Ingestion & Parsing -> NLP Entity/NP Chunking -> TF-IDF Scoring -> Relationship Detection -> NetworkX & Vis.js Knowledge Graph.</font>",
            body_style
        ))

        # Build PDF
        doc.build(story)
        return filepath
