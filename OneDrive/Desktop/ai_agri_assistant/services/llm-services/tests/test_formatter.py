from utils.formatter import build_prompt
def test_prompt_contains_intent():
    p = build_prompt("leaf yellow", "disease query", {"crop": "wheat"}, "soil pH 6.5")
    assert "disease query" in p['user']


def test_prompt_contains_entities_and_context():
    p = build_prompt(
        "leaf yellow",
        "disease",
        {"crop": "wheat"},
        "soil pH 6.5"
    )

    user = p["user"]

    assert "wheat" in user
    assert "soil pH 6.5" in user
    assert "Constraints:" in user
