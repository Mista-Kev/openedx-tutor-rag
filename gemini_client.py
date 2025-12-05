import os
import google.generativeai as genai



API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. "
        "Set it in your environment before running the code."
    )

genai.configure(api_key=API_KEY)


MODEL_NAME = "gemini-2.5-flash"


def ask_gemini(question: str, context: str) -> str:

    prompt = f"""You are a helpful assistant answering questions based on the given context.

Context:
{context}

Question:
{question}

Answer in a clear and concise way, using the context where relevant.
If the answer is not in the context, say that explicitly.
"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)


    return response.text
