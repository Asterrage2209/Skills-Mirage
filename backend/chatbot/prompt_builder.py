def build_prompt(query):
    worker = query.get("worker_profile")

    question = query.get("question")

    prompt = f"""
    Worker Profile:
    {worker}

    Question:
    {question}

    Answer using labour market insights.
    """

    return prompt
