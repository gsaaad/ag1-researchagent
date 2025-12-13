# Copyright (c) 2025
# Licensed under the MIT License
"""
Research Assistant Tools Module
Provides web search, Wikipedia, file operations, and calculator tools
"""

from typing import Optional
from langchain.tools import Tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, WikipediaAPIWrapper
import os
import re


class WebSearchTool:
    """Web search using DuckDuckGo"""
    
    def __init__(self):
        self.search = DuckDuckGoSearchAPIWrapper(max_results=5)
    
    def run(self, query: str) -> str:
        """Execute web search"""
        try:
            results = self.search.run(query)
            return f"Web Search Results for '{query}':\n{results}"
        except Exception as e:
            return f"Error performing web search: {str(e)}"


class WikipediaTool:
    """Wikipedia article lookup"""
    
    def __init__(self):
        self.wikipedia = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500)
    
    def run(self, query: str) -> str:
        """Fetch Wikipedia summary"""
        try:
            results = self.wikipedia.run(query)
            return f"Wikipedia Summary for '{query}':\n{results}"
        except Exception as e:
            return f"Error fetching Wikipedia article: {str(e)}"


class FileReadTool:
    """Read text files"""
    
    def run(self, filepath: str) -> str:
        """Read file contents"""
        try:
            if not os.path.exists(filepath):
                return f"Error: File '{filepath}' does not exist"
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"File content from '{filepath}':\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class FileWriteTool:
    """Write text files"""
    
    def run(self, filepath_and_content: str) -> str:
        """
        Write content to file
        Format: filepath|content
        """
        try:
            if '|' not in filepath_and_content:
                return "Error: Format should be 'filepath|content'"
            
            filepath, content = filepath_and_content.split('|', 1)
            filepath = filepath.strip()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to '{filepath}'"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class CalculatorTool:
    """Safe mathematical expression evaluator"""
    
    def run(self, expression: str) -> str:
        """Evaluate mathematical expression"""
        try:
            # Remove any non-mathematical characters for safety
            cleaned = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            
            if not cleaned:
                return "Error: Invalid mathematical expression"
            
            result = eval(cleaned, {"__builtins__": {}}, {})
            return f"Calculation: {expression} = {result}"
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"


def create_tools():
    """Create and return all LangChain tools"""
    
    web_search = WebSearchTool()
    wikipedia = WikipediaTool()
    file_read = FileReadTool()
    file_write = FileWriteTool()
    calculator = CalculatorTool()
    
    tools = [
        Tool(
            name="web_search",
            func=web_search.run,
            description="Useful for searching the internet for current information, news, articles, and general knowledge. Input should be a search query string."
        ),
        Tool(
            name="wikipedia",
            func=wikipedia.run,
            description="Useful for getting detailed information from Wikipedia about historical facts, concepts, people, places, and events. Input should be a topic name or question."
        ),
        Tool(
            name="read_file",
            func=file_read.run,
            description="Reads the contents of a text file. Input should be the complete file path as a string."
        ),
        Tool(
            name="write_file",
            func=file_write.run,
            description="Writes content to a text file. Input format: 'filepath|content' where filepath is the destination and content is what to write."
        ),
        Tool(
            name="calculator",
            func=calculator.run,
            description="Evaluates mathematical expressions. Supports basic operations (+, -, *, /, parentheses). Input should be a mathematical expression like '2 + 2' or '(10 * 5) / 2'."
        ),
    ]
    
    return tools
