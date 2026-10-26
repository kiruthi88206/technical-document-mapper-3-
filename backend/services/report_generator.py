import io
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ReportGenerator:
    """Generates a professional PDF report containing document metrics, key terminology, and concept relationships."""

    @classmethod
    def generate_pdf_report(cls, graph_data: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom palette matching Dark Navy / Indigo theme
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#1e1b4b'), # Navy Indigo
            spaceAfter=8
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#312e81'),
            spaceBefore=14,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1e293b')
        )
        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor('#0f172a')
        )

        story = []

        # 1. Header
        story.append(Paragraph("Concept Relationship & Terminology Report", title_style))
        meta = graph_data.get("metadata", {})
        filename = meta.get("filename", "Uploaded Technical Document")
        story.append(Paragraph(f"Analysis for: <b>{filename}</b> | Knowledge Graph Pipeline Output", subtitle_style))
        story.append(Spacer(1, 8))

        # 2. Executive Summary Metrics Table
        metrics_data = [
            [
                Paragraph("Total Words", meta_label_style),
                Paragraph(str(meta.get("word_count", 0)), body_style),
                Paragraph("Extracted Concepts", meta_label_style),
                Paragraph(str(len(graph_data.get("nodes", []))), body_style)
            ],
            [
                Paragraph("Sentences", meta_label_style),
                Paragraph(str(meta.get("sentence_count", 0)), body_style),
                Paragraph("Detected Relationships", meta_label_style),
                Paragraph(str(len(graph_data.get("edges", []))), body_style)
            ],
            [
                Paragraph("Graph Density", meta_label_style),
                Paragraph(str(meta.get("density", 0.0)), body_style),
                Paragraph("Storage Engine", meta_label_style),
                Paragraph(graph_data.get("database_status", {}).get("provider", "Graph Store"), body_style)
            ]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[120, 130, 140, 150])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 14))

        # 3. Top Extracted Terminology
        story.append(Paragraph("Key Extracted Terminology & Concepts", h2_style))
        term_table_data = [
            [
                Paragraph("<b>Concept Name</b>", meta_label_style),
                Paragraph("<b>Category</b>", meta_label_style),
                Paragraph("<b>Freq</b>", meta_label_style),
                Paragraph("<b>TF-IDF</b>", meta_label_style),
                Paragraph("<b>Context / Definition</b>", meta_label_style)
            ]
        ]

        nodes = graph_data.get("nodes", [])[:15] # Top 15 in report
        for n in nodes:
            context_snippet = n.get("definition", "")
            if len(context_snippet) > 110:
                context_snippet = context_snippet[:107] + "..."
            term_table_data.append([
                Paragraph(f"<b>{n['label']}</b>", body_style),
                Paragraph(n['category'], body_style),
                Paragraph(str(n.get('frequency', 1)), body_style),
                Paragraph(f"{n.get('tfidf_score', 0.0):.3f}", body_style),
                Paragraph(context_snippet, body_style)
            ])

        term_table = Table(term_table_data, colWidths=[110, 95, 40, 50, 245])
        term_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(term_table)
        story.append(Spacer(1, 14))

        # 4. Top Detected Concept Relationships
        story.append(Paragraph("Detected Concept Relationships", h2_style))
        node_id_to_label = {str(n["id"]): n["label"] for n in graph_data.get("nodes", [])}
        
        rel_table_data = [
            [
                Paragraph("<b>Source Concept</b>", meta_label_style),
                Paragraph("<b>Relationship</b>", meta_label_style),
                Paragraph("<b>Target Concept</b>", meta_label_style),
                Paragraph("<b>Type</b>", meta_label_style),
                Paragraph("<b>Confidence</b>", meta_label_style)
            ]
        ]

        edges = graph_data.get("edges", [])[:15]
        for e in edges:
            source = node_id_to_label.get(str(e["from"]), str(e["from"]))
            target = node_id_to_label.get(str(e["to"]), str(e["to"]))
            rel_table_data.append([
                Paragraph(source, body_style),
                Paragraph(f"<b>{e.get('label', 'relates to')}</b>", body_style),
                Paragraph(target, body_style),
                Paragraph(e.get("type", "co-occurrence"), body_style),
                Paragraph(f"{e.get('confidence', 0.5):.2f}", body_style)
            ])

        rel_table = Table(rel_table_data, colWidths=[130, 110, 130, 100, 70])
        rel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(rel_table)

        doc.build(story)
        buffer.seek(0)
        return buffer
