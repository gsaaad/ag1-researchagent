import os
import logging
from dotenv import load_dotenv
load_dotenv()
import signal
if os.name == 'nt':
    # Added 'SIGTSTP' to the list of signals to patch
    for sig in ('SIGHUP', 'SIGQUIT', 'SIGUSR1', 'SIGUSR2', 'SIGSTP', 'SIGTSTP', 'SIGINT', 'SIGCONT'):
        if not hasattr(signal, sig):
            setattr(signal, sig, signal.SIGTERM)

from crewai import Agent, Task, Crew
from crewai.tools import tool

# --- Best Practice: Configure Logging ---
# A basic logging setup helps in debugging and tracking the crew's execution.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- Set up your API Key ---
# For production, it's recommended to use a more secure method for key management
# like environment variables loaded at runtime or a secret manager.
#
# Set the environment variable for your chosen LLM provider (e.g., OPENAI_API_KEY)
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"
# os.environ["OPENAI_MODEL_NAME"] = "gpt-4o"
# --- 1. Refactored Tool: Returns Clean Data ---
# The tool now returns raw data (a float) or raises a standard Pythonerror.
# This makes it more reusable and forces the agent to handle outcomesproperly.
@tool("Stock Price Lookup Tool")
def get_stock_price(ticker: str) -> float:
    """
    Fetches the latest real-time stock price for a given stock ticker symbol using Yahoo Finance.
    Returns the price as a float. Raises a ValueError if the ticker is not found or API fails.
    """
    import yfinance as yf
    logging.info(f"Tool Call: get_stock_price for ticker '{ticker}'")
    
    try:
        stock = yf.Ticker(ticker)
        # fast_info is often faster/more reliable for current price than .info
        price = stock.fast_info.last_price
        
        if price is None:
             # Fallback to regular info if fast_info fails
            price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')

        if price is None:
            raise ValueError(f"Could not retrieve price for ticker '{ticker.upper()}'.")
            
        return float(price)
    except Exception as e:
        raise ValueError(f"Error fetching price for '{ticker.upper()}': {str(e)}")

# --- 2. Define the Agent ---
# The agent definition remains the same, but it will now leverage theimproved tool.
financial_analyst_agent = Agent(role='Senior Financial Analyst',goal='Analyze stock data using provided tools and report keyprices.',backstory="You are an experienced financial analyst adept at usingdata sources to find stock information. You provide clear, directanswers.",verbose=True,tools=[get_stock_price], allow_delegation=False)# Allowing delegation can be useful, but is not necessary for this simple task.allow_delegation=False,)
# --- 3. Refined Task: Clearer Instructions and Error Handling ---
# The task description is more specific and guides the agent on how to react
# to both successful data retrieval and potential errors.
analyze_aapl_task = Task(description=("What is the current simulated stock price for Apple (ticker:AAPL)? ""Use the 'Stock Price Lookup Tool' to find it. ""If the ticker is not found, you must report that you wereunable to retrieve the price."),expected_output=("A single, clear sentence stating the simulated stock price forAAPL. ""For example: 'The simulated stock price for AAPL is $178.15.' ""If the price cannot be found, state that clearly."),agent=financial_analyst_agent,)
# --- 4. Formulate the Crew ---
# The crew orchestrates how the agent and task work together.
financial_crew = Crew(
    agents=[financial_analyst_agent],
    tasks=[analyze_aapl_task],
    verbose=True,
    # Add this to disable the telemetry upload attempt
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    } if os.environ.get("OPENAI_API_KEY") else None,
)
# --- 5. Run the Crew within a Main Execution Block ---

# Using a __name__ == "__main__": block is a standard Python best practice.
def main():
    """Main function to run the crew."""
    # Check for API key before starting to avoid runtime errors.
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: The OPENAI_API_KEY environment variable is not set.")
        print("Please set it before running the script.")
        return
    print("\n## Starting the Financial Crew...")
    print("---------------------------------")
    # The kickoff method starts the execution.
    result = financial_crew.kickoff()
    print("\n---------------------------------")
    print("## Crew execution finished.")
    print("\nFinal Result:\n", result)
if __name__ == "__main__":
    main()
