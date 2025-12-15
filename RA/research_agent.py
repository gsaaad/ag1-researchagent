# Copyright (c) 2025
# Licensed under the MIT License
"""
Research Assistant Agent Configuration
LangChain agent with ReAct reasoning and tool integration
"""

from typing import List, Callable, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import logging
import os

# Load environment variables
load_dotenv()

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    LangChain-based research assistant agent with tool integration
    """
    
    def __init__(self, tools: List, callback_handler: Optional[Callable] = None):
        """
        Initialize the research agent
        
        Args:
            tools: List of LangChain tools
            callback_handler: Optional callback for streaming responses
        """
        self.tools = tools
        self.callback_handler = callback_handler
        self.chat_history = []  # Manual chat history management
        
        # Initialize LLM with streaming support
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.7,
            streaming=True,
            callbacks=[callback_handler] if callback_handler else None
        )
        
        # Define the ReAct prompt template
        self.prompt = PromptTemplate.from_template(
            """You are a highly capable research assistant with access to multiple tools.
Your goal is to help users find information, perform calculations, and manage files.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        # Create the ReAct agent
        self.agent = create_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            return_intermediate_steps=True
        )
        
        logger.info("Research agent initialized successfully")
    
    def run(self, query: str) -> dict:
        """
        Execute the agent with a query
        
        Args:
            query: User's research question
            
        Returns:
            dict with 'output' and 'intermediate_steps'
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Execute the agent
            result = self.agent_executor.invoke({"input": query})
            
            # Store in chat history
            self.chat_history.append({
                "query": query,
                "response": result.get("output", "")
            })
            
            logger.info(f"Query completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "output": f"I encountered an error: {str(e)}",
                "intermediate_steps": []
            }
    
    def clear_memory(self):
        """Clear conversation history"""
        self.chat_history = []
        logger.info("Memory cleared")
