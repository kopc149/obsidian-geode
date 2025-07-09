
# geode_gui.py

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QFrame, QLabel, QPushButton, QListWidget, QListWidgetItem, QScrollArea,
    QTextEdit, QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QMessageBox,
    QMenu, QTabWidget, QGroupBox, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool
from PyQt6.QtGui import QKeyEvent

# --- Import from our backend package ---
from geode_bridge.config import Config
from geode_bridge.exceptions import *
from geode_bridge.history import ChatHistoryManager
from geode_bridge.bridge import GeodeBridge

# --- Material Design Theme ---
try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

# --- SETUP ---
# Logging is configured in the backend, but we can get the logger here.
logger = logging.getLogger(__name__)

# --- THREADING & GUI WIDGETS ---

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    tool_call = pyqtSignal(str)
    message = pyqtSignal(str, str)
    file_cache_updated = pyqtSignal(list)


class GeminiWorker(QRunnable):
    """Worker thread for handling AI message processing."""
    
    def __init__(self, bridge: GeodeBridge, prompt: str):
        super().__init__()
        self.bridge = bridge
        self.prompt = prompt
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        """Execute the AI message processing in a separate thread."""
        self.bridge.send_message(self.prompt, self.signals)


class FileCacheWorker(QRunnable):
    """Worker thread for updating the file cache from Obsidian vault."""
    
    def __init__(self, bridge: GeodeBridge):
        super().__init__()
        self.bridge = bridge
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        """Fetch and update the file cache."""
        logger.info("Caching vault file tree...")
        try:
            items_str = self.bridge.tools.list_all_files()
            if not items_str.startswith("ERROR"):
                all_files = items_str.replace("SUCCESS:\\n", "").strip().split('\\n')
                unique_files = sorted(list(set(all_files)))
                self.signals.file_cache_updated.emit(unique_files)
                logger.info(f"File cache updated. Found {len(unique_files)} items.")
            else:
                logger.error(f"Error updating file cache: {items_str}")
                self.signals.error.emit(items_str)
        except Exception as e:
            logger.error(f"Critical error during file cache update: {e}", exc_info=True)
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


# ============================================================================
# UI COMPONENTS - AUTOCOMPLETE
# ============================================================================

class AutocompletePopup(QListWidget):
    """Popup widget for file path autocomplete functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._setup_styling()
    
    def _setup_styling(self):
        """Configure the visual appearance of the popup."""
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #475569;
                background-color: #334155;
                font-size: 13px;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
            }
        """)


class ChatInput(QTextEdit):
    """Enhanced text input with file autocomplete functionality."""
    
    sendMessage = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_cache = []
        self.autocomplete_popup = AutocompletePopup(self)
        self._setup_connections()
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.autocomplete_popup.itemClicked.connect(self.complete_text)
        self.textChanged.connect(self.handle_autocomplete)
    
    @pyqtSlot(list)
    def update_file_cache(self, new_cache):
        """Update the available files for autocomplete."""
        self.file_cache = new_cache
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events for autocomplete and message sending."""
        is_popup_visible = self.autocomplete_popup.isVisible()
        
        # Handle popup navigation
        if is_popup_visible and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.autocomplete_popup.keyPressEvent(event)
            return
        
        # Handle autocomplete selection
        if is_popup_visible and event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
            if self.autocomplete_popup.currentItem():
                self.complete_text(self.autocomplete_popup.currentItem())
            self.autocomplete_popup.hide()
            return
        
        # Handle message sending (Cmd+Return)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (event.modifiers() & Qt.KeyboardModifier.MetaModifier):
            self.sendMessage.emit()
            return
        
        super().keyPressEvent(event)
    
    def handle_autocomplete(self):
        """Process text changes and show autocomplete suggestions."""
        text_before_cursor = self.toPlainText()[:self.textCursor().position()]
        trigger = "/"
        last_trigger_pos = text_before_cursor.rfind(trigger)
        
        if last_trigger_pos == -1:
            self.autocomplete_popup.hide()
            return
        
        search_text = text_before_cursor[last_trigger_pos + len(trigger):]
        
        # Hide popup if search text contains spaces or newlines
        if " " in search_text or "\\n" in search_text:
            self.autocomplete_popup.hide()
            return
        
        # Filter suggestions based on search text
        if search_text:
            suggestions = [path for path in self.file_cache if search_text.lower() in path.lower()]
        else:
            suggestions = self.file_cache
        
        if suggestions:
            self.update_popup_suggestions(suggestions)
        else:
            self.autocomplete_popup.hide()
    
    def update_popup_suggestions(self, suggestions):
        """Update and show the autocomplete popup with suggestions."""
        self.autocomplete_popup.clear()
        self.autocomplete_popup.addItems(suggestions[:10])  # Limit to 10 items
        
        if self.autocomplete_popup.count() > 0:
            # Position popup below cursor
            cursor_rect = self.cursorRect()
            popup_pos = self.mapToGlobal(cursor_rect.bottomLeft())
            self.autocomplete_popup.move(popup_pos)
            self.autocomplete_popup.setMinimumWidth(self.width() - 20)
            self.autocomplete_popup.adjustSize()
            self.autocomplete_popup.show()
            self.autocomplete_popup.setCurrentRow(0)
        else:
            self.autocomplete_popup.hide()
    
    def complete_text(self, item):
        """Complete the text with the selected item."""
        completion_text = item.text()
        cursor = self.textCursor()
        text_before_cursor = self.toPlainText()[:cursor.position()]
        
        trigger = "/"
        last_trigger_pos = text_before_cursor.rfind(trigger)
        text_to_replace = text_before_cursor[last_trigger_pos:]
        
        # Replace the partial text with the completion
        cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, len(text_to_replace))
        cursor.insertText(completion_text)
        self.setTextCursor(cursor)
        self.autocomplete_popup.hide()


# ============================================================================
# SETTINGS DIALOG
# ============================================================================

class SettingsDialog(QDialog):
    """Configuration dialog for API keys and settings."""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the settings dialog UI."""
        self.setWindowTitle("Geode Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Create tabs for different setting categories
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Core Settings Tab
        core_tab = QWidget()
        core_layout = QVBoxLayout(core_tab)
        core_form = QFormLayout()
        
        # AI Provider selection
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems([
            "gemini", "claude", "openai", "cohere", 
            "mistral", "ollama", "perplexity", "together"
        ])
        self.ai_provider_combo.setCurrentText(self.config.ai_provider)
        self.ai_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        
        # API Key fields
        self.gemini_key_edit = QLineEdit(self.config.gemini_api_key)
        self.gemini_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.claude_key_edit = QLineEdit(self.config.claude_api_key)
        self.claude_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.openai_key_edit = QLineEdit(self.config.openai_api_key)
        self.openai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.cohere_key_edit = QLineEdit(self.config.cohere_api_key)
        self.cohere_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.mistral_key_edit = QLineEdit(self.config.mistral_api_key)
        self.mistral_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.perplexity_key_edit = QLineEdit(self.config.perplexity_api_key)
        self.perplexity_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.together_key_edit = QLineEdit(self.config.together_api_key)
        self.together_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Ollama URL field (no API key needed)
        self.ollama_url_edit = QLineEdit(self.config.ollama_base_url)
        
        self.obsidian_key_edit = QLineEdit(self.config.obsidian_api_key)
        self.obsidian_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self._update_available_models()
        self.model_combo.setCurrentText(self.config.model_name)
        
        self.port_edit = QLineEdit(str(self.config.obsidian_port))
        
        core_form.addRow("AI Provider:", self.ai_provider_combo)
        core_form.addRow("Gemini API Key:", self.gemini_key_edit)
        core_form.addRow("Claude API Key:", self.claude_key_edit)
        core_form.addRow("OpenAI API Key:", self.openai_key_edit)
        core_form.addRow("Cohere API Key:", self.cohere_key_edit)
        core_form.addRow("Mistral API Key:", self.mistral_key_edit)
        core_form.addRow("Perplexity API Key:", self.perplexity_key_edit)
        core_form.addRow("Together API Key:", self.together_key_edit)
        core_form.addRow("Ollama Base URL:", self.ollama_url_edit)
        core_form.addRow("Obsidian API Key:", self.obsidian_key_edit)
        core_form.addRow("AI Model:", self.model_combo)
        core_form.addRow("Obsidian Port:", self.port_edit)
        
        # Initially show/hide API key fields based on selected provider
        self._on_provider_changed(self.config.ai_provider)
        
        core_layout.addLayout(core_form)
        core_layout.addStretch()
        tab_widget.addTab(core_tab, "Core Settings")
        
        # Optional Extensions Tab
        extensions_tab = QWidget()
        extensions_layout = QVBoxLayout(extensions_tab)
        
        # MCP Section
        mcp_group = QGroupBox("MCP Server Integration (Optional)")
        mcp_layout = QVBoxLayout(mcp_group)
        
        # MCP enable checkbox
        self.mcp_enabled_checkbox = QCheckBox("Enable MCP server integration")
        self.mcp_enabled_checkbox.setChecked(self.config.enable_mcp)
        self.mcp_enabled_checkbox.setToolTip("Enable this to connect to additional MCP servers for extended capabilities")
        mcp_layout.addWidget(self.mcp_enabled_checkbox)
        
        # MCP info label
        mcp_info = QLabel("💡 MCP (Model Context Protocol) allows you to connect additional tools and capabilities.\n"
                         "This is completely optional - Geode works perfectly with just Obsidian integration.\n"
                         "🎯 Best with: Claude, OpenAI, Cohere, Mistral, Together AI")
        mcp_info.setWordWrap(True)
        mcp_info.setStyleSheet("color: #888; font-size: 12px; margin: 10px 0;")
        mcp_layout.addWidget(mcp_info)
        
        # MCP config file field
        mcp_config_layout = QHBoxLayout()
        self.mcp_config_edit = QLineEdit(self.config.mcp_config_file)
        self.mcp_config_edit.setPlaceholderText("mcp_servers.json")
        mcp_config_layout.addWidget(QLabel("Config File:"))
        mcp_config_layout.addWidget(self.mcp_config_edit)
        mcp_layout.addLayout(mcp_config_layout)
        
        # MCP status info
        self.mcp_status_label = QLabel("Status: Not connected")
        self.mcp_status_label.setStyleSheet("color: #666; font-size: 11px;")
        mcp_layout.addWidget(self.mcp_status_label)
        
        extensions_layout.addWidget(mcp_group)
        extensions_layout.addStretch()
        tab_widget.addTab(extensions_tab, "Optional Extensions")
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _on_provider_changed(self, provider: str):
        """Handle AI provider selection change."""
        # Show/hide relevant API key fields
        self.gemini_key_edit.setVisible(provider == "gemini")
        self.claude_key_edit.setVisible(provider == "claude")
        self.openai_key_edit.setVisible(provider == "openai")
        self.cohere_key_edit.setVisible(provider == "cohere")
        self.mistral_key_edit.setVisible(provider == "mistral")
        self.perplexity_key_edit.setVisible(provider == "perplexity")
        self.together_key_edit.setVisible(provider == "together")
        self.ollama_url_edit.setVisible(provider == "ollama")
        
        # Update available models
        self._update_available_models()
        
        # Update MCP compatibility info
        if hasattr(self, 'mcp_status_label'):
            if provider in ["claude", "openai", "cohere", "mistral", "together"]:
                self.mcp_status_label.setText("Status: MCP compatible provider selected")
                self.mcp_status_label.setStyleSheet("color: #4ade80; font-size: 11px;")
            elif provider == "ollama":
                self.mcp_status_label.setText("Status: Local provider - MCP may work depending on model")
                self.mcp_status_label.setStyleSheet("color: #3b82f6; font-size: 11px;")
            else:
                self.mcp_status_label.setText("Status: Limited MCP support for this provider")
                self.mcp_status_label.setStyleSheet("color: #fbbf24; font-size: 11px;")
    
    def _update_available_models(self):
        """Update the model dropdown based on selected provider."""
        provider = self.ai_provider_combo.currentText()
        available_models = self.config.get_available_models()
        
        self.model_combo.clear()
        if provider in available_models:
            self.model_combo.addItems(available_models[provider])
            
            # Set default model for provider
            defaults = {
                "gemini": "gemini-2.5-pro",
                "claude": "claude-3-5-sonnet-20241022", 
                "openai": "gpt-4o",
                "cohere": "command-r-plus",
                "mistral": "mistral-large-latest",
                "ollama": "llama3.1:8b",
                "perplexity": "llama-3.1-sonar-large-128k-online",
                "together": "meta-llama/Llama-3-70b-chat-hf"
            }
            if provider in defaults:
                self.model_combo.setCurrentText(defaults[provider])
    
    def accept(self):
        """Validate and save configuration when user clicks Save."""
        # Update config with form values
        self.config.ai_provider = self.ai_provider_combo.currentText()
        self.config.gemini_api_key = self.gemini_key_edit.text()
        self.config.claude_api_key = self.claude_key_edit.text()
        self.config.openai_api_key = self.openai_key_edit.text()
        self.config.cohere_api_key = self.cohere_key_edit.text()
        self.config.mistral_api_key = self.mistral_key_edit.text()
        self.config.perplexity_api_key = self.perplexity_key_edit.text()
        self.config.together_api_key = self.together_key_edit.text()
        self.config.ollama_base_url = self.ollama_url_edit.text()
        self.config.obsidian_api_key = self.obsidian_key_edit.text()
        self.config.model_name = self.model_combo.currentText()
        self.config.obsidian_port = self.port_edit.text()
        
        # Update MCP settings
        self.config.enable_mcp = self.mcp_enabled_checkbox.isChecked()
        self.config.mcp_config_file = self.mcp_config_edit.text() or "mcp_servers.json"
        
        # Validate configuration before saving
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            QMessageBox.warning(self, "Configuration Error", f"Invalid configuration: {error_msg}")
            return
        
        try:
            self.config.save()
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration: {e}")


# ============================================================================
# MESSAGE CARDS
# ============================================================================

class GroupedMessageCard(QFrame):
    """Card widget for displaying AI responses and tool calls."""
    
    def __init__(self, theme, model_name):
        super().__init__()
        self.theme = theme
        self.model_name = model_name
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the message card UI."""
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"QFrame {{ background-color: {self.theme['surface']}; border-radius: 12px; }}")
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(12, 12, 12, 12)
        self.card_layout.setSpacing(10)
    
    def add_message_part(self, sender, text, is_tool_call=False):
        """Add a message part to this card."""
        if is_tool_call:
            sender_text = "⚙️ System (Executing Tool)"
            sender_color = self.theme['tertiary_accent']
        else:
            sender_text = f"Geode ({self.model_name})"
            sender_color = self.theme['secondary_accent']
        
        # Create the message part
        part_frame = QFrame()
        part_layout = QVBoxLayout(part_frame)
        part_layout.setContentsMargins(0, 0, 0, 0)
        part_layout.setSpacing(5)
        
        # Sender label
        sender_label = QLabel(sender_text)
        sender_label.setStyleSheet(f"""
            color: {sender_color};
            font-size: 13px;
            font-weight: bold;
            background-color: transparent;
        """)
        part_layout.addWidget(sender_label)
        
        # Content label
        content_label = QLabel(text)
        content_label.setWordWrap(True)
        content_label.setStyleSheet(f"""
            color: {self.theme['text_primary']};
            font-size: 14px;
            background-color: transparent;
        """)
        part_layout.addWidget(content_label)
        
        self.card_layout.addWidget(part_frame)


class UserMessageCard(QFrame):
    """Card widget for displaying user messages."""
    
    def __init__(self, text, theme):
        super().__init__()
        self.theme = theme
        self._setup_ui(text)
    
    def _setup_ui(self, text):
        """Set up the user message card UI."""
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border: none;")
        
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(5)
        
        # Sender label
        sender_label = QLabel("You")
        sender_label.setStyleSheet(f"""
            color: {self.theme['primary_accent']};
            font-size: 13px;
            font-weight: bold;
        """)
        card_layout.addWidget(sender_label)
        
        # Content label
        content_label = QLabel(text)
        content_label.setWordWrap(True)
        content_label.setStyleSheet(f"""
            color: {self.theme['text_primary']};
            font-size: 14px;
        """)
        card_layout.addWidget(content_label)


# ============================================================================
# CHAT VIEW
# ============================================================================

class ChatView(QWidget):
    """Main chat interface widget."""
    
    def __init__(self, theme, bridge, history_manager, file_cache, session_id):
        super().__init__()
        self.theme = theme
        self.bridge = bridge
        self.history_manager = history_manager
        self.session_id = session_id
        self.threadpool = QThreadPool()
        self.current_ai_card = None
        
        self._setup_ui()
        self.text_input.update_file_cache(file_cache)
        self.load_history()
    
    def _setup_ui(self):
        """Set up the chat view UI."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Scrollable message area
        self._setup_message_area()
        
        # Input composer
        self._setup_input_composer()
        
        # Connect signals
        self.send_button.clicked.connect(self.send_message)
        self.text_input.sendMessage.connect(self.send_message)
    
    def _setup_message_area(self):
        """Set up the scrollable message display area."""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.addStretch()
        self.message_layout.setSpacing(15)
        self.message_layout.setContentsMargins(40, 20, 40, 20)
        
        self.scroll_area.setWidget(self.message_container)
        self.main_layout.addWidget(self.scroll_area)
    
    def _setup_input_composer(self):
        """Set up the message input area."""
        composer_frame = QFrame()
        composer_frame.setFixedHeight(80)
        composer_frame.setStyleSheet(f"background-color: {self.theme['background']};")
        
        composer_layout = QHBoxLayout(composer_frame)
        composer_layout.setContentsMargins(40, 10, 40, 10)
        
        # Text input
        self.text_input = ChatInput()
        self.text_input.setPlaceholderText("Reply to Geode... (Press '/' for files, Cmd+Return to send)")
        self.text_input.setFixedHeight(44)
        self.text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['surface']};
                color: {self.theme['text_primary']};
                border: 1px solid #475569;
                border-radius: 12px;
                font-size: 14px;
                padding: 10px;
            }}
        """)
        composer_layout.addWidget(self.text_input)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(80, 44)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['primary_accent']};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3b82f6;
            }}
        """)
        composer_layout.addWidget(self.send_button)
        
        self.main_layout.addWidget(composer_frame)
    
    def load_history(self):
        """Load and display chat history for the current session."""
        self.clear_chat_display()
        session = self.history_manager.get_session(self.session_id)
        
        if not session or not session.messages:
            self.welcome_message()
            return
        
        current_ai_card = None
        for msg in session.messages:
            if msg.sender == "user":
                self._add_widget_to_display(UserMessageCard(msg.content, self.theme))
                current_ai_card = None
            else:
                if current_ai_card is None:
                    current_ai_card = self._add_widget_to_display(
                        GroupedMessageCard(self.theme, self.bridge.config.model_name)
                    )
                current_ai_card.add_message_part(
                    msg.sender, msg.content, msg.message_type == 'tool_call'
                )
    
    def send_message(self):
        """Send a message to the AI."""
        prompt = self.text_input.toPlainText().strip()
        if not prompt:
            return
        
        # Add user message to history and display
        self.history_manager.add_message(self.session_id, "user", prompt)
        self._add_widget_to_display(UserMessageCard(prompt, self.theme))
        
        # Clear input and disable send button
        self.text_input.clear()
        self.text_input.setFixedHeight(44)
        self.send_button.setDisabled(True)
        self.send_button.setText("...")
        
        # Start AI processing in background thread
        worker = GeminiWorker(self.bridge, prompt)
        worker.signals.message.connect(self.on_ai_message)
        worker.signals.tool_call.connect(self.on_tool_call)
        worker.signals.error.connect(self.on_error)
        worker.signals.finished.connect(self.on_finished)
        self.threadpool.start(worker)
        
        self.current_ai_card = None
    
    def _add_widget_to_display(self, widget):
        """Add a widget to the message display."""
        self.message_layout.insertWidget(self.message_layout.count() - 1, widget)
        return widget
    
    def clear_chat_display(self):
        """Clear all messages from the display."""
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()
    
    def welcome_message(self):
        """Display a welcome message for new chats."""
        self.clear_chat_display()
        welcome_card = self._add_widget_to_display(
            GroupedMessageCard(self.theme, self.bridge.config.model_name)
        )
        welcome_card.add_message_part("Geode", "Welcome! How can I help with your vault?")
    
    @pyqtSlot(str)
    def on_tool_call(self, content):
        """Handle tool call display."""
        self.history_manager.add_message(self.session_id, "system", content, "tool_call")
        if self.current_ai_card is None:
            self.current_ai_card = self._add_widget_to_display(
                GroupedMessageCard(self.theme, self.bridge.config.model_name)
            )
        self.current_ai_card.add_message_part("Tool", content, is_tool_call=True)
    
    @pyqtSlot(str, str)
    def on_ai_message(self, sender, content):
        """Handle AI message display."""
        self.history_manager.add_message(self.session_id, "assistant", content)
        if self.current_ai_card is None:
            self.current_ai_card = self._add_widget_to_display(
                GroupedMessageCard(self.theme, self.bridge.config.model_name)
            )
        self.current_ai_card.add_message_part(sender, content)
    
    @pyqtSlot(str)
    def on_error(self, error_text):
        """Handle error display."""
        self.history_manager.add_message(self.session_id, "system", error_text, "error")
        error_card = self._add_widget_to_display(
            GroupedMessageCard(self.theme, self.bridge.config.model_name)
        )
        error_card.add_message_part("Error", error_text)
        error_card.setStyleSheet("""
            QFrame {
                border: 1px solid red;
                background-color: #401010;
                border-radius: 12px;
            }
        """)
    
    @pyqtSlot()
    def on_finished(self):
        """Handle completion of AI processing."""
        self.send_button.setDisabled(False)
        self.send_button.setText("Send")
        self.current_ai_card = None


# ============================================================================
# NAVIGATION SIDEBAR
# ============================================================================

class NavigationSidebar(QWidget):
    """Sidebar for navigation and chat session management."""
    
    openSettings = pyqtSignal()
    newChat = pyqtSignal()
    loadChat = pyqtSignal(str)
    deleteChat = pyqtSignal(str)
    
    def __init__(self, theme, history_manager):
        super().__init__()
        self.theme = theme
        self.history_manager = history_manager
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the sidebar UI."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)
        
        # New chat button
        self._setup_new_chat_button()
        
        # Spacing
        self.main_layout.addSpacing(15)
        
        # Recent chats section
        self._setup_recent_chats_section()
        
        # Profile/settings section
        self._setup_profile_section()
    
    def _setup_new_chat_button(self):
        """Set up the new chat button."""
        self.new_chat_button = QPushButton("  +  New Chat")
        self.new_chat_button.setFixedHeight(44)
        self.new_chat_button.setStyleSheet(f"""
            background-color: {self.theme['tertiary_accent']};
            color: #ffffff;
            border: none;
            border-radius: 10px;
            text-align: left;
            padding-left: 14px;
            font-size: 14px;
            font-weight: bold;
        """)
        self.new_chat_button.clicked.connect(self.newChat.emit)
        self.main_layout.addWidget(self.new_chat_button)
    
    def _setup_recent_chats_section(self):
        """Set up the recent chats list."""
        recents_label = QLabel("RECENTS")
        recents_label.setFixedHeight(20)
        recents_label.setStyleSheet(f"""
            color: {self.theme['text_secondary']};
            font-size: 11px;
            font-weight: bold;
            padding-left: 8px;
            border: none;
        """)
        self.main_layout.addWidget(recents_label)
        
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                font-size: 13px;
                padding: 0px;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 10px;
                border-radius: 6px;
                margin: 2px 0px;
            }}
            QListWidget::item:hover {{
                background-color: #475569;
            }}
            QListWidget::item:selected {{
                background-color: {self.theme['background']};
                color: {self.theme['text_primary']};
            }}
        """)
        
        self.chat_list.itemClicked.connect(self.on_chat_selected)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_context_menu)
        self.main_layout.addWidget(self.chat_list)
        
        self.main_layout.addStretch()
    
    def _setup_profile_section(self):
        """Set up the profile/settings section."""
        profile_frame = QFrame()
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(5, 5, 5, 5)
        profile_layout.addStretch()
        
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setStyleSheet("""
            QPushButton {
                border: none;
                font-size: 18px;
            }
        """)
        self.settings_button.clicked.connect(self.openSettings.emit)
        profile_layout.addWidget(self.settings_button)
        
        self.main_layout.addWidget(profile_frame)
    
    def refresh_list(self, current_session_id=None):
        """Refresh the chat list with recent sessions."""
        self.chat_list.clear()
        sessions = self.history_manager.get_recent_sessions()
        selected_row = -1
        
        for idx, session in enumerate(sessions):
            item = QListWidgetItem(session.title)
            item.setData(Qt.ItemDataRole.UserRole, session.session_id)
            self.chat_list.addItem(item)
            
            if current_session_id and session.session_id == current_session_id:
                selected_row = idx
        
        # Ensure the current session is selected if present
        if selected_row != -1:
            self.chat_list.setCurrentRow(selected_row)
    
    def on_chat_selected(self, item):
        """Handle chat selection."""
        if item is None:
            return
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id:
            self.loadChat.emit(session_id)
    
    def show_context_menu(self, position):
        """Show context menu for chat items."""
        item = self.chat_list.itemAt(position)
        if item is None:
            return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete Chat")
        action = menu.exec(self.chat_list.mapToGlobal(position))
        
        if action == delete_action:
            session_id = item.data(Qt.ItemDataRole.UserRole)
            if session_id:
                self.deleteChat.emit(session_id)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class GeodeApp(QMainWindow):
    """Main application window."""
    
    fileCacheUpdated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        # Define application theme - Updated with custom purple RGB(169, 149, 242)
        self.theme = {
            "background": "#1a1a2e",        # Deep purple-navy
            "surface": "#2d2d44",           # Purple-gray surface
            "primary_accent": "#A995F2",    # Custom purple RGB(169, 149, 242)
            "secondary_accent": "#2563eb",  # Blue secondary 
            "tertiary_accent": "#f97316",   # Orange tertiary
            "text_primary": "#f1f5f9",     # Light text
            "text_secondary": "#a78bfa"     # Purple-tinted secondary text
        }
        
        # Initialize application state
        self.bridge = None
        self.file_cache = []
        self.history_manager = None
        self.current_session_id = None
        
        self._setup_window()
        self._apply_material_theme()
        self.load_and_init_ui()
    
    def _setup_window(self):
        """Set up the main window properties."""
        self.setWindowTitle("Geode - Obsidian & Gemini")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        # Basic fallback styling will be replaced by Material Design
        self.setStyleSheet(f"""
            background-color: {self.theme['background']};
            color: {self.theme['text_primary']};
        """)
    
    def _apply_material_theme(self):
        """Apply Material Design theme to the application"""
        if not QT_MATERIAL_AVAILABLE:
            print("qt-material not available, using fallback theme")
            return
        
        try:
            # Apply dark purple as base theme
            apply_stylesheet(QApplication.instance(), theme='dark_purple.xml')
            
            # Override with custom colors
            custom_styles = f"""
            /* Custom Geode Material Design Overrides */
            
            /* Primary buttons with custom purple */
            QPushButton {{
                background-color: {self.theme['primary_accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: #8B7CE8;
            }}
            
            QPushButton:pressed {{
                background-color: #7C6AE4;
            }}
            
            /* Chat message cards with Material Design elevation */
            QFrame {{
                background-color: {self.theme['surface']};
                border: none;
                border-radius: 12px;
            }}
            
            /* Input fields with Material Design styling */
            QLineEdit, QTextEdit {{
                background-color: {self.theme['surface']};
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 12px;
                color: {self.theme['text_primary']};
                font-size: 14px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {self.theme['primary_accent']};
            }}
            
            /* List items with Material Design styling */
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 12px;
                margin: 2px 0px;
                color: {self.theme['text_primary']};
            }}
            
            QListWidget::item:hover {{
                background-color: rgba(169, 149, 242, 0.1);
            }}
            
            QListWidget::item:selected {{
                background-color: {self.theme['primary_accent']};
                color: white;
            }}
            
            /* Typography improvements */
            QLabel {{
                color: {self.theme['text_primary']};
            }}
            
            /* Sidebar styling */
            QFrame[objectName="sidebar"] {{
                background-color: {self.theme['surface']};
            }}
            """
            
            # Apply custom styles on top of Material Design base
            current_stylesheet = QApplication.instance().styleSheet()
            QApplication.instance().setStyleSheet(current_stylesheet + custom_styles)
            
            print("Material Design theme applied successfully")
            
        except Exception as e:
            print(f"Error applying Material Design theme: {e}")
    
    def load_and_init_ui(self):
        """Load configuration and initialize the UI."""
        try:
            self.config = Config.load()
            self.history_manager = ChatHistoryManager(self.config.chat_history_file)
        except Exception as e:
            QMessageBox.critical(
                self, "Fatal Error", 
                f"Could not load critical files.\\n\\nError: {e}"
            )
            sys.exit(1)
        
        # Check if initial setup is needed
        has_ai_key = (
            self.config.gemini_api_key or self.config.claude_api_key or 
            self.config.openai_api_key or self.config.cohere_api_key or 
            self.config.mistral_api_key or self.config.perplexity_api_key or 
            self.config.together_api_key or self.config.ai_provider == "ollama"
        )
        if not has_ai_key or not self.config.obsidian_api_key:
            if not self.show_settings_dialog(is_first_run=True):
                sys.exit(0)
        
        self.setup_main_widgets()
        self.load_latest_session()
    
    def setup_main_widgets(self):
        """Set up the main UI widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for sidebar and main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Sidebar
        self.sidebar_pane = NavigationSidebar(self.theme, self.history_manager)
        self.sidebar_pane.setStyleSheet(f"background-color: {self.theme['surface']};")
        splitter.addWidget(self.sidebar_pane)
        
        # Main content area
        self.main_content_pane = QFrame()
        splitter.addWidget(self.main_content_pane)
        splitter.setSizes([350, 1050])
        
        # Connect sidebar signals
        self.sidebar_pane.openSettings.connect(self.handle_settings_button_click)
        self.sidebar_pane.newChat.connect(self.reset_chat_session)
        self.sidebar_pane.loadChat.connect(self.load_chat_session)
        self.sidebar_pane.deleteChat.connect(self.delete_chat_session)
    
    def load_latest_session(self):
        """Load the most recent chat session or create a new one."""
        if not self.history_manager:
            print("No history manager available in load_latest_session.")
            return
        
        recent_sessions = self.history_manager.get_recent_sessions(1)
        if recent_sessions:
            self.load_chat_session(recent_sessions[0].session_id)
        else:
            self.reset_chat_session()
    
    @pyqtSlot(str)
    def load_chat_session(self, session_id):
        """Load a specific chat session."""
        self.current_session_id = session_id
        
        if hasattr(self, 'sidebar_pane') and self.sidebar_pane is not None:
            self.sidebar_pane.refresh_list(current_session_id=session_id)
        else:
            logger.warning("sidebar_pane is not available in load_chat_session.")
        
        self.refresh_bridge(new_chat_instance=False)
    
    @pyqtSlot()
    def handle_settings_button_click(self):
        """Handle settings button click."""
        self.show_settings_dialog()
    
    def show_settings_dialog(self, is_first_run=False):
        """Show the settings configuration dialog."""
        dialog = SettingsDialog(self.config, self)
        if is_first_run:
            dialog.setWindowTitle("Initial Setup Required")
        
        if dialog.exec():
            print("Settings saved. Refreshing AI bridge...")
            self.refresh_bridge(new_chat_instance=True)
            return True
        elif is_first_run:
            print("Initial setup cancelled. Exiting.")
            sys.exit(0)
        
        return False
    
    @pyqtSlot()
    def reset_chat_session(self):
        """Create and load a new chat session."""
        logger.info("Creating new chat session...")
        
        if not self.history_manager:
            logger.error("No history manager available.")
            return
        
        new_session = self.history_manager.create_session()
        if not new_session:
            QMessageBox.critical(self, "Session Error", "Failed to create a new chat session.")
            return
        
        if self.current_session_id == new_session.session_id:
            logger.info("Already on the latest session; not creating a duplicate.")
            return
        
        self.load_chat_session(new_session.session_id)
    
    @pyqtSlot(str)
    def delete_chat_session(self, session_id):
        """Delete a chat session with confirmation."""
        reply = QMessageBox.question(
            self, "Delete Chat", 
            "Are you sure you want to permanently delete this chat session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if not self.history_manager:
                logger.error("No history manager available.")
                return
            
            self.history_manager.delete_session(session_id)
            
            if hasattr(self, 'sidebar_pane') and self.sidebar_pane is not None:
                self.sidebar_pane.refresh_list()
            else:
                logger.warning("sidebar_pane is not available in delete_chat_session.")
            
            QMessageBox.information(self, "Chat Deleted", "Chat session deleted successfully.")
            
            # If the deleted session was the current one, load the latest or create a new session
            if self.current_session_id == session_id:
                self.load_latest_session()
    
    def refresh_bridge(self, new_chat_instance=True):
        """Refresh the AI bridge and chat view."""
        try:
            if new_chat_instance or self.bridge is None:
                self.bridge = GeodeBridge(self.config)
            
            # Disconnect previous connections to avoid duplicates
            try:
                if hasattr(self, '_last_text_input') and self._last_text_input is not None:
                    self.fileCacheUpdated.disconnect(self._last_text_input.update_file_cache)
            except Exception:
                pass  # Ignore if not connected
            
            # Create new chat view
            new_chat_view = ChatView(
                self.theme, self.bridge, self.history_manager, 
                self.file_cache, self.current_session_id
            )
            self.fileCacheUpdated.connect(new_chat_view.text_input.update_file_cache)
            self._last_text_input = new_chat_view.text_input
            
            # Replace the main content pane
            splitter = self.main_content_pane.parentWidget()
            if isinstance(splitter, QSplitter):
                old_widget = splitter.widget(1)
                if old_widget and old_widget is not new_chat_view:
                    old_widget.deleteLater()
                splitter.insertWidget(1, new_chat_view)
                splitter.setSizes([350, 1050])
            
            self.main_content_pane = new_chat_view
            self.update_file_cache()
            print("AI Bridge refreshed successfully.")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Bridge Error", 
                f"Could not refresh the AI Bridge. Check settings.\\n\\nError: {e}"
            )
    
    def update_file_cache(self):
        """Update the file cache in a background thread."""
        if self.bridge is None:
            print("Cannot update file cache: bridge is None.")
            return
        
        worker = FileCacheWorker(self.bridge)
        worker.signals.file_cache_updated.connect(self.on_cache_updated)
        worker.signals.error.connect(lambda msg: print(f"Cache Error: {msg}"))
        
        pool = QThreadPool.globalInstance()
        if pool is not None:
            pool.start(worker)
        else:
            print("QThreadPool.globalInstance() returned None!")
    
    @pyqtSlot(list)
    def on_cache_updated(self, file_list):
        """Handle file cache update completion."""
        self.file_cache = file_list
        
        # Update file cache if main_content_pane is a ChatView and has text_input
        text_input = getattr(self.main_content_pane, 'text_input', None)
        if text_input is not None:
            text_input.update_file_cache(self.file_cache)
        else:
            print("main_content_pane does not have text_input; skipping file cache update.")
        
        print(f"File cache updated in main app. Found {len(self.file_cache)} items.")


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

def ensure_config_exists():
    """Ensure a basic config file exists."""
    if not Path("config.json").exists():
        print("config.json not found. Creating a dummy file.")
        with open("config.json", 'w') as f:
            json.dump({"gemini_api_key": "", "obsidian_api_key": ""}, f, indent=2)


if __name__ == "__main__":
    ensure_config_exists()
    app = QApplication(sys.argv)
    main_window = GeodeApp()
    main_window.show()
    sys.exit(app.exec())