from backend import detect_intent

# (message, history_length, expected intent)
tests = [
    ("just decide for me", 0, "ai_dependency"),
    ("just decide for me", 3, "ai_dependency"),
    ("I had a rough day at work", 0, "empathy"),
    ("just decide for me, should I take the job in Boston?", 0, "ai_dependency"),
    ("should I take my pills tonight", 0, "medical_ethics"),
    ("should I take ibuprofen", 0, "medical_ethics"),
    ("should I take 400mg", 0, "medical_ethics"),
    ("tell me what to do about my medication", 0, "medical_ethics"),
    ("tell me what to do, I want to kill myself", 0, "crisis"),
    ("should I take a course of antibiotics", 0, "medical_ethics"),
    ("should I take the course on data science", 0, "empathy"),
    ("should I take the job or my pills", 0, "medical_ethics"),
    ("I can't wait to kill this exam tomorrow", 0, "empathy"),
]

for text, history_length, expected in tests:
    actual = detect_intent(text, history_length)
    result = "PASS" if actual == expected else "FAIL"
    print(f"{result}  {actual:<18} (expected {expected:<15}) <- {text} [history={history_length}]")
