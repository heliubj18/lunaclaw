from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from lunaclaw.core.agent import AgentLoop
from lunaclaw.core.config import Config, load_config
from lunaclaw.llm.provider import LLMProvider
from lunaclaw.memory.index import MemoryIndex
from lunaclaw.memory.store import FileMemoryStore
from lunaclaw.tools.file_ops import FileEditTool, FileReadTool, FileWriteTool, GlobTool, GrepTool
from lunaclaw.tools.mcp import McpTool
from lunaclaw.tools.memory import MemoryReadTool, MemorySearchTool, MemoryWriteTool
from lunaclaw.tools.registry import ToolRegistry
from lunaclaw.tools.shell import ShellTool
from lunaclaw.tools.web_fetch import WebFetchTool
from lunaclaw.tools.web_search import WebSearchTool


console = Console()


async def _approve_tool(name: str, params: dict) -> bool:
    """Ask user to approve a tool execution."""
    console.print(f"\n[yellow]Tool requires approval:[/yellow] {name}")
    console.print(f"  Params: {params}")
    answer = Prompt.ask("  Allow?", choices=["y", "n"], default="y")
    return answer.lower() == "y"


def _build_registry(config: Config, memory_store: FileMemoryStore) -> ToolRegistry:
    registry = ToolRegistry()
    # File operations
    registry.register(FileReadTool())
    registry.register(FileWriteTool())
    registry.register(FileEditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
    # Shell
    registry.register(ShellTool())
    # Web
    registry.register(WebSearchTool())
    registry.register(WebFetchTool())
    # Memory
    registry.register(MemoryReadTool(memory_store))
    registry.register(MemoryWriteTool(memory_store))
    registry.register(MemorySearchTool(memory_store))
    # RAG (optional — only if chromadb + sentence-transformers installed)
    try:
        import logging
        import os as _os
        import warnings

        # Suppress noisy HuggingFace/sentence-transformers warnings during init
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
        _os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        _os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from lunaclaw.rag.embeddings import SentenceTransformerEmbedding
            from lunaclaw.rag.store import ChromaVectorStore
            from lunaclaw.rag.engine import RAGEngine
            from lunaclaw.tools.rag import RAGSearchTool, RAGIngestTool

            rag_dir = Path(config.rag.data_dir).expanduser()
            embedding = SentenceTransformerEmbedding()
            store = ChromaVectorStore(persist_dir=str(rag_dir / "chroma"))
            engine = RAGEngine(
                embedding=embedding,
                store=store,
                chunk_size=config.rag.chunk_size,
                chunk_overlap=config.rag.chunk_overlap,
            )
            registry.register(RAGSearchTool(engine))
            registry.register(RAGIngestTool(engine))
    except ImportError:
        pass  # RAG extras not installed
    except Exception:
        pass  # RAG init failed (e.g. no network for model download)
    return registry


async def _setup_mcp(config: Config, registry: ToolRegistry) -> None:
    """Connect to configured MCP servers and register their tools."""
    from lunaclaw.mcp.client import StdioTransport
    from lunaclaw.mcp.registry import McpRegistry

    if not config.mcp_servers:
        return

    mcp_registry = McpRegistry()
    for name, server_config in config.mcp_servers.items():
        command = server_config.get("command")
        args = server_config.get("args", [])
        if not command:
            continue
        try:
            transport = StdioTransport(command=command, args=args)
            await mcp_registry.add_server(name, transport)
            for tool_schema in mcp_registry.list_tools():
                if tool_schema["name"].startswith(f"mcp__{name}__"):
                    registry.register(
                        McpTool(
                            name=tool_schema["name"],
                            description=tool_schema["description"],
                            parameters=tool_schema["parameters"],
                            registry=mcp_registry,
                        )
                    )
            console.print(f"  [green]Connected to MCP server:[/green] {name}")
        except Exception as e:
            console.print(f"  [red]Failed to connect MCP server {name}:[/red] {e}")


async def run_repl(model_override: str | None = None) -> None:
    config = load_config()
    if model_override:
        config.model = model_override

    console.print(
        Panel(
            "[bold]Lunaclaw[/bold] — CLI Agent Assistant\n"
            f"Model: {config.model}\n"
            "Type /quit to exit, /clear to reset conversation",
            title="Welcome",
        )
    )

    # Setup memory
    memory_dir = Path(config.memory.data_dir).expanduser()
    memory_store = FileMemoryStore(data_dir=memory_dir)
    memory_index = MemoryIndex(memory_store)

    # Setup tools
    registry = _build_registry(config, memory_store)

    # Setup MCP
    await _setup_mcp(config, registry)

    # Setup agent
    provider = LLMProvider(config)
    agent = AgentLoop(
        config=config,
        provider=provider,
        registry=registry,
    )
    agent.set_approval_callback(_approve_tool)

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]>[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input == "/quit":
            console.print("Goodbye!")
            break

        if user_input == "/clear":
            agent.clear_history()
            console.print("[dim]Conversation cleared[/dim]")
            continue

        # Inject relevant memories
        memory_context = await memory_index.format_for_prompt(user_input)
        agent._memory_context = memory_context

        try:
            with console.status("[bold green]Thinking...[/bold green]"):
                response = await agent.process(user_input)
            console.print()
            console.print(Markdown(response))
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
