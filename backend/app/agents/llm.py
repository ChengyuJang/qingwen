from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings

_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
)

MODEL = "deepseek-chat"


async def stream_chat(messages: list[dict]) -> AsyncGenerator[str, None]:
    """调用 DeepSeek，逐 token yield 文本增量。"""
    stream = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        temperature=0.7,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta