GENERAL_LIMITATIONS = [
    "Engine ki internal health (piston, compression, oil quality) photos se pata nahi chal sakti.",
    "Gearbox, transmission, clutch aur brakes ka working condition photo se nahi dikhta.",
    "Hydraulic system ka pressure aur leak behaviour sirf photo se confirm nahi hota.",
    "Undercarriage aur chassis ke neeche ka hidden rust ya damage photo angle par depend karta hai.",
    "Hour meter ki reading photo se verify nahi hoti, meter tampering ho sakti hai.",
    "Electrical system, battery aur starting condition photo se nahi jaanch sakte.",
    "Photo quality, light aur angle ki wajah se AI ke findings adhoore ya galat ho sakte hain.",
]

RECOMMENDATION = (
    "Kharidne ya repair ka decision lene se pehle qualified mechanic se physical inspection "
    "zaroor karwao: engine test run, hydraulic test, gearbox aur clutch check, aur service history verify karo."
)


def _num(value, default=100):
    try:
        return float(value)
    except Exception:
        return default


def build_limitations(analyses, missing_slots, confidence):
    specific = []

    if missing_slots:
        specific.append(
            "Is inspection mein ye angles cover nahi hue (photo nahi mili ya reject hui), "
            "isliye inka assessment nahi hua: " + ", ".join(missing_slots)
        )

    for a in analyses:
        vis = _num(a.get("visibility"))
        if vis < 60:
            specific.append(
                f"{a.get('slot_label', 'Photo')} photo mein visibility kam thi ({int(vis)}%), "
                "us angle ke findings adhoore ho sakte hain."
            )

    if confidence < 50:
        specific.append(f"Overall confidence {confidence}% hai, isliye grade sirf indicative hai.")

    return {
        "specific": specific,
        "general": GENERAL_LIMITATIONS,
        "recommendation": RECOMMENDATION,
    }