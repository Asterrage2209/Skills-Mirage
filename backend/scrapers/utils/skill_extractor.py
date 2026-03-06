AI_KEYWORDS = [
    "chatgpt",
    "openai",
    "generative ai",
    "machine learning",
    "automation",
    "llm",
    "gpt",
    "ai tools",
]


def detect_ai_mentions(text):
    text = text.lower()

    found = []

    for word in AI_KEYWORDS:
        if word in text:
            found.append(word)

    return found
