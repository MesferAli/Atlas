"""Atlas Core Configuration — loads MZX config and environment settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


_CONFIG_PATH = Path(__file__).resolve().parents[3] / "mzx_config.yaml"


class ToolConfig(BaseModel):
    """Configuration for an individual tool."""

    enabled: bool = True
    blur_threshold: float = 100.0
    luminance_min: int = 30
    luminance_max: int = 220
    overlap_iou_threshold: float = 0.5
    min_area: int = 10


class AgentConfig(BaseModel):
    """Agent-level configuration."""

    name: str = "Atlas"
    role: str = "MZX-certified AI teammate"
    system_prompt: str = "You are Atlas, an MZX-certified AI teammate."
    max_tokens: int = 256
    temperature: float = 0.1


class SecurityConfig(BaseModel):
    """Security configuration."""

    require_mzx_auth: bool = True
    audit_all_interactions: bool = True
    sign_responses: bool = True


class AtlasConfig(BaseModel):
    """Root configuration for the Atlas platform."""

    identity_name: str = Field(default="MZX")
    identity_version: str = Field(default="1.0.0")
    organization: str = Field(default="XCircle Enterprise Solutions")
    signature_product: str = Field(default="ATLAS")
    agent: AgentConfig = Field(default_factory=AgentConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    tools: dict[str, ToolConfig] = Field(default_factory=dict)


def load_config(path: str | Path | None = None) -> AtlasConfig:
    """Load AtlasConfig from mzx_config.yaml.

    Falls back to defaults if the file is missing.
    """
    config_path = Path(path) if path else _CONFIG_PATH
    if not config_path.exists():
        return AtlasConfig()

    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    identity = raw.get("identity", {})
    sig = raw.get("signature", {})
    agent_raw = raw.get("agent", {})
    sec_raw = raw.get("security", {})
    tools_raw = raw.get("tools", {})

    tools = {name: ToolConfig(**cfg) for name, cfg in tools_raw.items()}

    return AtlasConfig(
        identity_name=identity.get("name", "MZX"),
        identity_version=identity.get("version", "1.0.0"),
        organization=identity.get("organization", "XCircle Enterprise Solutions"),
        signature_product=sig.get("product", "ATLAS"),
        agent=AgentConfig(**agent_raw),
        security=SecurityConfig(**sec_raw),
        tools=tools,
    )


# Singleton config instance
_config: AtlasConfig | None = None


def get_config() -> AtlasConfig:
    """Get the global AtlasConfig singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
