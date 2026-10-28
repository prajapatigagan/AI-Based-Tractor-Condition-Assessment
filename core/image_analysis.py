import os, base64, json, re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from core.config import OPENROUTER_API_KEY, BASE_URL, VISION_MODEL, SLOT_LABELS

llm = ChatOpenAI(
    model=VISION_MODEL,
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY,
    temperature=0,
    max_retries=3,
    timeout=60,
)

# har angle par kaunse parts dekhne hain
SLOT_FOCUS = {
    "front": "headlights, grille, bonnet, bumper or front weights, front tyres",
    "rear": "rear lights, hitch or drawbar, PTO shaft cover, mudguards, rear tyres",
    "left": "left side body panels, fuel tank, steps, mudguard, left tyres",
    "right": "right side body panels, exhaust, steps, mudguard, right tyres",
    "engine": "engine bay, hoses, belts, battery, radiator, visible oil or coolant leaks, rust",
    "tyres": "tread depth, cracks, sidewall damage, uneven wear, rims",
    "cabin": "seat, steering wheel, pedals, dashboard, levers, glass, canopy",
    "hourmeter": "hour meter display, dashboard gauges, whether the reading is clearly visible",
}

PROMPT_TEMPLATE = """Tum tractor inspector ho. Ye photo tractor ke "{label}" angle ki hai.
Is angle par ye parts dekho: {focus}.

SIRF JSON do, koi extra text nahi:
{
  "summary": "4-5 line Hinglish summary",
  "visibility": 80,
  "findings": [
    {"part": "tyre", "issue": "rust/crack/wear/dent/leak/missing", "severity": "low|medium|high"}
  ]
}

Rules:
- visibility = 0 se 100 number (photo se kitna clearly inspect ho paya).
- Sirf wahi findings likho jo photo mein clearly dikhe.
- "missing" tabhi likho jab part ki jagah clearly khali ya toota hui dikhe. Agar angle ya dhundhli photo ki wajah se part nahi dikh raha, missing mat likho, summary mein likho ki wo part visible nahi tha.
- Kuch nahi dikha toh findings khali list rakho."""


def _parse_json(text):
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"summary": text, "visibility": 50, "findings": []}


def analyze_image(path, slot_key):
    label = SLOT_LABELS.get(slot_key, slot_key)
    focus = SLOT_FOCUS.get(slot_key, "overall condition")
    prompt = PROMPT_TEMPLATE.replace("{label}", label).replace("{focus}", focus)

    ext = os.path.splitext(path)[1].lower().replace(".", "")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    msg = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
    ])
    data = _parse_json(llm.invoke([msg]).content)

    data.setdefault("summary", "")
    data.setdefault("visibility", 50)
    data.setdefault("findings", [])
    return data