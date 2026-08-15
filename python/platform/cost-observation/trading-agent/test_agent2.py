import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from google.adk.runners import InMemoryRunner
from google.genai import types

from trading_agent.agent import mcp_toolset, root_agent

async def run_agent_one_turn(query: str) -> tuple[str, list[str]]:
    runner = InMemoryRunner(agent=root_agent, app_name="trading_agent")
    session = await runner.session_service.create_session(
        app_name="trading_agent", user_id="eval_user"
    )
    message = types.Content(role="user", parts=[types.Part(text=query)])
    final_text = ""
    tool_calls: list[str] = []
    try:
        async for event in runner.run_async(
            user_id="eval_user", session_id=session.id, new_message=message
        ):
            if not (event.content and event.content.parts):
                continue
            for part in event.content.parts:
                if part.function_call and part.function_call.name:
                    tool_calls.append(part.function_call.name)
                if part.text:
                    final_text = part.text
    finally:
        await mcp_toolset.close()
    return final_text, tool_calls

def main():
    query = "Give me a BINANCE 1h market snapshot."
    final_text, tool_calls = asyncio.run(run_agent_one_turn(query))
    print(f"query : {query}")
    print(f"tools : {tool_calls}")
    print(f"reply : {final_text}")

if __name__ == "__main__":
    main()
