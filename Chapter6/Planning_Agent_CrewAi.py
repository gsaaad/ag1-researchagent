import os
import signal

# --- Windows Compatibility Shim (MUST BE FIRST) ---
if os.name == 'nt':
    for sig in ('SIGHUP', 'SIGQUIT', 'SIGUSR1', 'SIGUSR2', 'SIGSTP', 'SIGTSTP', 'SIGCONT'):
        if not hasattr(signal, sig):
            setattr(signal, sig, signal.SIGTERM)

# --- Fix for langchain.verbose AttributeError ---
import langchain
if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'debug'):
    langchain.debug = False

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# --- Verify API Key ---
if not os.environ.get("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY environment variable is not set.")
    print("Please add it to your .env file.")
    exit(1)

# 1. Define the language model
llm = ChatOpenAI(model="gpt-4-turbo")

# 2. Define a clear and focused agent
planner_writer_agent = Agent(
    role='Article Planner and Writer',
    goal='Plan and then write a concise, engaging summary on a specified topic.',
    backstory=(
        'You are an expert technical writer and content strategist. '
        'Your strength lies in creating a clear, actionable plan before writing, '
        'ensuring the final summary is both informative and easy to digest.'
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 3. Define a task with a structured expected output
topic = "The importance of Reinforcement Learning in AI"

high_level_task = Task(
    description=(
        f"1. Create a bullet-point plan for a summary on the topic: '{topic}'.\n"
        f"2. Write the summary based on your plan, keeping it around 200 words."
    ),
    expected_output=(
        "A final report containing two distinct sections:\n\n"
        "### Plan\n"
        "- A bulleted list outlining the main points of the summary.\n\n"
        "### Summary\n"
        "- A concise and well-structured summary of the topic."
    ),
    agent=planner_writer_agent,
)

# 4. Create the crew with a clear process
crew = Crew(
    agents=[planner_writer_agent],
    tasks=[high_level_task],
    process=Process.sequential,
    verbose=True
)

# 5. Execute the task
def main():
    print("## Running the planning and writing task ##")
    print("-" * 50)
    result = crew.kickoff()
    print("\n" + "=" * 50)
    print("## Task Result ##")
    print("=" * 50)
    print(result)

if __name__ == "__main__":
    main()