"""
Condition Checker Agent with Google ADK
Demonstrates a LoopAgent that repeatedly processes steps until a condition is met.
Use case: Polling, iterative processing, retry logic, state-based workflows.
"""

import asyncio
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# --- Configuration ---
GEMINI_MODEL = "gemini-2.0-flash-exp"
APP_NAME = "condition_checker_app"
USER_ID = "user_123"
SESSION_ID = "session_condition"

# Progress settings (used by both simple and LLM loops)
TARGET_PROGRESS = 100  # Target percentage to reach
INCREMENT_AMOUNT = 17   # Progress increment per iteration (100/5 = 20 iterations)


# --- Custom Agent: Condition Checker ---
class ConditionChecker(BaseAgent):
    """
    A custom agent that checks session state for completion.
    If 'progress' reaches the target, it escalates to stop the loop.
    """
    
    name: str = "ConditionChecker"
    description: str = "Checks if the process is complete and signals the loop to stop."
    target_progress: int = TARGET_PROGRESS  # Use module constant

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Check state and yield event to continue or stop the loop."""
        
        # Get current progress from session state
        progress = context.session.state.get("progress", 0)
        iteration = context.session.state.get("iteration", 0)
        
        print(f"   🔍 ConditionChecker: Progress = {progress}%, Iteration = {iteration}")
        
        if progress >= self.target_progress:
            # ✅ Condition met - escalate to terminate the loop
            print(f"   ✅ Target reached! Escalating to stop loop.")
            content = types.Content(
                role="model",
                parts=[types.Part(text=f"🎯 Process complete! Final progress: {progress}%")]
            )
            yield Event(
                author=self.name,
                content=content,
                actions=EventActions(escalate=True)
            )
        else:
            # ⏳ Continue the loop
            remaining = self.target_progress - progress
            content = types.Content(
                role="model",
                parts=[types.Part(text=f"Progress: {progress}% | Remaining: {remaining}%")]
            )
            yield Event(author=self.name, content=content)


# --- Custom Agent: Progress Incrementer ---
class ProgressIncrementer(BaseAgent):
    """
    A custom agent that simulates work by incrementing progress.
    In real scenarios, this could be an LLM agent doing actual processing.
    """
    
    name: str = "ProgressIncrementer"
    description: str = "Performs work and updates progress in session state."
    increment_amount: int = INCREMENT_AMOUNT  # Use module constant

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Simulate work and update progress."""
        
        # Get current state
        current_progress = context.session.state.get("progress", 0)
        iteration = context.session.state.get("iteration", 0)
        
        # Increment progress
        new_progress = min(current_progress + self.increment_amount, 100)
        new_iteration = iteration + 1
        
        # Update session state
        context.session.state["progress"] = new_progress
        context.session.state["iteration"] = new_iteration
        
        print(f"   ⚙️  ProgressIncrementer: {current_progress}% → {new_progress}% (iteration {new_iteration})")
        
        # Yield status event
        content = types.Content(
            role="model",
            parts=[types.Part(text=f"Completed iteration {new_iteration}, progress now at {new_progress}%")]
        )
        yield Event(author=self.name, content=content)


# --- Define the Loop Agent ---
# The LoopAgent runs sub-agents repeatedly until escalation or max_iterations
status_poller = LoopAgent(
    name="StatusPoller",
    description="Repeatedly processes steps until completion condition is met.",
    max_iterations=TARGET_PROGRESS // INCREMENT_AMOUNT + 2,  # 100/5 = 20 iterations + buffer
    sub_agents=[
        ProgressIncrementer(),  # First: do work
        ConditionChecker(),      # Then: check if done
    ],
)

# Root agent for the runner
root_agent = status_poller


# --- Runner Setup ---
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# --- Agent Invocation Logic ---
async def run_condition_loop(task_description: str):
    """Execute the condition-based loop workflow."""
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Condition-Based Loop")
    print(f"📋 Task: {task_description}")
    print(f"🎯 Target: 100% progress")
    print(f"{'='*60}\n")

    try:
        content = types.Content(role="user", parts=[types.Part(text=task_description)])
        
        # Suppress warnings
        import warnings
        warnings.filterwarnings("ignore", message=".*non-text parts.*")
        
        final_result = ""
        
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content,
        ):
            # Capture content from events
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_result = part.text
            
            # Check for escalation (loop termination)
            if hasattr(event, "actions") and event.actions:
                if hasattr(event.actions, "escalate") and event.actions.escalate:
                    print(f"\n🛑 Loop terminated via escalation")
                    break

        # Get final state
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )
        
        print(f"\n{'='*60}")
        print(f"📊 Final Results:")
        print(f"   Progress: {session.state.get('progress', 0)}%")
        print(f"   Iterations: {session.state.get('iteration', 0)}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# --- Alternative: LLM-Based Processing Step ---
async def run_llm_condition_loop():
    """
    Alternative version using an LLM agent for processing.
    The LLM decides when to mark the task as complete.
    """
    
    # Create a fresh session for this demo
    llm_session_id = "session_llm_loop"
    
    # LLM-based processor that can decide completion
    llm_processor = LlmAgent(
        name="LLMProcessor",
        model=GEMINI_MODEL,
        description="Processes tasks step by step.",
        instruction=f"""You are a task processor working through a multi-step process.

Each iteration, you:
1. Report what step you're working on (Step N of {TARGET_PROGRESS // INCREMENT_AMOUNT})
2. Describe briefly what you accomplished
3. Update the progress percentage (each step adds {INCREMENT_AMOUNT}%)

Progress increases by {INCREMENT_AMOUNT}% each step until reaching {TARGET_PROGRESS}%.
Example: Step 1 = {INCREMENT_AMOUNT}%, Step 2 = {INCREMENT_AMOUNT * 2}%, etc.

When you reach {TARGET_PROGRESS}%, say "TASK COMPLETE" clearly.
Keep responses concise (2-3 sentences max).""",
    )
    
    # Custom checker for LLM output
    class LLMOutputChecker(BaseAgent):
        name: str = "LLMOutputChecker"
        description: str = "Checks if LLM indicated completion."
        
        async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
            iteration = context.session.state.get("llm_iteration", 0) + 1
            context.session.state["llm_iteration"] = iteration
            
            print(f"   🔍 Checking iteration {iteration}...")
            
            # Check if we've done enough iterations (simulating completion detection)
            if iteration >= TARGET_PROGRESS // INCREMENT_AMOUNT:
                print(f"   ✅ Process complete after {iteration} iterations!")
                content = types.Content(
                    role="model",
                    parts=[types.Part(text="Process completed successfully!")]
                )
                yield Event(author=self.name, content=content, actions=EventActions(escalate=True))
            else:
                content = types.Content(
                    role="model", 
                    parts=[types.Part(text=f"Iteration {iteration} done, continuing...")]
                )
                yield Event(author=self.name, content=content)
    
    llm_loop = LoopAgent(
        name="LLMProcessingLoop",
        max_iterations=TARGET_PROGRESS // INCREMENT_AMOUNT + 2,  # Allow some buffer
        sub_agents=[llm_processor, LLMOutputChecker()],
    )
    
    # Create runner for LLM loop
    llm_runner = Runner(
        agent=llm_loop,
        app_name=APP_NAME,
        session_service=session_service,
    )
    
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=llm_session_id,
    )
    
    print(f"\n{'='*60}")
    print(f"🤖 Starting LLM-Based Processing Loop")
    print(f"{'='*60}\n")
    
    content = types.Content(role="user", parts=[types.Part(text="Process this task step by step")])
    
    import warnings
    warnings.filterwarnings("ignore")
    
    async for event in llm_runner.run_async(
        user_id=USER_ID,
        session_id=llm_session_id,
        new_message=content,
    ):
        if hasattr(event, "content") and event.content:
            if hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text and len(part.text) > 20:
                        print(f"   📝 {event.author}: {part.text[:100]}...")
    
    print(f"\n{'='*60}")
    print(f"✅ LLM Processing Loop Complete!")
    print(f"{'='*60}\n")


# --- Main Entry Point ---
async def main():
    """Run demonstration of condition-based looping."""
    
    print("\n" + "🔄"*30)
    print("  CONDITION CHECKER AGENT DEMO")
    print("🔄"*30 + "\n")
    
    # Create session with initial state
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={"progress": 0, "iteration": 0},  # Initial state
    )
    print("✅ Session created with initial state\n")
    
    # Run the simple progress-based loop
    await run_condition_loop("Process data until completion")
    
    # Optionally run the LLM-based version
    print("\n" + "-"*60)
    print("Running LLM-based alternative...")
    print("-"*60)
    await run_llm_condition_loop()


if __name__ == "__main__":
    asyncio.run(main())