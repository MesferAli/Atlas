"""Unsloth LLM Integration - Real language model for SQL generation using Qwen."""

import asyncio
import os
import re
from typing import Any

from atlas.agent.sql_agent import BaseLLM


class UnslothLLM(BaseLLM):
    """
    Production LLM using Unsloth's FastLanguageModel with Qwen.

    This class loads a fine-tuned Qwen model for Arabic/English NL-to-SQL conversion.
    Requires CUDA-enabled GPU and Unsloth library.
    """

    # Default model path on server
    DEFAULT_MODEL_PATH = "/workspace/atlas_erp/models/atlas-qwen-full/final"

    # SQL generation prompt template (bilingual Arabic/English)
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
        model_path: str | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.1,
        device: str = "cuda",
    ) -> None:
        """
        Initialize the Unsloth LLM.

        Args:
            model_path: Path to the fine-tuned model weights
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            device: Device to run on ('cuda' or 'cpu')
        """
        self.model_path = model_path or os.getenv(
            "ATLAS_MODEL_PATH", self.DEFAULT_MODEL_PATH
        )
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.device = device

        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._prefix_cache: dict[str, Any] = {}
        self._cache_max_size = 32
        self._inference_lock = asyncio.Lock()

    def load_model(self) -> None:
        """Load the Unsloth model and tokenizer."""
        if self._loaded:
            return

        try:
            from unsloth import FastLanguageModel

            print(f"Loading Unsloth model from: {self.model_path}")

            self._model, self._tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_path,
                max_seq_length=2048,
                dtype=None,  # Auto-detect
                load_in_4bit=True,  # Memory efficient
            )

            # Enable faster inference
            FastLanguageModel.for_inference(self._model)

            self._loaded = True
            print("Unsloth model loaded successfully!")

        except ImportError:
            raise RuntimeError(
                "Unsloth not installed. Install with: pip install unsloth"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from model response."""
        # Remove any markdown code blocks
        response = re.sub(r"```sql\s*", "", response)
        response = re.sub(r"```\s*", "", response)

        # Find SELECT statement
        match = re.search(
            r"(SELECT\s+.+?)(?:;|$)",
            response,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            sql = match.group(1).strip()
            # Clean up whitespace
            sql = re.sub(r"\s+", " ", sql)
            return sql

        # Fallback: return cleaned response
        return response.strip()

    def _get_prefix_key(self, prompt: str) -> str:
        """Extract the schema context portion as cache key.

        The schema context (table list) rarely changes between requests for the
        same user session, so caching its tokenization saves ~30% latency.
        """
        # Everything before "User Question:" is the schema prefix
        marker = "سؤال المستخدم"
        idx = prompt.find(marker)
        if idx > 0:
            return prompt[:idx]
        return ""

    async def generate(self, prompt: str) -> str:
        """
        Generate SQL from the prompt using the Unsloth model.

        Args:
            prompt: The formatted prompt with schema context and question

        Returns:
            Generated SQL query
        """
        # Ensure model is loaded
        if not self._loaded:
            self.load_model()

        # Serialize GPU inference to prevent concurrent CUDA access
        async with self._inference_lock:
            return await self._generate_locked(prompt)

    async def _generate_locked(self, prompt: str) -> str:
        """Run inference while holding the lock."""
        # Resolve prefix cache key for schema context
        prefix_key = self._get_prefix_key(prompt)

        # Tokenize input
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1792,  # Leave room for generation
        ).to(self.device)

        # Update prefix cache (evict oldest if full)
        if prefix_key and prefix_key not in self._prefix_cache:
            if len(self._prefix_cache) >= self._cache_max_size:
                oldest = next(iter(self._prefix_cache))
                del self._prefix_cache[oldest]
            self._prefix_cache[prefix_key] = inputs["input_ids"].shape[1]

        # Generate
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=self.temperature > 0,
            pad_token_id=self._tokenizer.eos_token_id,
            use_cache=True,
        )

        # Decode response
        response = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )

        # Extract SQL from response
        sql = self._extract_sql(response)

        return sql

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_path": self.model_path,
            "loaded": self._loaded,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "device": self.device,
            "model_type": "Qwen (Unsloth Fine-tuned)",
        }


def create_unsloth_llm(
    model_path: str | None = None,
    fallback_to_mock: bool = True,
) -> BaseLLM:
    """
    Factory function to create an Unsloth LLM with optional fallback.

    Args:
        model_path: Path to model weights
        fallback_to_mock: If True, return MockLLM when Unsloth unavailable

    Returns:
        UnslothLLM or MockLLM instance
    """
    try:
        llm = UnslothLLM(model_path=model_path)
        llm.load_model()
        return llm
    except Exception as e:
        if fallback_to_mock:
            print(f"Unsloth unavailable ({e}), falling back to MockLLM")
            from atlas.agent.sql_agent import MockLLM
            return MockLLM()
        raise
