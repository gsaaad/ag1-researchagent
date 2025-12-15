# Research Assistant Agent

A professional-grade LangChain-based research assistant with integrated tools for web search, Wikipedia lookup, file operations, and calculations. Features a modern PyQt6 GUI interface with dual-panel design.

## 🎯 Features

### Core Capabilities
- **Web Search**: Real-time internet search using DuckDuckGo API
- **Wikipedia Lookup**: Quick access to Wikipedia article summaries
- **File Operations**: Read and write text files
- **Calculator**: Safe mathematical expression evaluation
- **ReAct Agent**: Advanced reasoning and action loop

### GUI Features
- **Dual-Panel Interface**: Chat on left, agent thinking logs on right
- **Real-time Streaming**: See agent responses as they're generated
- **Conversation Memory**: Maintains context across queries
- **Comprehensive Logging**: Track all agent actions, tool usage, and reasoning

## 📋 Prerequisites

- Python 3.8 or higher
- Google API Key (for Gemini model)
- Internet connection

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_research.txt
```

### 2. Configure API Key

Copy the example environment file and add your Google API key:

```bash
copy .env.example .env
```

Edit `.env` and replace `your_google_api_key_here` with your actual Google API key.

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Create Logs Directory

```bash
mkdir logs
```

### 4. Run the Application

```bash
python research_main.py
```

## 🏗️ Architecture

```
research_main.py          - Entry point and application launcher
research_agent.py         - LangChain agent configuration with ReAct reasoning
research_tools.py         - Tool implementations (search, Wikipedia, files, calculator)
research_gui.py           - PyQt6 GUI interface with dual panels
requirements_research.txt - Python dependencies
.env                      - Environment configuration (API keys)
logs/                     - Application and agent logs
```

## 🛠️ Tools Available

### 1. Web Search
- **Purpose**: Search the internet for current information
- **Input**: Search query string
- **Example**: "latest developments in AI"

### 2. Wikipedia
- **Purpose**: Get detailed information from Wikipedia
- **Input**: Topic name or question
- **Example**: "Albert Einstein"

### 3. Read File
- **Purpose**: Read contents of a text file
- **Input**: Complete file path
- **Example**: "C:\\data\\notes.txt"

### 4. Write File
- **Purpose**: Write content to a text file
- **Input Format**: `filepath|content`
- **Example**: "C:\\output\\summary.txt|This is the summary..."

### 5. Calculator
- **Purpose**: Evaluate mathematical expressions
- **Input**: Mathematical expression
- **Example**: "(10 * 5) + 25"

## 💡 Usage Examples

### Example 1: Research Query
```
User: "What is quantum computing and what are its recent applications?"

Agent will:
1. Search Wikipedia for quantum computing basics
2. Perform web search for recent applications
3. Synthesize information into comprehensive answer
```

### Example 2: Calculation and File Save
```
User: "Calculate the compound interest on $10000 at 5% for 3 years and save it to a file"

Agent will:
1. Use calculator: 10000 * (1.05^3)
2. Use write_file to save results
3. Provide confirmation
```

### Example 3: Multi-step Research
```
User: "Find information about the Eiffel Tower, calculate its age, and save a summary"

Agent will:
1. Wikipedia lookup for Eiffel Tower
2. Calculate age using completion year
3. Write summary to file
4. Return complete answer
```

## 🎨 GUI Interface

### Chat Panel (Left)
- Displays conversation history
- User input field at bottom
- Send and Clear buttons
- Color-coded messages (User: blue, Assistant: green, Errors: red)

### Agent Thinking Panel (Right)
- Real-time agent reasoning process
- Tool usage indicators
- LLM token streaming
- Action/observation logs
- Color-coded by activity type

## 📊 Logging

The application maintains comprehensive logs in the `logs/` directory:

- `main.log`: Application startup and shutdown events
- `agent.log`: Agent reasoning, tool usage, and execution details

## 🔧 Customization

### Modify Tools
Edit `research_tools.py` to:
- Add new tools
- Modify existing tool behavior
- Adjust tool descriptions

### Change Agent Behavior
Edit `research_agent.py` to:
- Adjust temperature for creativity
- Modify max iterations
- Change the ReAct prompt template
- Update model (e.g., use different Gemini version)

### Customize GUI
Edit `research_gui.py` to:
- Change color scheme
- Adjust panel sizes
- Add new features
- Modify fonts and styling

## 🐛 Troubleshooting

### "GOOGLE_API_KEY not found"
- Ensure `.env` file exists in the project root
- Verify API key is set correctly
- Check for typos in environment variable name

### Import Errors
- Run `pip install -r requirements_research.txt` again
- Verify Python version is 3.8+
- Check for conflicting package versions

### GUI Doesn't Launch
- Verify PyQt6 is installed correctly
- On Linux, may need: `sudo apt-get install python3-pyqt6`
- Check display environment variables

### Tool Errors
- Web search: Check internet connection
- Wikipedia: Verify connectivity to Wikipedia
- File operations: Check file paths and permissions
- Calculator: Ensure valid mathematical expressions

## 🔐 Security Notes

- Never commit `.env` file with real API keys
- Calculator tool uses `eval` with restricted namespace for safety
- File operations limited to specified paths
- No external code execution beyond defined tools

## 📚 Technical Details

### Agent Architecture
- **Framework**: LangChain with Google Generative AI
- **Reasoning Pattern**: ReAct (Reasoning + Acting)
- **Memory**: Conversation buffer for context retention
- **Execution**: Agent executor with error handling

### GUI Architecture
- **Framework**: PyQt6
- **Threading**: QThread for non-blocking agent execution
- **Callbacks**: Custom streaming handler for real-time updates
- **Styling**: Fusion style for modern appearance

## 🚀 Deployment Considerations

For public deployment:
1. Implement rate limiting
2. Add user authentication
3. Set up API key rotation
4. Configure proper logging and monitoring
5. Add input validation and sanitization
6. Implement usage quotas
7. Set up error tracking (e.g., Sentry)
8. Configure production-grade database for conversation history

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues or questions:
- Check troubleshooting section
- Review logs in `logs/` directory
- Open an issue on GitHub

---

**Built with LangChain, Google Gemini AI, and PyQt6**
