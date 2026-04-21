from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

CLAUDE_CONFIG_DIR = Path.home() / ".claude"
CLAW_CONFIG_DIR = Path.home() / ".claw"
LUNACLAW_USER_DIR = Path.home() / ".lunaclaw"
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "default.yaml"


class RagConfig(BaseModel):
    embedding_model: str = "local"
    chunk_size: int = 512
    chunk_overlap: int = 50
    data_dir: str = "~/.lunaclaw/rag"


class MemoryConfig(BaseModel):
    data_dir: str = "~/.lunaclaw/memory"


class AuditConfig(BaseModel):
    enabled: bool = False
    log_dir: str = "~/.lunaclaw/audit"
    log_level: str = "full"


class PlannerConfig(BaseModel):
    auto: bool = True
    threshold: int = 3
    model: str | None = None


class Config(BaseModel):
    model: str = "claude-sonnet-4-6"
    rag: RagConfig = Field(default_factory=RagConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    planner: PlannerConfig = Field(default_factory=PlannerConfig)
    mcp_servers: dict[str, Any] = Field(default_factory=dict)
    env: dict[str, str] = Field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(project_dir: Path | None = None) -> Config:
    project_dir = project_dir or Path.cwd()

    # 1. Load defaults
    merged = _load_yaml(DEFAULT_CONFIG_PATH)

    # 2. Read Claude Code settings
    claude_settings = _load_json(CLAUDE_CONFIG_DIR / "settings.json")
    env_block: dict[str, str] = {}

    if claude_model := claude_settings.get("model"):
        merged["model"] = claude_model
    if claude_env := claude_settings.get("env"):
        env_block.update(claude_env)
    if claude_mcp := claude_settings.get("mcpServers"):
        merged.setdefault("mcp_servers", {}).update(claude_mcp)

    # 3. Read claw-code settings
    claw_settings = _load_json(CLAW_CONFIG_DIR / "settings.json")

    if claw_model := claw_settings.get("model"):
        merged["model"] = claw_model
    if claw_env := claw_settings.get("env"):
        env_block.update(claw_env)
    if claw_mcp := claw_settings.get("mcpServers"):
        merged.setdefault("mcp_servers", {}).update(claw_mcp)

    # 4. Lunaclaw user config
    user_config = _load_yaml(LUNACLAW_USER_DIR / "config.yaml")
    merged = _deep_merge(merged, user_config)

    # 5. Lunaclaw project config
    project_config = _load_yaml(project_dir / ".lunaclaw.yaml")
    merged = _deep_merge(merged, project_config)

    # 6. Env var overrides
    if env_model := os.environ.get("ANTHROPIC_MODEL"):
        merged["model"] = env_model

    # Handle null model from default.yaml
    if merged.get("model") is None:
        merged["model"] = "claude-sonnet-4-6"

    # Store env block for provider resolution
    merged["env"] = env_block

    return Config(**merged)
