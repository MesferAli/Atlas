"""GLM-4 LLM Integration - ChatGLM-4 model for SQL generation."""

import asyncio
import os
import re
from typing import Any

from atlas.agent.sql_agent import BaseLLM


class GLM4LLM(BaseLLM):
    """
    LLM provider using THUDM's GLM-4 model for NL-to-SQL generation.

    Supports both API-based access (via OpenAI-compatible endpoint) and
    local model loading via transformers. Bilingual Arabic/English.
    """

    SYSTEM_PROMPT = (
        "أنت خبير في Oracle SQL. مهمتك كتابة استعلام SQL.\n"
        "You are an Oracle SQL Expert. Write a SQL query.\n\n"
        "القواعد / Rules:\n"
        "- اكتب فقط استعلامات SELECT\n"
        "- Write ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)\n"
        "- Use proper Oracle SQL syntax\n"
        "- Return only the SQL query, no explanations\n\n"
        "الجداول المتاحة / Available Tables:\n"
        "{schema_context}\n\n"
        "سؤال المستخدم / User Question: {question}\n\n"
        "SQL Query:"
    )

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        model_name: str = "glm-4",
        max_tokens: int = 256,
        temperature: float = 0.1,
    ) -> None:
        """
        Initialize GLM-4 LLM.

        Args:
            api_key: ZhipuAI API key (or ZHIPUAI_API_KEY env var)
            api_base: API base URL (or ZHIPUAI_API_BASE env var)
            model_name: Model name to use (e.g. glm-4, glm-4-plus)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY", "")
        self.api_base = api_base or os.getenv(
            "ZHIPUAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4"
        )
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None
        self._loaded = False
        self._inference_lock = asyncio.Lock()

    def load_model(self) -> None:
        """Initialize the API client."""
        if self._loaded:
            return

        if not self.api_key:
            raise RuntimeError(
                "GLM-4 API key not set. Set ZHIPUAI_API_KEY environment variable."
            )

        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
            )
            self._loaded = True
            print(f"GLM-4 client initialized (model: {self.model_name})")
        except ImportError:
            raise RuntimeError(
                "openai package not installed. Install with: pip install openai"
            )

    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from model response."""
        response = re.sub(r"```sql\s*", "", response)
        response = re.sub(r"```\s*", "", response)

        match = re.search(
            r"(SELECT\s+.+?)(?:;|$)",
            response,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            sql = match.group(1).strip()
            sql = re.sub(r"\s+", " ", sql)
            return sql

        return response.strip()

    async def generate(self, prompt: str) -> str:
        """
        Generate SQL using GLM-4 API.

        Args:
            prompt: The formatted prompt with schema context and question

        Returns:
            Generated SQL query
        """
        if not self._loaded:
            self.load_model()

        async with self._inference_lock:
            return await self._generate_locked(prompt)

    async def _generate_locked(self, prompt: str) -> str:
        """Run inference via the GLM-4 API."""
        loop = asyncio.get_event_loop()

        def _call_api() -> str:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an Oracle SQL expert. Write only SELECT queries. "
                            "Return only the SQL, no explanations."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""

        raw = await loop.run_in_executor(None, _call_api)
        return self._extract_sql(raw)

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the GLM-4 model configuration."""
        return {
            "model_type": f"GLM-4 ({self.model_name})",
            "loaded": self._loaded,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_base": self.api_base,
        }


def create_glm4_llm(
    api_key: str | None = None,
    fallback_to_mock: bool = True,
) -> BaseLLM:
    """
    Factory function to create a GLM-4 LLM with optional fallback.

    Args:
        api_key: ZhipuAI API key
        fallback_to_mock: If True, return MockLLM when GLM-4 unavailable

    Returns:
        GLM4LLM or MockLLM instance
    """
    try:
        llm = GLM4LLM(api_key=api_key)
        llm.load_model()
        return llm
    except Exception as e:
        if fallback_to_mock:
            print(f"GLM-4 unavailable ({e}), falling back to MockLLM")
            from atlas.agent.sql_agent import MockLLM

            return MockLLM()
        raise
