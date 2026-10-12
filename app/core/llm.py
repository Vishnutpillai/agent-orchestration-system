
import os
import time
import random

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it to your .env file."
    )

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
    max_retries=0,
)


def _create_with_retry(**kwargs):
    """Retry Groq rate-limit errors with increasing delays."""
    max_attempts = 4

    for attempt in range(max_attempts):
        try:
            return client.chat.completions.create(**kwargs)

        except RateLimitError:
            if attempt == max_attempts - 1:
                raise

            wait_time = min(20 * (2 ** attempt), 60)
            wait_time += random.randint(0, 5)

            print(
                f"Groq rate limit reached. "
                f"Waiting {wait_time}s before retry "
                f"({attempt + 1}/{max_attempts - 1})..."
            )
            time.sleep(wait_time)


class _CompletionsProxy:
    def create(self, **kwargs):
        return _create_with_retry(**kwargs)


class _ChatProxy:
    def __init__(self):
        self.completions = _CompletionsProxy()


class _LLMProxy:
    def __init__(self):
        self.chat = _ChatProxy()


_shared_llm = _LLMProxy()


def get_llm():
    """Return a shared interface used by all agents."""
    return _shared_llm


def chat_completion(
    messages,
    temperature=0.2,
    max_tokens=512,
    **kwargs,
):
    """Create a completion using the shared retry handler."""
    return _create_with_retry(
        model=GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


def generate_response(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
) -> str:
    response = chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("LLM returned an empty response.")

    return content
