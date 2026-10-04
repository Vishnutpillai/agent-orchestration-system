import os
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Add it to your .env file."
    )


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)


def get_llm():
    return client


def chat_completion(
    messages,
    temperature=0.2,
    max_tokens=512,
    **kwargs,
):
    """
    Centralized Groq completion helper.

    Automatically retries temporary 429 rate-limit errors.
    """

    max_retries = 3

    for attempt in range(max_retries):

        try:

            return client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

        except RateLimitError as exc:

            if attempt == max_retries - 1:
                raise

            wait_time = 6 * (attempt + 1)

            print(
                f"Groq rate limit reached. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


def generate_response(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
) -> str:

    response = chat_completion(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=512,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "LLM returned an empty response."
        )

    return content