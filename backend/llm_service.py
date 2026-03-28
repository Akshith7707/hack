from openai import AsyncOpenAI
import asyncio
import os

# Featherless.ai configuration
BASE_URL = "https://api.featherless.ai/v1"
API_KEY = "rc_8cad9e3f8bfc3ff04770f0c6889e3c4af225d4b6aa2dfba34e8fd9b3e21adf4a"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
MAX_TOKENS = 1024
TIMEOUT_SECONDS = 60  # Increased from 30 to handle longer inputs

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)


class LLMTimeoutError(Exception):
    """Raised when LLM call times out"""
    pass


class LLMError(Exception):
    """Raised when LLM call fails"""
    pass


async def call_llm(system_prompt: str, user_message: str, timeout: int = TIMEOUT_SECONDS) -> str:
    """
    Async wrapper for LLM calls to Featherless.ai with timeout
    Raises LLMTimeoutError if call takes too long
    Raises LLMError on other failures
    """
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            ),
            timeout=timeout
        )
        return response.choices[0].message.content.strip()
    except asyncio.TimeoutError:
        raise LLMTimeoutError(f"LLM call timed out after {timeout} seconds")
    except Exception as e:
        raise LLMError(f"LLM call failed: {str(e)}")


async def call_llm_with_retry(system_prompt: str, user_message: str, 
                               max_retries: int = 2, timeout: int = TIMEOUT_SECONDS) -> str:
    """
    LLM call with retry logic - retries on timeout or error
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await call_llm(system_prompt, user_message, timeout)
        except (LLMTimeoutError, LLMError) as e:
            last_error = e
            if attempt < max_retries:
                await asyncio.sleep(1)  # Brief pause before retry
                continue
            break
    
    # All retries failed
    raise last_error or LLMError("LLM call failed after retries")


def call_llm_sync(prompt: str) -> str:
    """
    Synchronous LLM call (for drift detection and simple queries)
    Uses asyncio to run the async call
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(call_llm("You are a helpful assistant.", prompt))
    except Exception as e:
        return f"Error: {str(e)}"
