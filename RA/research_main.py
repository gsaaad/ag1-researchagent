# Copyright (c) 2025
# Licensed under the MIT License
"""
Research Assistant - Main Entry Point
Run this file to launch the research assistant with GUI
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Import our modules
from research_tools import create_tools
from research_agent import ResearchAgent
from research_gui import launch_gui

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Research Assistant Starting")
    logger.info("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not found in environment")
        print("\n❌ ERROR: GOOGLE_API_KEY not found!")
        print("Please create a .env file with your Google API key:")
        print("GOOGLE_API_KEY=your_api_key_here\n")
        sys.exit(1)
    
    try:
        # Create tools
        logger.info("Initializing tools...")
        tools = create_tools()
        logger.info(f"Created {len(tools)} tools: {[t.name for t in tools]}")
        
        # Create agent
        logger.info("Initializing research agent...")
        agent = ResearchAgent(tools=tools)
        logger.info("Agent initialized successfully")
        
        # Launch GUI
        logger.info("Launching GUI...")
        launch_gui(agent)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
