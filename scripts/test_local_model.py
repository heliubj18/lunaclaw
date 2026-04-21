#!/usr/bin/env python3
"""Test lunaclaw's LLM provider against a local model server.

Usage:
    # Default: llama.cpp at 192.168.1.73:8003
    python scripts/test_local_model.py

    # Custom server:
    python scripts/test_local_model.py --base-url http://localhost:11434/v1 --model openai/llama3
"""

import argparse
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lunaclaw.core.config import Config
from lunaclaw.llm.provider import LLMProvider
from lunaclaw.audit.tracer import TraceContext


async def test_provider(base_url: str, model: str, api_key: str):
    print(f"Testing lunaclaw LLM provider")
    print(f"  Server:  {base_url}")
    print(f"  Model:   {model}")
    print()

    config = Config(model=model)
    config.env = {
        "OPENAI_API_KEY": api_key,
        "OPENAI_BASE_URL": base_url,
    }
    provider = LLMProvider(config)
    trace = TraceContext()

    print("Sending request... (may take a while for reasoning models)")
    try:
        response = await provider.complete(
            messages=[
                {"role": "system", "content": "Answer very briefly in one sentence."},
                {"role": "user", "content": "What is Python?"},
            ],
            tools=[],
            trace=trace,
        )

        print(f"\nResponse:")
        print(f"  Content: {response.content}")
        print(f"  Usage:   {response.usage}")
        print(f"  Trace:   {len(trace.events)} events")
        print(f"\n{trace.summary()}")

        if response.content:
            print("\n[OK] Provider works with local model!")
        else:
            print("\n[WARN] Empty content — model may need more max_tokens (reasoning model?)")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Test lunaclaw with a local model server")
    parser.add_argument(
        "--base-url",
        default="http://192.168.1.73:8003/v1",
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--model",
        default="openai/Qwopus-GLM-18B-Merged-Q4_K_M.gguf",
        help="Model name (prefix with openai/ for litellm routing)",
    )
    parser.add_argument(
        "--api-key",
        default="not-needed",
        help="API key (default: not-needed for local servers)",
    )
    args = parser.parse_args()

    asyncio.run(test_provider(args.base_url, args.model, args.api_key))


if __name__ == "__main__":
    main()
