import json
import os
from unittest.mock import patch

import yaml

from lunaclaw.core.config import load_config


def test_load_default_config(tmp_path):
    # Isolate from real user configs
    with (
        patch("lunaclaw.core.config.CLAUDE_CONFIG_DIR", tmp_path / "no_claude"),
        patch("lunaclaw.core.config.CLAW_CONFIG_DIR", tmp_path / "no_claw"),
        patch("lunaclaw.core.config.LUNACLAW_USER_DIR", tmp_path / "no_luna"),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("ANTHROPIC_MODEL", None)
        config = load_config(project_dir=tmp_path)
    assert config.model == "claude-sonnet-4-6"
    assert config.rag.chunk_size == 512
    assert config.memory.data_dir == "~/.lunaclaw/memory"
    assert config.audit.enabled is False
    assert config.planner.auto is True


def test_env_var_overrides_model(tmp_path):
    with patch.dict(os.environ, {"ANTHROPIC_MODEL": "qwen3.6-plus"}):
        config = load_config(project_dir=tmp_path)
    assert config.model == "qwen3.6-plus"


def test_claude_settings_model(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings = {"model": "claude-opus-4-6"}
    (claude_dir / "settings.json").write_text(json.dumps(settings))

    with patch("lunaclaw.core.config.CLAUDE_CONFIG_DIR", claude_dir):
        config = load_config(project_dir=tmp_path)
    assert config.model == "claude-opus-4-6"


def test_claude_settings_env_block(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings = {
        "env": {
            "ANTHROPIC_BASE_URL": "https://custom.api.com",
            "ANTHROPIC_API_KEY": "test-key",
        }
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings))

    with patch("lunaclaw.core.config.CLAUDE_CONFIG_DIR", claude_dir):
        config = load_config(project_dir=tmp_path)
    assert config.env.get("ANTHROPIC_BASE_URL") == "https://custom.api.com"
    assert config.env.get("ANTHROPIC_API_KEY") == "test-key"


def test_lunaclaw_user_config_overrides(tmp_path):
    luna_dir = tmp_path / ".lunaclaw"
    luna_dir.mkdir()
    user_config = {"model": "my-custom-model", "rag": {"chunk_size": 1024}}
    (luna_dir / "config.yaml").write_text(yaml.dump(user_config))

    with patch("lunaclaw.core.config.LUNACLAW_USER_DIR", luna_dir):
        config = load_config(project_dir=tmp_path)
    assert config.model == "my-custom-model"
    assert config.rag.chunk_size == 1024
    assert config.rag.chunk_overlap == 50  # default preserved


def test_project_config_overrides(tmp_path):
    project_config = {"model": "project-model"}
    (tmp_path / ".lunaclaw.yaml").write_text(yaml.dump(project_config))

    config = load_config(project_dir=tmp_path)
    assert config.model == "project-model"


def test_mcp_servers_from_claude_config(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings = {
        "mcpServers": {
            "brave": {
                "command": "npx",
                "args": ["-y", "@anthropic/brave-mcp"],
            }
        }
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings))

    with patch("lunaclaw.core.config.CLAUDE_CONFIG_DIR", claude_dir):
        config = load_config(project_dir=tmp_path)
    assert "brave" in config.mcp_servers
    assert config.mcp_servers["brave"]["command"] == "npx"
