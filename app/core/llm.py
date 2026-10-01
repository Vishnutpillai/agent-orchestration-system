from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL


def get_llm():
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Add it to the .env file."
        )

    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0
    )