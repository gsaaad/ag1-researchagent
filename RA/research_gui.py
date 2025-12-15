# Copyright (c) 2025
# Licensed under the MIT License
"""
PyQt6 GUI for Research Assistant
Dual-panel interface: Chat + Agent Thinking Logs
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QSplitter, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from langchain.callbacks.base import BaseCallbackHandler
import logging

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming agent responses to GUI"""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.current_thought = ""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts"""
        self.append_log("\n[LLM Started]\n", color="#0066cc")
    
    def on_llm_new_token(self, token: str, **kwargs):
        """Called when new token is generated"""
        self.text_widget.insertPlainText(token)
        self.text_widget.ensureCursorVisible()
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM finishes"""
        self.append_log("\n[LLM Finished]\n", color="#00cc66")
    
    def on_tool_start(self, serialized, input_str: str, **kwargs):
        """Called when tool starts"""
        tool_name = serialized.get("name", "Unknown")
        self.append_log(f"\n🔧 Using Tool: {tool_name}\n", color="#ff6600")
        self.append_log(f"   Input: {input_str}\n", color="#666666")
    
    def on_tool_end(self, output: str, **kwargs):
        """Called when tool finishes"""
        self.append_log(f"   Output: {output[:200]}...\n" if len(output) > 200 else f"   Output: {output}\n", 
                       color="#009900")
    
    def on_agent_action(self, action, **kwargs):
        """Called when agent takes action"""
        self.append_log(f"\n💭 Thinking: {action.log}\n", color="#9900cc")
    
    def append_log(self, text: str, color: str = "#000000"):
        """Append colored text to log widget"""
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_widget.setTextCursor(cursor)
        self.text_widget.insertHtml(f'<span style="color:{color}">{text}</span>')
        self.text_widget.ensureCursorVisible()


class AgentWorker(QThread):
    """Worker thread for running agent queries"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, agent, query):
        super().__init__()
        self.agent = agent
        self.query = query
    
    def run(self):
        """Execute agent query in background thread"""
        try:
            result = self.agent.run(self.query)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ResearchAssistantGUI(QMainWindow):
    """Main GUI window for research assistant"""
    
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Research Assistant Agent")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create title
        title = QLabel("🔍 AI Research Assistant")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Create splitter for dual panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Chat interface
        chat_panel = self.create_chat_panel()
        splitter.addWidget(chat_panel)
        
        # Right panel: Agent thinking logs
        log_panel = self.create_log_panel()
        splitter.addWidget(log_panel)
        
        # Set initial sizes (60% chat, 40% logs)
        splitter.setSizes([840, 560])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        logger.info("GUI initialized")
    
    def create_chat_panel(self):
        """Create the chat interface panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Chat title
        chat_label = QLabel("💬 Conversation")
        chat_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(chat_label)
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything... (Press Enter to send)")
        self.input_field.setFont(QFont("Arial", 11))
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_chat)
        input_layout.addWidget(self.clear_button)
        
        layout.addLayout(input_layout)
        
        return panel
    
    def create_log_panel(self):
        """Create the agent thinking logs panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Log title
        log_label = QLabel("🧠 Agent Thinking Process")
        log_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_display)
        
        # Clear logs button
        clear_log_button = QPushButton("Clear Logs")
        clear_log_button.clicked.connect(lambda: self.log_display.clear())
        layout.addWidget(clear_log_button)
        
        return panel
    
    def send_message(self):
        """Handle sending a message to the agent"""
        query = self.input_field.text().strip()
        
        if not query:
            return
        
        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.statusBar().showMessage("Processing...")
        
        # Display user message
        self.append_chat(f"<b>You:</b> {query}", "#000080")
        self.input_field.clear()
        
        # Clear previous logs
        self.log_display.clear()
        
        # Create callback handler for streaming
        callback = StreamingCallbackHandler(self.log_display)
        self.agent.llm.callbacks = [callback]
        
        # Run agent in background thread
        self.worker = AgentWorker(self.agent, query)
        self.worker.finished.connect(self.on_agent_finished)
        self.worker.error.connect(self.on_agent_error)
        self.worker.start()
    
    def on_agent_finished(self, result):
        """Handle agent completion"""
        output = result.get("output", "No response generated")
        
        # Display agent response
        self.append_chat(f"<b>Assistant:</b> {output}", "#006600")
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
        self.statusBar().showMessage("Ready")
        
        logger.info("Agent response displayed")
    
    def on_agent_error(self, error_msg):
        """Handle agent error"""
        self.append_chat(f"<b>Error:</b> {error_msg}", "#cc0000")
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Error occurred")
        
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error_msg}")
        logger.error(f"Agent error: {error_msg}")
    
    def append_chat(self, text: str, color: str = "#000000"):
        """Append message to chat display"""
        self.chat_display.append(f'<span style="color:{color}">{text}</span>')
        self.chat_display.ensureCursorVisible()
    
    def clear_chat(self):
        """Clear chat history and agent memory"""
        reply = QMessageBox.question(
            self, "Clear Chat",
            "Are you sure you want to clear the conversation history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_display.clear()
            self.log_display.clear()
            self.agent.clear_memory()
            self.statusBar().showMessage("Chat cleared")
            logger.info("Chat and memory cleared")


def launch_gui(agent):
    """Launch the GUI application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = ResearchAssistantGUI(agent)
    window.show()
    
    sys.exit(app.exec())
