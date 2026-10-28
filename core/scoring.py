from core.config import SLOT_LABELS

SEVERITY_POINTS = {"low": 1, "medium": 3, "high": 6}
EXPECTED_PHOTOS = len(SLOT_LABELS)


def _num(value, default=50):
    try:
        return max(0, min(100, float(value)))
    except Exception:
        return default


def merge_findings(analyses):
    """Same part + issue ek baar, jiski severity zyada ho wo rakho.
    Evidence mein wo saari photos jodo jahan se finding aayi."""
    best = {}
    for a in analyses:
        label = a.get("slot_label", "Photo")
        path = a.get("path")
        for f in a.get("findings", []):
            part = str(f.get("part", "unknown")).lower().strip()
            issue = str(f.get("issue", "unknown")).lower().strip()
            sev = str(f.get("severity", "low")).lower().strip()
            if sev not in SEVERITY_POINTS:
                sev = "low"

            key = (part, issue)
            if key not in best:
                best[key] = {"part": part, "issue": issue, "severity": sev, "evidence": []}
            entry = best[key]

            if SEVERITY_POINTS[sev] > SEVERITY_POINTS[entry["severity"]]:
                entry["severity"] = sev
            if not any(e["label"] == label for e in entry["evidence"]):
                entry["evidence"].append({"label": label, "path": path})
    return list(best.values())


def score_tractor(analyses):
    findings = merge_findings(analyses)

    penalty = sum(SEVERITY_POINTS[f["severity"]] for f in findings)
    score = max(0, 100 - penalty * 4)

    if score >= 85: grade = "A"
    elif score >= 70: grade = "B"
    elif score >= 50: grade = "C"
    else: grade = "D"

    # coverage = kitne alag angles (slots) sahi mile
    covered_keys = {a.get("slot") for a in analyses if a.get("slot")}
    covered_slots = [label for key, label in SLOT_LABELS.items() if key in covered_keys]
    missing_slots = [label for key, label in SLOT_LABELS.items() if key not in covered_keys]

    coverage = len(covered_keys) / EXPECTED_PHOTOS
    avg_vis = (sum(_num(a.get("visibility")) for a in analyses) / len(analyses) / 100) if analyses else 0
    confidence = round((0.6 * coverage + 0.4 * avg_vis) * 100)

    if confidence >= 75: label = "High"
    elif confidence >= 50: label = "Medium"
    else: label = "Low"

    return {
        "score": score,
        "grade": grade,
        "confidence": confidence,
        "confidence_label": label,
        "findings": findings,
        "photos_used": len(analyses),
        "covered_slots": covered_slots,
        "missing_slots": missing_slots,
        "reliable": coverage >= 0.5,   # 8 mein se kam se kam 4 angles
    }