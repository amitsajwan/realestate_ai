import asyncio
import os
from dotenv import load_dotenv; load_dotenv()
# Lazy imports to avoid optional dependency errors at import time
Agent = Runner = OpenAIChatCompletionsModel = set_default_openai_client = set_tracing_disabled = None  # type: ignore
AsyncOpenAI = MCPServerStdio = None  # type: ignore


async def create_agent(server):
    global Agent, Runner, OpenAIChatCompletionsModel, set_default_openai_client, set_tracing_disabled, AsyncOpenAI
    if Agent is None:
        from agents import (
            Agent as _Agent,
            Runner as _Runner,
            OpenAIChatCompletionsModel as _OpenAIChatCompletionsModel,
            set_default_openai_client as _set_default_openai_client,
            set_tracing_disabled as _set_tracing_disabled,
        )
        from openai import AsyncOpenAI as _AsyncOpenAI
        Agent, Runner, OpenAIChatCompletionsModel = _Agent, _Runner, _OpenAIChatCompletionsModel
        set_default_openai_client, set_tracing_disabled = _set_default_openai_client, _set_tracing_disabled
        AsyncOpenAI = _AsyncOpenAI
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    set_default_openai_client(client)
    set_tracing_disabled(True)

    return Agent(
        name="Playwright MCP Agent",
        instructions="You control a browser via the Playwright MCP server. Be precise and deterministic.",
        model=OpenAIChatCompletionsModel(model=os.getenv("MODEL", "gemini-2.0-flash"), openai_client=client),
        mcp_servers=[server],
    )


async def main():
    global MCPServerStdio
    if MCPServerStdio is None:
        from agents.mcp import MCPServerStdio as _MCPServerStdio
        MCPServerStdio = _MCPServerStdio
    mcp_args = ["-y", "@playwright/mcp@latest", "--output-dir", "./mcp_artifacts"]
    cdp = os.getenv("MCP_CDP_ENDPOINT")
    if cdp:
        mcp_args += ["--cdp-endpoint", cdp]

    async with MCPServerStdio(name="Playwright MCP", params={"command": "npx", "args": mcp_args}) as server:
        agent = await create_agent(server)
        while True:
            try:
                req = input("Your request -> ")
            except EOFError:
                break
            if req.strip().lower() in {"exit", "quit"}:
                break
            out = await Runner.run(agent, input=req)
            print(f"Output ->\n{out.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())
