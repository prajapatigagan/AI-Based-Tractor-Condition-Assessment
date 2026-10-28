import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, Spacer, Table, TableStyle,
)

SEV_COLORS = {
    "low": colors.HexColor("#1e8e4e"),
    "medium": colors.HexColor("#d98a00"),
    "high": colors.HexColor("#dc2626"),
}


def _thumb(path, width=3 * cm):
    try:
        w, h = ImageReader(path).getSize()
        return Image(path, width=width, height=width * h / w)
    except Exception:
        return None


def make_pdf(accepted, rejected, out_path, result=None, limitations=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=normal, fontSize=8)

    story = [
        Paragraph("Tractor Inspection Report", styles["Title"]),
        Paragraph(datetime.now().strftime("%d-%m-%Y %H:%M"), normal),
        Spacer(1, 12),
        Paragraph(
            f"Total photos: {len(accepted) + len(rejected)} | "
            f"Accepted: {len(accepted)} | Rejected: {len(rejected)}",
            styles["Heading3"],
        ),
        Spacer(1, 8),
    ]

    # ----- Grade -----
    if result:
        story.append(Paragraph(
            f"Visual Grade: {result['grade']} (Score {result['score']}/100)", styles["Heading2"]))
        story.append(Paragraph(
            f"Confidence: {result['confidence']}% ({result['confidence_label']}) | "
            f"Angles covered: {len(result['covered_slots'])}/8", normal))
        if not result.get("reliable", True):
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                "<b>Note:</b> 8 mein se 4 se kam angles mile, isliye ye grade sirf indicative hai.",
                normal))
        story.append(Spacer(1, 10))

        # ----- Findings table with evidence -----
        story.append(Paragraph("Findings", styles["Heading2"]))
        if result["findings"]:
            data = [["Part", "Issue", "Severity", "Evidence (photo)"]]
            for f in result["findings"]:
                ev = f.get("evidence", [])
                cell = []
                if ev and ev[0].get("path"):
                    t = _thumb(ev[0]["path"])
                    if t:
                        cell.append(t)
                cell.append(Paragraph(escape(", ".join(e["label"] for e in ev)), small))
                data.append([
                    Paragraph(escape(f["part"].title()), normal),
                    Paragraph(escape(f["issue"].title()), normal),
                    f["severity"].upper(),
                    cell,
                ])

            table = Table(data, colWidths=[3.2 * cm, 3.2 * cm, 2.2 * cm, 6.5 * cm], repeatRows=1)
            style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf3ec")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8d2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
            for i, f in enumerate(result["findings"], start=1):
                style.append(("TEXTCOLOR", (2, i), (2, i), SEV_COLORS.get(f["severity"], colors.black)))
                style.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))
            table.setStyle(TableStyle(style))
            story.append(table)
        else:
            story.append(Paragraph("Analyze ki gayi photos mein koi visible issue nahi mila.", normal))
        story.append(Spacer(1, 14))

    # ----- Limitations -----
    if limitations:
        story.append(Paragraph("Limitations", styles["Heading2"]))
        if limitations.get("specific"):
            story.append(Paragraph("Is inspection ki limitations:", styles["Heading4"]))
            for s in limitations["specific"]:
                story.append(Paragraph(escape(f"- {s}"), normal))
            story.append(Spacer(1, 6))

        story.append(Paragraph("Photos se kya pata nahi chal sakta:", styles["Heading4"]))
        for s in limitations["general"]:
            story.append(Paragraph(escape(f"- {s}"), normal))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Recommendation:</b> {escape(limitations['recommendation'])}", normal))
        story.append(Spacer(1, 14))

    # ----- Accepted images -----
    story.append(Paragraph("Accepted Photos", styles["Heading2"]))
    for path, analysis in accepted:
        label = analysis.get("slot_label", os.path.basename(path))
        summary = analysis.get("summary", "")
        story.append(Paragraph(escape(label), styles["Heading4"]))
        t = _thumb(path, width=10 * cm)
        if t:
            story.append(t)
        story.append(Spacer(1, 6))
        story.append(Paragraph(escape(summary).replace("\n", "<br/>"), normal))
        story.append(Spacer(1, 16))

    # ----- Rejected images -----
    if rejected:
        story.append(Paragraph("Rejected Photos (dobara upload karo)", styles["Heading2"]))
        for path, reason, label in rejected:
            story.append(Paragraph(f"{escape(label)}: {escape(str(reason))}", normal))

    SimpleDocTemplate(out_path, pagesize=A4).build(story)