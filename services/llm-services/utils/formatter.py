MAX_USER_CHARS = 1200
MAX_CONTEXT_CHARS = 1800

def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    return text[:limit]

def build_prompt(user_message, intent, entities, context_data):
    system = (
        "You are an agriculture expert. Reply in simple Hinglish. "
        "If unsure, ask ONE concise clarifying question."
    )

    user_message = _truncate(user_message, MAX_USER_CHARS)
    context_data = _truncate(context_data, MAX_CONTEXT_CHARS)

    user_block = (
        f"User Query: {user_message}\n"
        f"Intent: {intent}\n"
        f"Entities: {entities}\n"
        f"Context: {context_data}\n"
    )

    constraints = (
        "Constraints:\n"
        "- Short, practical steps\n"
        "- No hallucination\n"
        "- If context insufficient, ask clarification\n"
        "- End with ONE next action for farmer"
    )

    return {"system": system, "user": user_block + constraints}