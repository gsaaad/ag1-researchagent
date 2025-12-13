# Copyright (c) 2025
# Licensed under the MIT License
"""
Research Assistant Agent Configuration
LangChain agent with ReAct reasoning and tool integration
"""

from typing import List, Callable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

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
    
    def __init__(self, tools: List, callback_handler: Callable = None):
        """
        Initialize the research agent
        
        Args:
            tools: List of LangChain tools
            callback_handler: Optional callback for streaming responses
        """
        self.tools = tools
        self.callback_handler = callback_handler
        
        # Initialize LLM with streaming support
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.7,
            streaming=True,
            callbacks=[callback_handler] if callback_handler else None
        )
        
        # Create memory for conversation context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
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

Previous conversation:
{chat_history}

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
            memory=self.memory,
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
            result = self.agent_executor.invoke({"input": query})
            logger.info(f"Query completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "output": f"I encountered an error: {str(e)}",
                "intermediate_steps": []
            }
    
    def clear_memory(self):
        """Clear conversation history"""
        self.memory.clear()
        logger.info("Memory cleared")
