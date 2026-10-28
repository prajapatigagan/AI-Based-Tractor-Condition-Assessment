import streamlit as st

from core.chat_engine import build_report_context, chat_reply


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Tractor AI Assistant",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Custom CSS
# --------------------------------------------------
st.markdown(
    """
    <style>
    /* Main application background */
    .stApp {
        background: linear-gradient(135deg, #f4f8f4, #edf4ef);
    }

    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #123c2a;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    [data-testid="stSidebar"] button {
        border-radius: 10px;
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #123c2a, #237447);
        padding: 32px;
        border-radius: 22px;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(18, 60, 42, 0.14);
    }

    .hero h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .hero p {
        color: #e1f2e6;
        font-size: 1rem;
        line-height: 1.7;
        margin-bottom: 0;
    }

    .badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        color: #ffffff;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-bottom: 12px;
    }

    /* Report information cards */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dfe9e1;
        border-radius: 15px;
        padding: 18px;
        box-shadow: 0 3px 12px rgba(18,60,42,0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #53665a;
        font-weight: 600;
    }

    /* Chat message containers */
    [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e1ebe3;
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 12px;
    }

    /* Chat input */
    [data-testid="stChatInput"] {
        border-radius: 14px;
    }

    [data-testid="stChatInput"] textarea {
        background: #ffffff;
    }

    /* General buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 650;
        min-height: 42px;
    }

    /* Section headings */
    .section-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #173d2a;
        margin-top: 22px;
        margin-bottom: 8px;
    }

    .section-subtitle {
        color: #637368;
        font-size: 0.95rem;
        margin-bottom: 18px;
    }

    /* Empty chat welcome card */
    .welcome-card {
        background: #ffffff;
        border: 1px solid #dce9df;
        border-radius: 18px;
        padding: 28px;
        text-align: center;
        margin: 22px 0;
    }

    .welcome-card h3 {
        color: #173d2a;
        margin-bottom: 10px;
    }

    .welcome-card p {
        color: #637368;
        line-height: 1.7;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #75847a;
        font-size: 0.83rem;
        padding-top: 30px;
    }

    /* Mobile */
    @media (max-width: 768px) {
        .hero {
            padding: 22px;
        }

        .hero h1 {
            font-size: 1.65rem;
        }

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }


    /* ---------- Readability / contrast improvements ---------- */
    .stApp {
        background: #e9eee9 !important;
        color: #17251b !important;
    }

    /* Dark body text on the light main canvas and cards. */
    [data-testid="stAppViewContainer"] .stMarkdown,
    [data-testid="stAppViewContainer"] .stMarkdown p,
    [data-testid="stAppViewContainer"] .stMarkdown li,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] {
        color: #202b23;
    }

    .section-title { color: #123c2a !important; }
    .section-subtitle { color: #39483e !important; }
    .footer { color: #46534a !important; }

    /* Darker green hero with clear white lettering. */
    .hero {
        background: linear-gradient(135deg, #102f22, #1d6039) !important;
    }
    .hero h1, .hero p, .hero .badge { color: #ffffff !important; }
    .hero p { color: #f0f7f1 !important; }

    /* Pale message cards with dark text. */
    [data-testid="stMetric"],
    [data-testid="stChatMessage"],
    [data-testid="stExpander"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8faf8 !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong {
        color: #17251b !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #17251b !important;
        caret-color: #123c2a !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #59665d !important;
        opacity: 1 !important;
    }

    .welcome-card {
        background: #f8faf8 !important;
        border-color: #cbd8cd !important;
    }
    .welcome-card h3 { color: #123c2a !important; }
    .welcome-card p { color: #39483e !important; }

    /* Sidebar intentionally stays dark; keep its text high-contrast. */
    [data-testid="stSidebar"] {
        background: #102f22 !important;
    }
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #f7faf7 !important;
    }
    [data-testid="stSidebar"] button {
        background: #1d6039 !important;
        color: #ffffff !important;
        border: 1px solid #4a8060 !important;
    }
    [data-testid="stSidebar"] button:hover {
        background: #287748 !important;
        color: #ffffff !important;
    }

    /* Buttons remain dark green with white text. */
    .stButton > button {
        background: #1d6039;
        color: #ffffff;
    }
    .stButton > button:hover {
        background: #154a2b;
        color: #ffffff;
    }
    .stButton > button:disabled {
        background: #d3dbd4 !important;
        color: #344239 !important;
        opacity: 1 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.markdown("# 🚜 Tractor AI")
    st.caption("Your intelligent tractor inspection assistant")

    st.markdown("---")

    st.markdown("### 💬 Chat Controls")

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state["chat"] = []
        st.rerun()

    st.markdown("---")

    st.markdown("### 💡 What You Can Ask")

    st.markdown(
        """
        - What is the overall tractor condition?
        - Which parts need attention?
        - What problems were detected?
        - Is the tractor worth buying?
        - What should a mechanic inspect?
        - What maintenance is recommended?
        """
    )

    st.markdown("---")

    st.caption(
        "Tip: Ask specific questions about the inspection report "
        "for more useful answers."
    )


# --------------------------------------------------
# Hero Section
# --------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="badge">AI-POWERED TRACTOR ASSISTANT</div>
        <h1>💬 Tractor AI Chatbot</h1>
        <p>
            Ask questions about your tractor inspection report.
            Understand its condition, identify potential issues,
            and explore recommended maintenance steps.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Retrieve Inspection Report
# --------------------------------------------------
report = st.session_state.get("report")

if not report or not report.get("accepted"):
    st.warning(
        "No inspection report found. Please upload tractor photos "
        "on the main page and generate a report before starting a chat."
    )

    st.info(
        "Once your inspection report is ready, return here to ask "
        "questions about the results."
    )

    st.stop()


accepted = report["accepted"]
result = report.get("result")


# --------------------------------------------------
# Report Summary
# --------------------------------------------------
st.markdown(
    '<div class="section-title">📊 Inspection Overview</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">'
    'Review your inspection summary before starting the conversation.'
    '</div>',
    unsafe_allow_html=True,
)

if result:
    grade = result.get("grade", "N/A")
    score = result.get("score", "N/A")
    confidence = result.get("confidence", "N/A")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Condition Grade",
            value=str(grade),
        )

    with col2:
        st.metric(
            label="Condition Score",
            value=f"{score}/100",
        )

    with col3:
        st.metric(
            label="AI Confidence",
            value=f"{confidence}%",
        )

else:
    st.info(
        "An inspection report is available, but detailed grading "
        "information is not available."
    )


st.markdown("---")


# --------------------------------------------------
# Build Chat Context
# --------------------------------------------------
context = build_report_context(result, accepted, report.get("limitations"))

history = st.session_state.setdefault("chat", [])


# --------------------------------------------------
# Chat Section
# --------------------------------------------------
st.markdown(
    '<div class="section-title">🤖 Chat with Your Tractor AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">'
    'Ask questions in natural language and get answers based on your report.'
    '</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Welcome Screen
# --------------------------------------------------
if not history:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>👋 Welcome to Tractor AI Assistant!</h3>
            <p>
                Your inspection report is ready. Ask me about the
                tractor's condition, potential problems, maintenance
                requirements, or points to verify before purchasing.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Try asking:**")


# --------------------------------------------------
# Suggested Questions
# --------------------------------------------------
if not history:
    suggestions = [
        "Summarize the tractor condition",
        "Which parts need attention?",
        "What maintenance is recommended?",
    ]

    cols = st.columns(3)

    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(
                suggestion,
                key=f"suggestion_{i}",
                use_container_width=True,
            ):
                st.session_state["pending_question"] = suggestion
                st.rerun()


# --------------------------------------------------
# Display Chat History
# --------------------------------------------------
for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# Chat Input
# --------------------------------------------------
question = st.chat_input(
    "Ask anything about your tractor inspection..."
)

if not question:
    question = st.session_state.pop("pending_question", None)


# --------------------------------------------------
# Process User Question
# --------------------------------------------------
if question:
    history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your inspection report..."):
            try:
                reply = chat_reply(history, context)

                if not isinstance(reply, str):
                    reply = str(reply)

            except Exception as error:
                reply = (
                    "I couldn't process your question right now. "
                    "Please try again.\n\n"
                    f"**Error details:** {error}"
                )

        st.markdown(reply)

    history.append(
        {
            "role": "assistant",
            "content": reply,
        }
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown(
    """
    <div class="footer">
        🚜 Tractor Condition Check AI
        <br>
        AI-generated observations are informational and should be
        verified by a qualified tractor mechanic.
    </div>
    """,
    unsafe_allow_html=True,
)
