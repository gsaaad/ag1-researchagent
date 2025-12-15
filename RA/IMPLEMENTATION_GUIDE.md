# Research Assistant Implementation Guide

## 📁 Project Structure

```
research_main.py          - Main entry point (run this!)
research_agent.py         - LangChain ReAct agent with memory
research_tools.py         - Tool implementations (5 tools)
research_gui.py           - PyQt6 GUI with dual panels
test_research.py          - Console-based testing script
requirements_research.txt - Dependencies
setup_research.bat        - Automated setup script
.env.example             - Environment template
README_RESEARCH.md       - Full documentation
```

## 🚀 Quick Start (3 Steps)

### Option A: Automated Setup (Recommended)
```bash
setup_research.bat
```
This will:
- Check Python installation
- Install all dependencies
- Create logs directory
- Set up .env file

### Option B: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements_research.txt

# 2. Configure environment
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Create logs directory
mkdir logs

# 4. Run the application
python research_main.py
```

## 🧪 Testing

Before running the full GUI, test with console mode:
```bash
python test_research.py
```

This runs 3 basic tests to verify:
- Calculator tool works
- Web search connects properly
- Wikipedia lookup functions

## 🎯 Core Features Implemented

### 1. Tools (research_tools.py)
✅ **WebSearchTool** - DuckDuckGo integration with 5 result limit
✅ **WikipediaTool** - Wikipedia API with smart summaries
✅ **FileReadTool** - Safe file reading with error handling
✅ **FileWriteTool** - File writing with auto-directory creation
✅ **CalculatorTool** - Secure eval with restricted namespace

### 2. Agent (research_agent.py)
✅ **ReAct Pattern** - Reasoning and Acting loop
✅ **Conversation Memory** - Context retention across queries
✅ **Streaming Support** - Real-time response generation
✅ **Error Handling** - Graceful failure recovery
✅ **Logging** - Comprehensive action tracking
✅ **Max 10 Iterations** - Prevents infinite loops

### 3. GUI (research_gui.py)
✅ **Dual Panels** - Chat (60%) + Logs (40%)
✅ **Real-time Streaming** - See tokens as generated
✅ **Color Coding** - Different colors for different actions
✅ **Threading** - Non-blocking UI using QThread
✅ **Memory Management** - Clear button resets conversation
✅ **Status Bar** - Current operation feedback
✅ **Error Dialogs** - User-friendly error messages

## 🏗️ Architecture Details

### Agent Flow
```
User Input → Agent Executor → ReAct Loop → Tools → Response
              ↓
         Conversation Memory (retained for context)
              ↓
         Streaming Callbacks → GUI Updates
```

### Tool Selection Logic
The agent uses the ReAct pattern:
1. **Thought**: Analyze what needs to be done
2. **Action**: Choose appropriate tool
3. **Action Input**: Prepare tool input
4. **Observation**: Process tool output
5. Repeat until final answer is ready

### GUI Threading Model
```
Main Thread (GUI)
  ↓
  Spawns → Worker Thread (Agent Execution)
           ↓
           Callbacks → Signal → Main Thread → Update UI
```

## 💡 Usage Patterns

### Simple Question
```
User: "What is 150 * 23?"
Agent: Uses calculator → Returns 3450
```

### Research Query
```
User: "Tell me about the Pythagorean theorem"
Agent: 
  1. Checks Wikipedia for Pythagorean theorem
  2. Synthesizes information
  3. Returns comprehensive answer
```

### Multi-Tool Query
```
User: "Search for Python tutorials and save the top result to a file"
Agent:
  1. Uses web_search for "Python tutorials"
  2. Extracts top result
  3. Uses write_file to save
  4. Confirms completion
```

### Complex Research
```
User: "Find Einstein's birth year, calculate his age if alive, and save to file"
Agent:
  1. Wikipedia lookup for Einstein
  2. Calculator for age (2025 - birth year)
  3. Write to file with summary
  4. Return final answer
```

## 🔧 Customization Guide

### Change Model
Edit `research_agent.py`, line 50:
```python
self.llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",  # Change this
    temperature=0.7,                # Adjust creativity
    streaming=True,
)
```

Models available:
- `gemini-2.0-flash-exp` (current, fastest)
- `gemini-1.5-pro` (more capable, slower)
- `gemini-1.5-flash` (balanced)

### Adjust Agent Behavior
Edit `research_agent.py`, line 82:
```python
self.agent_executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    memory=self.memory,
    verbose=True,           # Set False to reduce console output
    handle_parsing_errors=True,
    max_iterations=10,      # Increase for complex tasks
    return_intermediate_steps=True
)
```

### Add New Tool
1. Create tool class in `research_tools.py`:
```python
class MyNewTool:
    def run(self, input: str) -> str:
        # Implementation
        return result
```

2. Add to `create_tools()` function:
```python
Tool(
    name="my_tool",
    func=MyNewTool().run,
    description="What this tool does..."
)
```

### Modify GUI Colors
Edit `research_gui.py`, color definitions:
- Line 26: LLM start color
- Line 34: LLM finish color
- Line 40: Tool usage color
- Line 47: Tool output color
- Line 53: Agent thinking color

## 📊 Performance Considerations

### Response Time
- Simple calculator: <1 second
- Web search: 2-5 seconds (network dependent)
- Wikipedia: 1-3 seconds
- Complex multi-tool: 5-15 seconds

### Memory Usage
- Base application: ~100MB
- With conversation history: +10MB per 100 messages
- PyQt6 GUI: ~50MB

### Optimization Tips
1. Reduce `max_results` in WebSearchTool (line 16 of research_tools.py)
2. Decrease `doc_content_chars_max` for Wikipedia (line 27)
3. Set `verbose=False` in agent executor for less logging
4. Clear memory periodically for long sessions

## 🐛 Common Issues & Solutions

### Issue: "GOOGLE_API_KEY not found"
**Solution**: 
```bash
copy .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_actual_key
```

### Issue: Import errors for langchain
**Solution**:
```bash
pip install --upgrade langchain langchain-google-genai langchain-community
```

### Issue: PyQt6 not working
**Solution** (Windows):
```bash
pip uninstall PyQt6
pip install PyQt6
```

### Issue: DuckDuckGo search fails
**Solution**: Check internet connection and firewall settings
```bash
python -c "from duckduckgo_search import DDGS; print(DDGS().text('test', max_results=1))"
```

### Issue: Agent takes too long
**Solutions**:
- Reduce `max_iterations` in research_agent.py (line 88)
- Use `gemini-2.0-flash-exp` for faster responses
- Simplify prompts

### Issue: GUI freezes
**Cause**: Worker thread issue
**Solution**: Already handled with QThread - check for exceptions in logs/

## 🔐 Security Checklist

✅ API keys in .env (not committed)
✅ Calculator uses restricted eval namespace
✅ File operations validate paths
✅ No arbitrary code execution
✅ Input sanitization on file paths
⚠️ For production: Add rate limiting
⚠️ For production: Implement user authentication
⚠️ For production: Add input validation middleware

## 📈 Next Steps / Enhancements

### Phase 2 (Future)
- [ ] Add PDF reading tool
- [ ] Integrate ArXiv search for research papers
- [ ] Add email sending capability
- [ ] Implement web scraping tool
- [ ] Add image generation tool

### Phase 3 (Advanced)
- [ ] Multi-agent orchestration
- [ ] Vector database for RAG
- [ ] Custom knowledge base integration
- [ ] API server mode (Flask/FastAPI)
- [ ] Docker containerization

### Production Readiness
- [ ] Add comprehensive unit tests
- [ ] Implement CI/CD pipeline
- [ ] Set up error monitoring (Sentry)
- [ ] Add usage analytics
- [ ] Create deployment documentation
- [ ] Implement backup/restore for conversations

## 📚 Code Quality

### Standards Followed
✅ PEP 8 style guide
✅ Type hints where applicable
✅ Comprehensive docstrings
✅ Error handling throughout
✅ Logging at appropriate levels
✅ Separation of concerns

### File Organization
- **research_main.py**: Entry point, minimal logic
- **research_agent.py**: Agent configuration only
- **research_tools.py**: Tool implementations only
- **research_gui.py**: GUI code only
- Each module has clear responsibility

## 🎓 Learning Resources

### LangChain Concepts Used
- **Agents**: High-level reasoning entities
- **Tools**: External capabilities
- **Memory**: Conversation state
- **Callbacks**: Streaming and monitoring
- **Prompts**: ReAct template
- **Executors**: Agent runtime

### PyQt6 Concepts Used
- **QMainWindow**: Application window
- **QSplitter**: Resizable panels
- **QThread**: Background processing
- **Signals/Slots**: Event handling
- **QTextEdit**: Rich text display

## 📞 Support & Resources

### Documentation
- LangChain: https://python.langchain.com/
- Google AI: https://ai.google.dev/
- PyQt6: https://www.riverbankcomputing.com/static/Docs/PyQt6/

### Getting Help
1. Check logs in `logs/` directory
2. Review README_RESEARCH.md
3. Run test_research.py to isolate issues
4. Check console output for errors

---

**🎉 You're ready to use the Research Assistant!**

Run: `python research_main.py`
