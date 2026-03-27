from app.models.schemas import NLUResult

def detect_intent_and_crop(text: str) -> NLUResult:
    t = text.lower()
    intent = "general"
    crop: str | None = None

    # crop detection (Standardized to English for DB consistency)
    if any(w in t for w in ["gehu", "wheat"]):
        crop = "wheat"
    elif any(w in t for w in ["dhaan", "rice", "chawal"]):
        crop = "rice"
    elif any(w in t for w in ["tamatar", "tomato"]):
        crop = "tomato"
    elif any(w in t for w in ["sarson", "mustard"]):
        crop = "mustard"

    # intent detection
    if any(w in t for w in ["khaad", "fertilizer", "urvarak"]):
        intent = "fertilizer"
    elif any(w in t for w in ["bimari", "rog", "disease", "daag", "spot", "lakshan"]):
        intent = "disease"
    elif any(w in t for w in ["paani", "sinchai", "irrigation", "water"]):
        intent = "water"
    elif any(w in t for w in ["daam", "bhav", "mandi", "price"]):
        intent = "price"

    return NLUResult(intent=intent, crop=crop)
