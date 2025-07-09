#!/usr/bin/env python3
"""
Redesigned Geode GUI with proper Material Design layout
Modern chat interface following 2024 design patterns
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QFrame, QLabel, QPushButton, QListWidget, QListWidgetItem, QScrollArea,
    QTextEdit, QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QMessageBox,
    QMenu, QTabWidget, QGroupBox, QCheckBox, QComboBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool, QTimer
from PyQt6.QtGui import QKeyEvent, QFont

# Material Design Theme
try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

# Import from backend package
from geode_bridge.config import Config
from geode_bridge.exceptions import *
from geode_bridge.history import ChatHistoryManager, ChatSession, ChatMessage
from geode_bridge.bridge import GeodeBridge

logger = logging.getLogger(__name__)


class ModernChatMessage(QFrame):
    """Modern Material Design chat message bubble"""
    
    def __init__(self, sender: str, message: str, is_user: bool = False):
        super().__init__()
        self.sender = sender
        self.message = message
        self.is_user = is_user
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the message bubble UI"""
        self.setContentsMargins(0, 0, 0, 0)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        
        if self.is_user:
            # User message - right aligned
            main_layout.addStretch()
            bubble = self.create_user_bubble()
            main_layout.addWidget(bubble)
        else:
            # AI message - left aligned
            bubble = self.create_ai_bubble()
            main_layout.addWidget(bubble)
            main_layout.addStretch()
    
    def create_user_bubble(self):
        """Create user message bubble"""
        bubble = QFrame()
        bubble.setObjectName("user_bubble")
        bubble.setMaximumWidth(600)
        bubble.setStyleSheet("""
            QFrame#user_bubble {
                background-color: #A995F2;
                border-radius: 18px;
                padding: 12px 16px;
                margin: 4px 0px;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Message text
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(message_label)
        
        return bubble
    
    def create_ai_bubble(self):
        """Create AI message bubble"""
        bubble = QFrame()
        bubble.setObjectName("ai_bubble")
        bubble.setMaximumWidth(600)
        bubble.setStyleSheet("""
            QFrame#ai_bubble {
                background-color: #2D2D44;
                border-radius: 18px;
                padding: 12px 16px;
                margin: 4px 0px;
                border: 1px solid #3A3A52;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        # Sender header
        sender_label = QLabel(self.sender)
        sender_label.setStyleSheet("""
            QLabel {
                color: #A995F2;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(sender_label)
        
        # Message text
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #F1F5F9;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(message_label)
        
        return bubble


class ModernChatInput(QFrame):
    """Modern Material Design chat input area"""
    
    sendMessage = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the input area UI"""
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
                border-top: 1px solid #3A3A52;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)
        
        # Input container
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D44;
                border-radius: 24px;
                border: 2px solid #3A3A52;
            }
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 8, 16, 8)
        input_layout.setSpacing(8)
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message...")
        self.text_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #F1F5F9;
                font-size: 14px;
                font-weight: 400;
                padding: 8px 0px;
            }
            QLineEdit::placeholder {
                color: #A78BFA;
            }
        """)
        self.text_input.returnPressed.connect(self.send_message)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(60, 32)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #A995F2;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #8B7CE8;
            }
            QPushButton:pressed {
                background-color: #7C6AE4;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.text_input)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(input_container)
    
    def send_message(self):
        """Send message and clear input"""
        text = self.text_input.text().strip()
        if text:
            self.sendMessage.emit(text)
            self.text_input.clear()


class ModernSidebar(QFrame):
    """Modern Material Design sidebar"""
    
    newChat = pyqtSignal()
    loadChat = pyqtSignal(str)
    openSettings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the sidebar UI"""
        self.setFixedWidth(320)
        self.setStyleSheet("""
            QFrame {
                background-color: #2D2D44;
                border-right: 1px solid #3A3A52;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("Geode")
        header.setStyleSheet("""
            QLabel {
                color: #A995F2;
                font-size: 24px;
                font-weight: 700;
                padding: 8px 0px;
            }
        """)
        layout.addWidget(header)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setFixedHeight(44)
        new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #A995F2;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #8B7CE8;
            }
            QPushButton:pressed {
                background-color: #7C6AE4;
            }
        """)
        new_chat_btn.clicked.connect(self.newChat.emit)
        layout.addWidget(new_chat_btn)
        
        # Recent chats section
        recents_label = QLabel("RECENT CHATS")
        recents_label.setStyleSheet("""
            QLabel {
                color: #A78BFA;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 16px 8px 8px 8px;
            }
        """)
        layout.addWidget(recents_label)
        
        # Chat list
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 12px;
                margin: 2px 0px;
                color: #F1F5F9;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background-color: rgba(169, 149, 242, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(169, 149, 242, 0.2);
            }
        """)
        # Add some sample chats
        self.chat_list.addItems([
            "💬 Material Design Discussion",
            "📝 Note Organization Help",
            "🔍 Search Functionality",
            "⚙️ Settings Configuration"
        ])
        layout.addWidget(self.chat_list)
        
        layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFixedHeight(40)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A78BFA;
                border: 1px solid #3A3A52;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover {
                background-color: rgba(169, 149, 242, 0.1);
                border-color: #A995F2;
            }
        """)
        settings_btn.clicked.connect(self.openSettings.emit)
        layout.addWidget(settings_btn)


class ModernChatArea(QFrame):
    """Modern Material Design chat area"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the chat area UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A2E;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat messages scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1A1A2E;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2D2D44;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #A995F2;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8B7CE8;
            }
        """)
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 16, 0, 16)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Input area
        self.input_area = ModernChatInput()
        self.input_area.sendMessage.connect(self.add_user_message)
        layout.addWidget(self.input_area)
        
        # Add welcome message
        self.add_welcome_message()
    
    def add_welcome_message(self):
        """Add welcome message"""
        welcome_msg = ModernChatMessage(
            "Geode", 
            "Welcome to the redesigned Geode! 🎉\n\nI'm your AI assistant for managing your Obsidian vault. How can I help you today?",
            is_user=False
        )
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, welcome_msg)
        self.scroll_to_bottom()
    
    def add_user_message(self, message: str):
        """Add user message to chat"""
        user_msg = ModernChatMessage("You", message, is_user=True)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, user_msg)
        
        # Simulate AI response
        QTimer.singleShot(1000, lambda: self.add_ai_response(message))
        self.scroll_to_bottom()
    
    def add_ai_response(self, user_message: str):
        """Add AI response to chat"""
        responses = [
            "I understand you'd like help with that. Let me assist you!",
            "Great question! Here's what I can help you with...",
            "I can definitely help you organize your notes better.",
            "That's an interesting request. Let me provide some suggestions."
        ]
        
        import random
        response = random.choice(responses)
        
        ai_msg = ModernChatMessage("Geode", response, is_user=False)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, ai_msg)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll to bottom of chat"""
        QTimer.singleShot(10, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))


class ModernGeodeApp(QMainWindow):
    """Modern redesigned Geode application"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.apply_material_theme()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Geode - Modern Design")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ModernSidebar()
        main_layout.addWidget(self.sidebar)
        
        # Chat area
        self.chat_area = ModernChatArea()
        main_layout.addWidget(self.chat_area)
        
        # Connect signals
        self.sidebar.newChat.connect(self.new_chat)
        self.sidebar.openSettings.connect(self.open_settings)
    
    def apply_material_theme(self):
        """Apply Material Design theme"""
        if QT_MATERIAL_AVAILABLE:
            apply_stylesheet(QApplication.instance(), theme='dark_purple.xml')
            print("Material Design theme applied")
        else:
            print("Material Design not available, using custom theme")
    
    def new_chat(self):
        """Start new chat"""
        print("New chat started")
        # Clear messages and add welcome message
        # Implementation here
    
    def open_settings(self):
        """Open settings dialog"""
        print("Settings opened")
        # Implementation here


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = ModernGeodeApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()