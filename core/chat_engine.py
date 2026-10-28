from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.config import OPENROUTER_API_KEY, BASE_URL, CHAT_MODEL

model = ChatOpenAI(
    model=CHAT_MODEL,
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY,
    temperature=0.7,
    max_retries=3,
    timeout=60,
)

SYSTEM_PROMPT = (
    "You are a helpful tractor inspection assistant. "
    "Reply in Hinglish, short and clear. "
    "Answer ONLY from the tractor inspection report below. "
    "If the answer is not in the report, say: 'Ye report mein nahi hai.' "
    "If the user asks about something listed under Limitations or about a photo "
    "angle that was not assessed, say clearly that it cannot be determined from the photos. "
    "Never invent damage or findings."
)


def build_report_context(result, accepted, limitations=None):
    lines = []
    if result:
        lines.append(f"Grade: {result['grade']}, Score: {result['score']}/100, "
                     f"Confidence: {result['confidence']}% ({result['confidence_label']})")
        lines.append("Angles covered: " + (", ".join(result["covered_slots"]) or "none"))
        if result["missing_slots"]:
            lines.append("Angles NOT assessed: " + ", ".join(result["missing_slots"]))
        if result["findings"]:
            lines.append("Findings:")
            for f in result["findings"]:
                photos = ", ".join(e["label"] for e in f.get("evidence", []))
                lines.append(f"- {f['part']}: {f['issue']} ({f['severity']}) [photos: {photos}]")
        else:
            lines.append("Findings: koi visible issue nahi mila")

    if limitations:
        lines.append("Limitations:")
        for s in limitations["specific"] + limitations["general"]:
            lines.append(f"- {s}")
        lines.append("Recommendation: " + limitations["recommendation"])

    lines.append("Photo summaries:")
    for _, a in accepted:
        lines.append(f"- {a.get('slot_label', 'Photo')}: {a.get('summary', '')}")
    return "\n".join(lines)


def chat_reply(history, report_context):
    system = f"{SYSTEM_PROMPT}\n\nREPORT:\n{report_context}"
    messages = [SystemMessage(content=system)]
    for m in history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))
    return model.invoke(messages).content