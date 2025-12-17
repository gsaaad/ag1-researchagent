import asyncio
import os
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.tools import google_search  # ✅ Changed from enterprise_web_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

# --- Application Constants ---
APP_NAME = "google_search_app"
USER_ID = "user_123"
SESSION_ID = "session_456"

# --- Session Service ---
session_service = InMemorySessionService()

# --- Agent Definition ---
search_agent = LlmAgent(
    name="google_search_agent",
    description="Answers questions using Google Search.",
    model="gemini-2.0-flash-exp",
    instruction=(
        "You are a helpful assistant with access to Google Search. "
        "Use the search tool to find accurate, up-to-date information. "
        "Always cite your sources when providing answers."
    ),
    tools=[google_search],  # ✅ Use google_search instead
)

# --- Runner Initialization ---
runner = Runner(
    agent=search_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

# --- Agent Invocation Logic ---
async def call_search_agent_async(query: str):
    """Runs a query through the search agent."""
    print(f"\n{'='*60}")
    print(f"User: {query}")
    print(f"{'='*60}")
    print("Agent: ", end="", flush=True)
    
    try:
        content = types.Content(role='user', parts=[types.Part(text=query)])
        
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            # Stream the text response
            if hasattr(event, 'content_part_delta') and event.content_part_delta:
                print(event.content_part_delta.text, end="", flush=True)
            
            # Handle final response
            if event.is_final_response():
                print()  # Newline after streaming
                
                # Check for grounding metadata (sources)
                if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
                    gm = event.grounding_metadata
                    # Try different possible attribute names based on SDK version
                    sources = (
                        getattr(gm, 'grounding_chunks', None) or
                        getattr(gm, 'grounding_supports', None) or
                        getattr(gm, 'search_entry_point', None) or
                        getattr(gm, 'web_search_queries', None)
                    )
                    if sources:
                        print(f"\n📚 Grounding info found")
                        # If it's web_search_queries (list of strings)
                        if isinstance(sources, list) and sources and isinstance(sources[0], str):
                            print(f"  Search queries: {sources}")
                        # If it's grounding_chunks or similar
                        elif isinstance(sources, list):
                            for i, chunk in enumerate(sources[:3], 1):
                                if hasattr(chunk, 'web') and chunk.web:
                                    print(f"  {i}. {chunk.web.uri}")
                                elif hasattr(chunk, 'uri'):
                                    print(f"  {i}. {chunk.uri}")
                    else:
                        # Just show that grounding metadata exists
                        print(f"\n📚 Grounding metadata present (type: {type(gm).__name__})")
                else:
                    print("\n(No grounding metadata found)")
                
                print("-" * 60)

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("-" * 60)

# --- Run Example ---
async def run_search_example():
    # ✅ Create the session FIRST
    print(f"Creating session: {SESSION_ID}")
    session_service.create_session_sync(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print("✅ Session created successfully\n")
    
    # Now run queries
    await call_search_agent_async("What are the latest developments in quantum computing?")
    await call_search_agent_async("Explain the current state of AI safety research.")
    await call_search_agent_async("What is the capital of France?")

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable is not set.")
        print("Please add it to your .env file.")
    else:
        try:
            asyncio.run(run_search_example())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                print("⚠️  Skipping execution (already in event loop).")
            else:
                raise e