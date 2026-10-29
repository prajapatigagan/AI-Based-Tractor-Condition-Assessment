import os
import html
import tempfile
import shutil
from pathlib import Path

import streamlit as st

from core.config import PHOTO_SLOTS
from core.quality_check import check_quality
from core.image_analysis import analyze_image
from core.scoring import score_tractor
from core.limitations import build_limitations
from core.pdf_report import make_pdf


# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="Tractor Condition Check AI",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded",
)

GRADE_COLORS = {"A": "#1e8e4e", "B": "#7cb342", "C": "#f59e0b", "D": "#dc2626"}
GRADE_TEXT = {
    "A": "Excellent condition",
    "B": "Good condition",
    "C": "Average condition",
    "D": "Needs attention",
}
IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]
CSS_PATH = Path(__file__).parent / "assets" / "style.css"


# ==================================================
# HELPERS
# ==================================================
def reset_session():
    """Purani report, chat aur temp photos saaf karo."""
    old_dir = st.session_state.get("tmp_dir")
    if old_dir:
        shutil.rmtree(old_dir, ignore_errors=True)

    for key in ("report", "chat", "tmp_dir"):
        st.session_state.pop(key, None)

    # uploader key badalne se uploaded files clear ho jati hain
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1


def load_css():
    try:
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("assets/style.css nahi mili, isliye default design dikh raha hai.")


load_css()


# ==================================================
# HERO SECTION
# ==================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">AI-POWERED TRACTOR INSPECTION</div>
        <h1>🚜 Tractor Condition Check AI</h1>
        <p>
            Upload tractor photos angle-wise, analyze visible condition,
            identify potential issues, and download an inspection report
            that also clearly states what photos cannot tell.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# PHOTO UPLOAD (8 SLOTS)
# ==================================================
st.markdown(
    '<div class="section-title">📸 Upload Tractor Photos</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="section-description">
        Har angle ke liye ek photo upload karo. Saare 8 zaroori nahi,
        par jitne zyada angles, utna reliable report.
    </div>
    """,
    unsafe_allow_html=True,
)

uploader_key = st.session_state.get("uploader_key", 0)
slot_files = {}

with st.container(border=True):
    for row_slots in (PHOTO_SLOTS[:4], PHOTO_SLOTS[4:]):
        cols = st.columns(4)
        for col, (key, label) in zip(cols, row_slots):
            with col:
                uploaded = st.file_uploader(
                    label,
                    type=IMAGE_TYPES,
                    key=f"{key}_{uploader_key}",
                )
                if uploaded:
                    slot_files[key] = uploaded
                    st.image(uploaded, width="stretch")

if slot_files:
    missing_now = [label for key, label in PHOTO_SLOTS if key not in slot_files]
    st.caption(f"{len(slot_files)}/{len(PHOTO_SLOTS)} angles upload hui")
    if missing_now:
        st.caption("Baaki angles: " + ", ".join(missing_now))


# ==================================================
# GENERATE REPORT
# ==================================================
st.markdown("---")

if st.button(
    "🔍 Analyze Photos & Generate Report",
    type="primary",
    width="stretch",
    disabled=not slot_files,
):
    # Pichli report ka temp folder saaf karo
    old_dir = st.session_state.get("tmp_dir")
    if old_dir:
        shutil.rmtree(old_dir, ignore_errors=True)

    tmp_dir = tempfile.mkdtemp(prefix="tractor_report_")
    st.session_state["tmp_dir"] = tmp_dir

    accepted = []     # (path, analysis)
    rejected = []     # (path, reason, label)
    pdf_bytes = None

    progress = st.progress(0, text="Initializing tractor inspection...")
    status_text = st.empty()

    try:
        todo = [(key, label) for key, label in PHOTO_SLOTS if key in slot_files]
        total = len(todo)

        for i, (key, label) in enumerate(todo):
            uploaded_file = slot_files[key]
            safe_name = os.path.basename(uploaded_file.name)
            path = os.path.join(tmp_dir, f"{key}_{safe_name}")

            with open(path, "wb") as output_file:
                output_file.write(uploaded_file.getbuffer())

            progress.progress(
                int((i / total) * 100),
                text=f"Checking {label} ({i + 1} of {total})...",
            )
            status_text.info(f"Inspecting: {label}")

            # Step 1: quality check
            try:
                is_acceptable, reason = check_quality(path)
            except Exception as error:
                rejected.append((path, f"Image quality check failed: {error}", label))
                continue

            if not is_acceptable:
                rejected.append((path, reason, label))
                continue

            # Step 2: AI analysis
            try:
                analysis = analyze_image(path, key)
                analysis["slot"] = key
                analysis["slot_label"] = label
                analysis["path"] = path
                accepted.append((path, analysis))
            except Exception as error:
                rejected.append((path, f"Image analysis failed: {error}", label))

        progress.progress(100, text="Image processing completed!")
        status_text.empty()

        # Step 3: score + limitations
        analyses = [a for _, a in accepted]

        if analyses:
            result = score_tractor(analyses)
            missing = result["missing_slots"]
            confidence = result["confidence"]
        else:
            result = None
            missing = [label for _, label in PHOTO_SLOTS]
            confidence = 0

        limitations = build_limitations(analyses, missing, confidence)

        # Step 4: PDF
        if accepted or rejected:
            pdf_path = os.path.join(tmp_dir, "tractor_report.pdf")
            make_pdf(accepted, rejected, pdf_path, result, limitations)
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()

        st.session_state["report"] = {
            "accepted": accepted,
            "rejected": rejected,
            "result": result,
            "limitations": limitations,
            "pdf": pdf_bytes,
        }
        st.session_state["chat"] = []

        st.success("Tractor inspection completed successfully!")

    except Exception as error:
        st.error(f"Unable to complete the inspection: {error}")

    finally:
        # Temp folder yahan delete NAHI karte, report mein images isi se dikhti hain.
        progress.empty()
        status_text.empty()


# ==================================================
# DISPLAY REPORT
# ==================================================
report = st.session_state.get("report")

if report:
    accepted = report.get("accepted", [])
    rejected = report.get("rejected", [])
    result = report.get("result")
    limitations = report.get("limitations") or {}

    st.markdown("---")
    st.markdown(
        '<div class="section-title">📊 Inspection Dashboard</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # TOP SUMMARY
    # --------------------------------------------------
    if result:
        grade = str(result.get("grade", "N/A"))
        score = result.get("score", 0)
        confidence = result.get("confidence", 0)
        confidence_label = result.get("confidence_label", "")
        color = GRADE_COLORS.get(grade, "#6b7280")

        col_grade, col_stats = st.columns([1, 2], gap="large")

        with col_grade:
            st.markdown(
                f"""
                <div class="grade-card" style="background: {color};">
                    <div class="label">VISUAL GRADE</div>
                    <div class="letter">{html.escape(grade)}</div>
                    <div class="text">{GRADE_TEXT.get(grade, "")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_stats:
            r1c1, r1c2 = st.columns(2)
            r1c1.metric("Condition Score", f"{score}/100")
            r1c2.metric("AI Confidence", f"{confidence}% ({confidence_label})")

            r2c1, r2c2 = st.columns(2)
            r2c1.metric("Angles Covered", f"{len(result['covered_slots'])}/{len(PHOTO_SLOTS)}")
            r2c2.metric("Rejected Photos", len(rejected))

            st.progress(
                min(max(int(score), 0), 100) / 100,
                text=f"Overall condition: {score}%",
            )

        if result["missing_slots"]:
            st.warning(
                "Ye angles cover nahi hue, isliye inka assessment nahi hua: "
                + ", ".join(result["missing_slots"])
            )

        if not result.get("reliable", True):
            st.warning(
                "8 mein se 4 se kam angles mile, isliye ye grade sirf indicative hai. "
                "Zyada angles upload karoge toh result behtar hoga."
            )
        elif confidence < 50:
            st.warning(
                f"Confidence sirf {confidence}% hai (photos kam clear thi ya angles kam the). "
                "Grade par zyada bharosa mat karo."
            )
    else:
        st.warning(
            "No condition score is available because no images "
            "were successfully analyzed."
        )

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # --------------------------------------------------
    # TABS: Findings | Photos | Limitations | Rejected
    # --------------------------------------------------
    tab_names = [
        "🔎 Findings",
        f"✅ Photos ({len(accepted)})",
        "🧭 Limitations",
    ]
    if rejected:
        tab_names.append(f"⚠️ Rejected ({len(rejected)})")

    tabs = st.tabs(tab_names)

    # ---- Findings ----
    with tabs[0]:
        findings = result.get("findings", []) if result else []

        if findings:
            rows = ""
            for f in findings:
                part = html.escape(str(f.get("part", "unknown")).title())
                issue = html.escape(str(f.get("issue", "unknown")).title())
                sev = str(f.get("severity", "low")).lower()
                if sev not in ("low", "medium", "high"):
                    sev = "low"
                evidence = html.escape(
                    ", ".join(e["label"] for e in f.get("evidence", [])) or "-"
                )
                rows += (
                    f"<tr><td>🔧 {part}</td><td>{issue}</td>"
                    f'<td><span class="chip chip-{sev}">{sev.upper()}</span></td>'
                    f"<td>📷 {evidence}</td></tr>"
                )

            st.markdown(
                f"""
                <table class="find-table">
                    <thead>
                        <tr><th>Part</th><th>Issue</th><th>Severity</th><th>Evidence</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Analyze ki gayi photos mein koi visible issue nahi mila. "
                "Iska matlab ye nahi ki tractor mein mechanical problem nahi hai."
            )

    # ---- Accepted photos ----
    with tabs[1]:
        if accepted:
            cols = st.columns(3)
            for i, (path, analysis) in enumerate(accepted):
                with cols[i % 3]:
                    with st.container(border=True):
                        if os.path.exists(path):
                            st.image(path, width="stretch")
                        else:
                            st.warning("Image file ab available nahi hai.")
                        st.caption(f"**{analysis.get('slot_label', 'Photo')}**")

                        with st.expander("AI analysis dekho"):
                            st.write(analysis.get("summary", "No summary available."))
        else:
            st.info("No photos were accepted for AI analysis.")

    # ---- Limitations ----
    with tabs[2]:
        specific = limitations.get("specific", [])
        if specific:
            st.markdown("**Is inspection ki limitations**")
            for s in specific:
                st.markdown(f"- {s}")

        st.markdown("**Photos se kya pata nahi chal sakta**")
        for s in limitations.get("general", []):
            st.markdown(f"- {s}")

        if limitations.get("recommendation"):
            st.info(limitations["recommendation"])

    # ---- Rejected ----
    if rejected:
        with tabs[3]:
            st.caption(
                "Reason dekho aur in angles ki photos behtar light/focus mein "
                "dobara upload karo."
            )
            for path, reason, label in rejected:
                st.error(f"**{label}**: {reason}")

    # --------------------------------------------------
    # PDF DOWNLOAD
    # --------------------------------------------------
    st.markdown("---")
    st.markdown(
        '<div class="section-title">📄 Download Inspection Report</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-description">
            PDF mein grade, findings (photo evidence ke saath),
            limitations aur recommendation shamil hain.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if report.get("pdf"):
        st.download_button(
            label="⬇️ Download PDF Report",
            data=report["pdf"],
            file_name="tractor_condition_report.pdf",
            mime="application/pdf",
            width="stretch",
        )
    else:
        st.warning("The PDF report is not available for this inspection.")

    st.markdown(
        """
        <div class="info-card">
            <h4>💬 Need More Information?</h4>
            <p>
                Open the <b>Chatbot</b> page from the sidebar
                to ask questions about your tractor inspection
                report and its limitations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# FOOTER
# ==================================================
st.markdown(
    """
    <div class="footer">
        🚜 Tractor Condition Check AI
        <br>
        AI-generated visual assessments are informational.
        Consult a qualified mechanic before making purchase
        or repair decisions.
    </div>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# SIDEBAR PANEL
# ==================================================
with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="icon">🚜</div>
            <div class="name">Tractor Check AI</div>
            <div class="tag">VISUAL INSPECTION</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-title">Report Status</div>', unsafe_allow_html=True)

    current = st.session_state.get("report")

    if current and current.get("result"):
        res = current["result"]
        g = str(res.get("grade", "N/A"))
        g_color = GRADE_COLORS.get(g, "#6b7280")

        st.markdown(
            '<div class="side-status ready">✅ Report ready</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="side-stats">
                <div class="side-stat">
                    <div class="val" style="color:{g_color};">{html.escape(g)}</div>
                    <div class="lbl">Grade</div>
                </div>
                <div class="side-stat">
                    <div class="val">{res.get("score", 0)}</div>
                    <div class="lbl">Score</div>
                </div>
                <div class="side-stat">
                    <div class="val">{res.get("confidence", 0)}%</div>
                    <div class="lbl">Confidence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif current:
        st.markdown(
            '<div class="side-status empty">⚠️ Koi photo accept nahi hui</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="side-status empty">⏳ Abhi koi report nahi hai</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="side-title">Quick Actions</div>', unsafe_allow_html=True)

    st.page_link(
        "pages/1_Chatbot.py",
        label="Open Chatbot",
        icon="💬",
        disabled=not (current and current.get("accepted")),
    )

    st.button(
        "🔄 New Inspection",
        on_click=reset_session,
        disabled=not (current or slot_files),
        width="stretch",
    )

    # ---- Photo checklist (live) ----
    st.markdown('<div class="side-title">Photo Checklist</div>', unsafe_allow_html=True)

    covered_now = set()
    if current and current.get("result"):
        covered_now = {a["slot"] for _, a in current["accepted"]}
    done = set(slot_files) | covered_now

    items = "".join(
        f"<li>{'✅' if key in done else '⬜'} {label}</li>"
        for key, label in PHOTO_SLOTS
    )
    st.markdown(f'<ul class="angle-list">{items}</ul>', unsafe_allow_html=True)

    st.markdown('<div class="side-title">How To Use</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <ol class="step-list">
            <li>Har angle ki photo upload karo</li>
            <li>Analyze button dabao</li>
            <li>Report, limitations dekho, PDF download karo</li>
            <li>Chatbot se sawaal poochho</li>
        </ol>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("💡 Better photo tips"):
        st.markdown(
            "- Din ki roshni mein photo lo\n"
            "- Tractor poora frame mein rakho\n"
            "- Camera hilne se bachao (blur na ho)\n"
            "- Engine aur tyres ki close-up lo\n"
            "- Hour meter ki reading saaf dikhe"
        )

    st.markdown(
        '<div class="side-footer">v1.1 • Visual assessment only</div>',
        unsafe_allow_html=True,
    )