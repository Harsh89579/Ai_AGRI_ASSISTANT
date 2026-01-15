from pydantic import BaseModel


class NLUResult(BaseModel):
    intent: str
    crop: str | None = None
    language: str = "hi-en"  # abhi simple assumption


def detect_intent_and_crop(text: str) -> NLUResult:
    t = text.lower()

    intent = "general"
    crop: str | None = None

    # crop detection
    if "gehu" in t or "wheat" in t:
        crop = "gehu"
    elif "dhaan" in t or "chawal" in t or "rice" in t:
        crop = "dhaan"
    elif "sarson" in t or "mustard" in t:
        crop = "sarson"

    # intent detection
    if any(w in t for w in ["khaad", "fertilizer", "urvarak"]):
        intent = "fertilizer"
    elif any(w in t for w in ["bimari", "rog", "disease", "daag", "spot"]):
        intent = "disease"
    elif any(w in t for w in ["paani", "sinchai", "irrigation", "water"]):
        intent = "water"
    elif any(w in t for w in ["daam", "bhav", "mandi", "price"]):
        intent = "price"

    # ✅ yahin return karo, dubara function call nahi
    return NLUResult(intent=intent, crop=crop)


    return {
      "intent": result.intent,
      "entities": {
        "crop": result.crop
       }
    }
