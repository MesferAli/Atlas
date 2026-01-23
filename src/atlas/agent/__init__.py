from .sql_agent import BaseLLM, MockLLM, OracleSQLAgent

__all__ = ["OracleSQLAgent", "BaseLLM", "MockLLM"]

# Conditional import for UnslothLLM (requires GPU)
try:
    from .unsloth_llm import (  # noqa: F401
        UnslothLLM,
        create_unsloth_llm,
    )

    __all__.extend(["UnslothLLM", "create_unsloth_llm"])
except ImportError:
    pass  # Unsloth not available
