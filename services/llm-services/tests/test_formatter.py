from utils.formatter import build_prompt
def test_prompt_contains_intent():
    p = build_prompt("leaf yellow", "disease query", {"crop": "wheat"}, "soil pH 6.5")
    assert "disease query" in p['user']