import os
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image as PILImage, ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, Spacer, Table, TableStyle, KeepTogether,
)

# ---------- Constants ----------
TOTAL_SLOTS = 8
MIN_RELIABLE_SLOTS = 4
MAX_IMG_PX = 1200          # PDF mein embed hone se pehle image is size tak chhoti hogi
JPEG_QUALITY = 80
MAX_IMG_HEIGHT = 12 * cm   # bahut lambi portrait photo page se bahar na jaye

SEV_COLORS = {
    "low": colors.HexColor("#1e8e4e"),
    "medium": colors.HexColor("#d98a00"),
    "high": colors.HexColor("#dc2626"),
}

# ---------- Styles (ek baar banao, har call par nahi) ----------
_styles = getSampleStyleSheet()
NORMAL = _styles["Normal"]
TITLE = _styles["Title"]
H2 = _styles["Heading2"]
H3 = _styles["Heading3"]
H4 = _styles["Heading4"]
SMALL = ParagraphStyle("small", parent=NORMAL, fontSize=8)
BULLET = ParagraphStyle("bullet", parent=NORMAL, leftIndent=12, bulletIndent=0)


# ---------- Image helpers ----------
@lru_cache(maxsize=128)
def _prepared_image(path):
    """Image ko resize + EXIF rotation fix karke compressed JPEG bytes deta hai."""
    try:
        with PILImage.open(path) as im:
            im = ImageOps.exif_transpose(im)   # phone photos sideways na aayein
            im.thumbnail((MAX_IMG_PX, MAX_IMG_PX))
            im = im.convert("RGB")
            buf = BytesIO()
            im.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)
            return buf.getvalue(), im.width, im.height
    except Exception:
        return None


def _thumb(path, width=3 * cm, max_height=MAX_IMG_HEIGHT):
    prepared = _prepared_image(path)
    if not prepared:
        return None
    data, w, h = prepared
    height = width * h / w
    if height > max_height:
        width, height = width * max_height / height, max_height
    return Image(BytesIO(data), width=width, height=height)


def _bullets(items):
    return [Paragraph(escape(str(s)), BULLET, bulletText="•") for s in items]


# ---------- Sections ----------
def _header_section(accepted, rejected):
    return [
        Paragraph("Tractor Inspection Report", TITLE),
        Paragraph(datetime.now().strftime("%d-%m-%Y %H:%M"), NORMAL),
        Spacer(1, 12),
        Paragraph(
            f"Total photos: {len(accepted) + len(rejected)} | "
            f"Accepted: {len(accepted)} | Rejected: {len(rejected)}",
            H3,
        ),
        Spacer(1, 8),
    ]


def _findings_section(findings):
    story = [Paragraph("Findings", H2)]
    if not findings:
        story.append(Paragraph("Analyze ki gayi photos mein koi visible issue nahi mila.", NORMAL))
        return story

    data = [["Part", "Issue", "Severity", "Evidence (photo)"]]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf3ec")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8d2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]

    for i, f in enumerate(findings, start=1):
        ev = f.get("evidence", [])
        cell = []
        if ev and ev[0].get("path"):
            thumb = _thumb(ev[0]["path"])
            if thumb:
                cell.append(thumb)
        cell.append(Paragraph(escape(", ".join(e["label"] for e in ev)), SMALL))

        sev = str(f.get("severity", "")).lower()
        data.append([
            Paragraph(escape(f["part"].title()), NORMAL),
            Paragraph(escape(f["issue"].title()), NORMAL),
            sev.upper(),
            cell,
        ])
        style += [
            ("TEXTCOLOR", (2, i), (2, i), SEV_COLORS.get(sev, colors.black)),
            ("FONTNAME", (2, i), (2, i), "Helvetica-Bold"),
        ]

    table = Table(data, colWidths=[3.2 * cm, 3.2 * cm, 2.2 * cm, 6.5 * cm], repeatRows=1)
    table.setStyle(TableStyle(style))
    story.append(table)
    return story


def _grade_section(result):
    covered = len(result.get("covered_slots", []))
    story = [
        Paragraph(f"Visual Grade: {result['grade']} (Score {result['score']}/100)", H2),
        Paragraph(
            f"Confidence: {result['confidence']}% ({result['confidence_label']}) | "
            f"Angles covered: {covered}/{TOTAL_SLOTS}",
            NORMAL,
        ),
    ]
    if not result.get("reliable", True):
        story += [
            Spacer(1, 4),
            Paragraph(
                f"<b>Note:</b> {TOTAL_SLOTS} mein se {MIN_RELIABLE_SLOTS} se kam angles mile, "
                "isliye ye grade sirf indicative hai.",
                NORMAL,
            ),
        ]
    story.append(Spacer(1, 10))
    story += _findings_section(result.get("findings", []))
    story.append(Spacer(1, 14))
    return story


def _limitations_section(limitations):
    story = [Paragraph("Limitations", H2)]
    if limitations.get("specific"):
        story.append(Paragraph("Is inspection ki limitations:", H4))
        story += _bullets(limitations["specific"])
        story.append(Spacer(1, 6))

    story.append(Paragraph("Photos se kya pata nahi chal sakta:", H4))
    story += _bullets(limitations.get("general", []))
    story += [
        Spacer(1, 8),
        Paragraph(f"<b>Recommendation:</b> {escape(limitations.get('recommendation', ''))}", NORMAL),
        Spacer(1, 14),
    ]
    return story


def _accepted_section(accepted):
    story = [Paragraph("Accepted Photos", H2)]
    for path, analysis in accepted:
        label = analysis.get("slot_label", os.path.basename(path))
        summary = analysis.get("summary", "")

        block = [Paragraph(escape(label), H4)]
        img = _thumb(path, width=10 * cm)
        if img:
            block.append(img)
        block.append(Spacer(1, 6))
        story.append(KeepTogether(block))   # heading image se alag page par na rahe
        story.append(Paragraph(escape(summary).replace("\n", "<br/>"), NORMAL))
        story.append(Spacer(1, 16))
    return story


def _rejected_section(rejected):
    story = [Paragraph("Rejected Photos (dobara upload karo)", H2)]
    story += [
        Paragraph(f"{escape(str(label))}: {escape(str(reason))}", NORMAL)
        for _, reason, label in rejected
    ]
    return story


# ---------- Main ----------
def make_pdf(accepted, rejected, out_path, result=None, limitations=None):
    out_dir = os.path.dirname(out_path)
    if out_dir:                       # dirname "" ho to makedirs crash karta tha
        os.makedirs(out_dir, exist_ok=True)

    story = _header_section(accepted, rejected)
    if result:
        story += _grade_section(result)
    if limitations:
        story += _limitations_section(limitations)
    story += _accepted_section(accepted)
    if rejected:
        story += _rejected_section(rejected)

    SimpleDocTemplate(
        out_path, pagesize=A4, title="Tractor Inspection Report"
    ).build(story)

    _prepared_image.cache_clear()     # memory free karo
