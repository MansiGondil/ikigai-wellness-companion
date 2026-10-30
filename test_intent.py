from backend import detect_intent

tests = [
    "just decide for me",
    "tell me what to do, I want to kill myself",
    "tell me what to do about my medication",
    "I had a rough day at work",
]

for t in tests:
    print(f"{detect_intent(t):<18} <- {t}")
    print(detect_intent("just decide for me", history_length=3))