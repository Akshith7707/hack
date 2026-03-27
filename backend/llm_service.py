from openai import AsyncOpenAI
import os

# Featherless.ai configuration
BASE_URL = "https://api.featherless.ai/v1"
API_KEY = "rc_8cad9e3f8bfc3ff04770f0c6889e3c4af225d4b6aa2dfba34e8fd9b3e21adf4a"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
MAX_TOKENS = 1024

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)


async def call_llm(system_prompt: str, user_message: str) -> str:
    """
    Async wrapper for LLM calls to Featherless.ai
    Returns the response text or an error message
    """
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM Error: {str(e)}]"
