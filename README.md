# Lunaclaw

A simple, powerful CLI agent assistant with RAG, MCP, memory, and audit tracing.

Lunaclaw is a general-purpose CLI agent that works with any LLM provider — Anthropic, OpenAI, local models (Ollama, vLLM, llama.cpp), or third-party Anthropic-compatible services (Alibaba Cloud, Doubao, etc.). It reads your existing Claude Code configuration so there's zero setup if you already use Claude Code.

## Features

- **Single agent + planner subagent** — keeps it simple, extensible when needed
- **14 built-in tools** — shell, file ops (read/write/edit/glob/grep), web search, web fetch, RAG, MCP, memory
- **Claude Code compatible config** — reads `~/.claude/settings.json` and env vars directly
- **Any LLM provider** — Anthropic, OpenAI, Bedrock, Vertex, DashScope, Doubao, DeepSeek, Ollama, vLLM, llama.cpp
- **RAG** — index your documents, search with embeddings (ChromaDB + sentence-transformers)
- **MCP integration** — connects to MCP servers from your Claude Code config
- **Memory** — persistent file-based memory across sessions
- **Audit tracing** — structured JSON call chain logs for debugging

## Quick Start

```bash
# Install
uv venv && uv pip install -e .

# With RAG support (optional)
uv pip install -e ".[rag]"

# Run
lunaclaw
```

## Model Configuration

Lunaclaw uses environment variables for model configuration, same as Claude Code. No provider registry — just set the right env vars.

### Cloud Providers

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY=sk-xxx
lunaclaw  # uses claude-sonnet-4-6 by default

# OpenAI
export OPENAI_API_KEY=sk-xxx
# set model in ~/.lunaclaw/config.yaml: model: "gpt-4o"

# AWS Bedrock
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_REGION_NAME=us-east-1
# model: "bedrock/anthropic.claude-sonnet-4-6-v1"

# Google Vertex
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
export VERTEX_PROJECT=your-project
export VERTEX_LOCATION=us-central1
# model: "vertex_ai/claude-sonnet-4-6@20250514"
```

### Third-Party Anthropic-Compatible

```bash
# Alibaba Cloud (DashScope)
export ANTHROPIC_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export ANTHROPIC_API_KEY=your-dashscope-key
export ANTHROPIC_MODEL=qwen-plus

# Doubao (Volcengine)
export ANTHROPIC_AUTH_TOKEN=your-ark-key
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
export ANTHROPIC_MODEL=your-endpoint-id

# DeepSeek
export OPENAI_API_KEY=your-deepseek-key
export OPENAI_BASE_URL=https://api.deepseek.com/v1
# model: "openai/deepseek-chat"
```

### Local Model Servers

Any OpenAI-compatible server works. Prefix model names with `openai/` for litellm routing.

```bash
# Ollama
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
# model: "openai/llama3"

# vLLM
export OPENAI_API_KEY=token-abc123
export OPENAI_BASE_URL=http://localhost:8000/v1
# model: "openai/your-model-name"

# llama.cpp server
export OPENAI_API_KEY=not-needed
export OPENAI_BASE_URL=http://localhost:8080/v1
# model: "openai/local-model"

# LM Studio
export OPENAI_API_KEY=lm-studio
export OPENAI_BASE_URL=http://localhost:1234/v1
# model: "openai/your-loaded-model"
```

## Configuration

Lunaclaw reads config from multiple sources (later overrides earlier):

1. `config/default.yaml` — built-in defaults
2. `~/.claude/settings.json` — Claude Code config (model, env, mcpServers)
3. `~/.claw/settings.json` — claw-code config
4. `~/.lunaclaw/config.yaml` — lunaclaw user config
5. `./.lunaclaw.yaml` — project-level config
6. Environment variables — `ANTHROPIC_MODEL`, `ANTHROPIC_API_KEY`, etc.

### User Config Example

```yaml
# ~/.lunaclaw/config.yaml
model: "claude-sonnet-4-6"

rag:
  chunk_size: 1024
  data_dir: "~/.lunaclaw/rag"

memory:
  data_dir: "~/.lunaclaw/memory"

audit:
  enabled: true
  log_dir: "~/.lunaclaw/audit"

planner:
  auto: true
  threshold: 3
```

## Built-in Tools

| Tool | Description | Approval Required |
|------|-------------|:-:|
| `shell` | Execute shell commands | Yes |
| `file_read` | Read file contents | No |
| `file_write` | Write/create files | Yes |
| `file_edit` | String replacement in files | Yes |
| `glob` | Find files by pattern | No |
| `grep` | Search file contents by regex | No |
| `web_search` | Search the web (DuckDuckGo) | No |
| `web_fetch` | Fetch and extract URL content | No |
| `rag_search` | Search indexed knowledge base | No |
| `rag_ingest` | Index documents into RAG | No |
| `memory_read` | Read stored memories | No |
| `memory_write` | Store new memories | No |
| `memory_search` | Search memories | No |
| `mcp__*` | MCP server tools (auto-discovered) | Configurable |

## MCP Integration

Lunaclaw reads MCP server definitions from your Claude Code config (`~/.claude/settings.json`). Any `mcpServers` entries are automatically connected and their tools are registered.

```json
{
  "mcpServers": {
    "brave": {
      "command": "npx",
      "args": ["-y", "@anthropic/brave-mcp"]
    }
  }
}
```

## Architecture

```
lunaclaw/
├── core/          # Agent loop, planner subagent, config, events, context
├── llm/           # LiteLLM provider adapter
├── tools/         # All 14 built-in tools
├── rag/           # Adapter interfaces + ChromaDB/sentence-transformers
├── mcp/           # JSON-RPC client + registry
├── memory/        # Adapter interface + file-based store
├── audit/         # TraceContext + AuditLogger
└── interfaces/    # Rich CLI REPL
```

### Adapter Pattern

RAG, memory, and MCP use abstract interfaces so backends are swappable:

- **EmbeddingProvider** — default: sentence-transformers
- **VectorStore** — default: ChromaDB
- **MemoryStore** — default: file-based JSON
- **McpTransport** — default: stdio (subprocess)

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev,rag]"

# Run tests
pytest -v

# Lint
ruff check lunaclaw/ tests/

# Format
ruff format lunaclaw/ tests/
```

## License

See [LICENSE](LICENSE) for details.
