import asyncio
import getpass
import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool as langchain_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

# Prompt the user securely if missing.
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

try:
    # A model with function/tool calling capabilities is required.
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    print(f"✅ Language model initialized: {llm.model}")
except Exception as e:
    llm = None
    print(f"🛑 Error initializing language model: {e}")
# --- Define a Tool ---
@langchain_tool
def search_information(query: str) -> str:
    """
    Provides factual information on a given topic. Use this tool to
    find answers to phrases
    like 'capital of France' or 'weather in London?'.
    """
    print(f"\n--- 🛠️ Tool Called: search_information with query: '{query}' ---")

    normalized = re.sub(r"[^a-z0-9\s]", "", query.lower()).strip()

    # Simulated search results.
    if "capital" in normalized and "france" in normalized:
        result = "The capital of France is Paris."
    elif "weather" in normalized and "london" in normalized:
        result = "The weather in London is currently cloudy with a temperature of 15°C."
    elif "population" in normalized and "earth" in normalized:
        result = "The estimated population of Earth is around 8 billion people."
    elif "tallest" in normalized and "mountain" in normalized:
        result = "Mount Everest is the tallest mountain above sea level."
    else:
        result = f"Simulated search result for '{query}': No specific information found, but the topic seems interesting."

    print(f"--- TOOL RESULT: {result} ---")
    return result
tools = [search_information]

# --- Create a Tool-Calling Agent (LangGraph) ---
agent = None
if llm is not None:
    # LangGraph is the recommended runtime for agents in modern LangChain.
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="You are a helpful assistant. Use tools when needed to answer factual questions.",
    )
async def run_agent_with_tool(query: str):
    """Invokes the agent executor with a query and prints the final
    response."""
    print(f"\n--- 🏃 Running Agent with Query: '{query}' ---")
    try:
        if agent is None:
            raise RuntimeError("Agent was not initialized (LLM init failed).")

        response = await agent.ainvoke({"messages": [HumanMessage(content=query)]})
        final_message = response["messages"][-1]
        print("\n--- ✅ Final Agent Response ---")
        print(final_message.content)
    except Exception as e:
        print(f"\n🛑 An error occurred during agent execution: {e}")
async def main():

    """Runs all agent queries concurrently."""
    tasks = [
    run_agent_with_tool("What is the capital of France?"),
    run_agent_with_tool("What's the weather like in London?"),
    run_agent_with_tool("Tell me something about dogs.") 
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())