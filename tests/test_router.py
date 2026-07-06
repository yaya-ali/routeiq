from app.router import CHEAP, STRONG, choose_model


def test_simple_query_goes_cheap():
    model, _ = choose_model("What time is it in Berlin?")
    assert model == CHEAP


def test_reasoning_goes_strong():
    model, _ = choose_model("Analyze the trade-off between latency and cost step by step.")
    assert model == STRONG


def test_code_goes_strong():
    model, _ = choose_model("Fix this: def add(a, b): return a - b")
    assert model == STRONG


def test_long_prompt_goes_strong():
    model, _ = choose_model("x" * 3000)
    assert model == STRONG
