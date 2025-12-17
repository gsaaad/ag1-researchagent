"""
Greeter Agent with Google ADK
Demonstrates a coordinator agent with sub-agents for greeting and task execution.
"""

import asyncio
import random
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# --- Configuration ---
GEMINI_MODEL = "gemini-2.0-flash-exp"
APP_NAME = "greeter_app"
USER_ID = "user_123"
SESSION_ID = "session_456"


# --- Custom Agent: Task Executor ---
class TaskExecutor(BaseAgent):
    """A specialized agent with custom, non-LLM behavior."""

    name: str = "TaskExecutor"
    description: str = "Executes predefined tasks like calculations or lookups."

    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """Custom implementation logic for the task."""
        # Extract the user's request from context if available
        task_description = "default task"
        if context.user_content and context.user_content.parts:
            task_description = context.user_content.parts[0].text

        # Simulate task execution
        result_text = f"✅ Task completed: '{task_description}' was processed successfully."
        
        # Create proper Content object for the Event
        content = types.Content(
            role="model",
            parts=[types.Part(text=result_text)]
        )
        
        yield Event(author=self.name, content=content)


# --- Greeter Personality Styles ---
GREETER_PERSONALITIES = [
    # 🎉 Excited Greeter
    """You are an INCREDIBLY excited greeter! You're bursting with energy and enthusiasm!
Use exclamation marks liberally!! Add emojis where appropriate 🎉✨🌟
Express genuine joy at meeting the user. Be upbeat and energetic!
Example vibe: "OH WOW, HELLO THERE!! 🎉 SO thrilled to meet you! This is AMAZING!"
Keep responses short but FULL of energy!""",

    # 🧑 Human/Casual Greeter
    """You are a casual, human-like greeter. Talk like a friendly neighbor or coworker.
Use contractions (you're, it's, gonna). Maybe a little slang.
Be warm but not over the top. Natural conversation style.
Example vibe: "Hey! How's it going? Nice to see ya. What can I do for you today?"
Keep it real and relatable.""",

    # 👔 Professional/Executive Greeter
    """You are a polished, professional executive greeter. Think corporate concierge.
Use formal language. Be courteous and respectful.
Maintain professionalism while still being warm.
Example vibe: "Good day. Welcome. How may I be of assistance to you today?"
Keep responses dignified and articulate.""",

    # 😎 Chill Greeter
    """You are a super chill, laid-back greeter. Very relaxed vibes.
Use casual language, maybe some "dude", "no worries", "all good" type phrases.
Nothing stresses you out. Everything is cool.
Example vibe: "Heyyy, what's up? Welcome, welcome. Take your time, no rush."
Keep it mellow and easygoing.""",
]


def get_random_personality() -> str:
    """Select a random greeter personality for variety."""
    return random.choice(GREETER_PERSONALITIES)


# --- Define Sub-Agents ---
greeter = LlmAgent(
    name="Greeter",
    model=GEMINI_MODEL,
    description="A greeter with varying personality styles.",
    instruction=get_random_personality(),  # Gets a random personality at startup
)

task_executor = TaskExecutor()


# --- Define Coordinator Agent ---
coordinator = LlmAgent(
    name="Coordinator",
    model=GEMINI_MODEL,
    description="A coordinator that delegates to specialized sub-agents.",
    instruction=(
        "You are a helpful coordinator assistant. Based on the user's request:\n\n"
        "1. For greetings (hello, hi, hey, good morning, etc.) → delegate to 'Greeter'\n"
        "2. For task execution requests (backup, run, execute, process, etc.) → delegate to 'TaskExecutor'\n"
        "3. For questions about your capabilities or general help → Answer DIRECTLY yourself:\n"
        "   - You can greet users warmly (via Greeter)\n"
        "   - You can execute tasks (via TaskExecutor)\n"
        "   - You can answer general questions\n\n"
        "Always respond helpfully. When answering directly, provide clear and useful information."
    ),
    sub_agents=[greeter, task_executor],
)

# The ADK framework assigns root_agent for the runner
root_agent = coordinator


# --- Runner Setup ---
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# --- Agent Invocation Logic ---
async def chat_with_agent(query: str):
    """Send a message to the coordinator and print the response."""
    
    # 🎲 Refresh greeter's personality for each interaction
    new_personality = get_random_personality()
    greeter.instruction = new_personality
    
    # Show which personality was selected (optional - for demo)
    personality_names = ["🎉 Excited", "🧑 Casual/Human", "👔 Professional", "😎 Chill"]
    personality_index = GREETER_PERSONALITIES.index(new_personality)
    print(f"\n[Greeter Mode: {personality_names[personality_index]}]")
    
    print(f"\n{'='*60}")
    print(f"👤 User: {query}")
    print(f"{'='*60}")
    print("🤖 Agent: ", end="", flush=True)

    try:
        content = types.Content(role="user", parts=[types.Part(text=query)])
        full_response = ""
        
        # Suppress the SDK warning about non-text parts
        import warnings
        warnings.filterwarnings("ignore", message=".*non-text parts.*")

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content,
        ):
            # Stream text delta (streaming responses)
            if hasattr(event, "content_part_delta") and event.content_part_delta:
                if hasattr(event.content_part_delta, "text") and event.content_part_delta.text:
                    print(event.content_part_delta.text, end="", flush=True)
                    full_response += event.content_part_delta.text

            # Handle complete content in event (for sub-agent responses)
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            # Avoid duplicating streamed content
                            if part.text not in full_response:
                                print(part.text, end="", flush=True)
                                full_response += part.text

            # Handle final response
            if hasattr(event, "is_final_response") and event.is_final_response():
                pass  # Just continue, we'll print newline after loop

        # Print newline and separator
        if not full_response.strip():
            print("I can help you with greetings and task execution. Just say hello or ask me to run a task!")
        print()
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# --- Main Entry Point ---
async def main():
    """Run example interactions with the coordinator agent."""
    # Create session first (using async method)
    print("🚀 Initializing Greeter Agent System...")
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    print("✅ Session created\n")

    # Example interactions
    await chat_with_agent("Hello! How are you today?")
    await chat_with_agent("Can you execute a data backup task for me?")
    await chat_with_agent("What can you help me with?")


if __name__ == "__main__":
    asyncio.run(main())
