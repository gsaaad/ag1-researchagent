# Copyright (c) 2025
# Licensed under the MIT License
"""
Test script for research assistant (console mode)
Run this to test the agent without GUI
"""

import os
from dotenv import load_dotenv
from research_tools import create_tools
from research_agent import ResearchAgent

# Load environment
load_dotenv()

def test_agent():
    """Test the research agent in console mode"""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n❌ ERROR: GOOGLE_API_KEY not found!")
        print("Please create a .env file with your Google API key\n")
        return
    
    print("\n" + "="*60)
    print("Research Assistant - Console Test")
    print("="*60 + "\n")
    
    # Create tools and agent
    print("Initializing tools...")
    tools = create_tools()
    print(f"✓ Created {len(tools)} tools: {[t.name for t in tools]}\n")
    
    print("Initializing agent...")
    agent = ResearchAgent(tools=tools)
    print("✓ Agent ready\n")
    
    # Test queries
    test_queries = [
        "What is 25 * 37?",
        "Search for the latest news about artificial intelligence",
        "What is the capital of France according to Wikipedia?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print('='*60 + "\n")
        
        try:
            result = agent.run(query)
            print(f"\nFinal Answer: {result['output']}\n")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
        
        input("Press Enter to continue...")
    
    print("\n" + "="*60)
    print("Testing Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    test_agent()
