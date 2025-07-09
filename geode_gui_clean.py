#!/usr/bin/env python3
"""
Geode GUI - Clean, minimal design that actually works
Based on successful chat applications with clean aesthetics
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
    QMenu, QTabWidget, QGroupBox, QCheckBox, QComboBox, QStackedWidget,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool, QTimer, QSize
from PyQt6.QtGui import QKeyEvent, QFont, QPalette, QPixmap, QPainter, QBrush, QColor

# Material Design Theme
try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class CleanMessageCard(QFrame):
    """Clean, minimal message card with better chat-like layout"""
    
    def __init__(self, sender: str, message: str, is_user: bool = False):
        super().__init__()
        self.sender = sender
        self.message = message
        self.is_user = is_user
        self.setup_ui()
    
    def setup_ui(self):
        """Setup clean message card with proper chat spacing"""
        self.setContentsMargins(0, 0, 0, 0)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 4, 16, 4)
        main_layout.setSpacing(0)
        
        if self.is_user:
            # User messages - right side with max width
            main_layout.addStretch(1)
            message_widget = self.create_user_message()
            main_layout.addWidget(message_widget)
            main_layout.addSpacing(8)  # Small right margin
        else:
            # AI messages - left side with avatar
            main_layout.addSpacing(8)  # Small left margin
            avatar = self.create_avatar()
            main_layout.addWidget(avatar, 0)
            main_layout.addSpacing(12)
            message_widget = self.create_ai_message()
            main_layout.addWidget(message_widget)
            main_layout.addStretch(1)
    
    def create_avatar(self):
        """Create small AI avatar"""
        avatar_container = QWidget()
        avatar_container.setFixedSize(32, 32)
        
        # Simple circular avatar
        avatar_container.setStyleSheet("""
            QWidget {
                background-color: #A995F2;
                border-radius: 16px;
            }
        """)
        
        # Add "G" label
        layout = QVBoxLayout(avatar_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("G")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: 700;
                background: transparent;
            }
        """)
        layout.addWidget(label)
        
        return avatar_container
    
    def create_user_message(self):
        """Create user message bubble"""
        bubble = QFrame()
        bubble.setMaximumWidth(450)
        bubble.setStyleSheet("""
            QFrame {
                background-color: #A995F2;
                border-radius: 18px;
                padding: 10px 14px;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(message_label)
        
        return bubble
    
    def create_ai_message(self):
        """Create AI message without bubble - cleaner look"""
        container = QFrame()
        container.setMaximumWidth(550)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Sender name
        sender_label = QLabel(self.sender)
        sender_label.setStyleSheet("""
            QLabel {
                color: #A995F2;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        layout.addWidget(sender_label)
        
        # Message content - no bubble for cleaner look
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #E8E8E8;
                font-size: 14px;
                background: transparent;
                border: none;
                padding: 2px 0px;
            }
        """)
        layout.addWidget(message_label)
        
        return container


class CleanInputArea(QFrame):
    """Clean input area with modern styling"""
    
    sendMessage = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup clean input area"""
        self.setFixedHeight(70)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-top: 1px solid #333333;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)
        
        # Input field
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setFixedHeight(40)
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A;
                border: 1px solid #404040;
                border-radius: 20px;
                padding: 0 16px;
                color: #F1F5F9;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #A995F2;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        self.text_input.returnPressed.connect(self.send_message)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(70, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #A995F2;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #8B7CE8;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        layout.addWidget(self.text_input)
        layout.addWidget(self.send_button)
    
    def send_message(self):
        """Send message and clear input"""
        text = self.text_input.text().strip()
        if text:
            self.sendMessage.emit(text)
            self.text_input.clear()


class CleanSidebar(QFrame):
    """Clean, minimal sidebar"""
    
    newChat = pyqtSignal()
    openSettings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup clean sidebar"""
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-right: 1px solid #333333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Geode")
        title.setStyleSheet("""
            QLabel {
                color: #F1F5F9;
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(title)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setFixedHeight(36)
        new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #A995F2;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #8B7CE8;
            }
        """)
        new_chat_btn.clicked.connect(self.newChat.emit)
        layout.addWidget(new_chat_btn)
        
        # Spacing
        layout.addSpacing(8)
        
        # Recent chats
        recents_label = QLabel("Recent")
        recents_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
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
                border-radius: 6px;
                padding: 8px 12px;
                margin: 1px 0;
                color: #CCCCCC;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background-color: #2A2A2A;
                color: #F1F5F9;
            }
            QListWidget::item:selected {
                background-color: #A995F2;
                color: white;
            }
        """)
        
        # Add sample chats
        sample_chats = [
            "💬 Design Discussion",
            "📝 Note Organization", 
            "🔍 Search Help",
            "⚙️ Settings"
        ]
        for chat in sample_chats:
            self.chat_list.addItem(chat)
        
        layout.addWidget(self.chat_list)
        layout.addStretch()
        
        # Settings
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFixedHeight(32)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888888;
                border: 1px solid #333333;
                border-radius: 6px;
                font-size: 13px;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                color: #F1F5F9;
                border-color: #A995F2;
            }
        """)
        settings_btn.clicked.connect(self.openSettings.emit)
        layout.addWidget(settings_btn)


class CleanChatArea(QFrame):
    """Clean chat area with proper message display"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup clean chat area"""
        self.setStyleSheet("""
            QFrame {
                background-color: #121212;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #121212;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #444444;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A995F2;
            }
        """)
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 20, 0, 20)
        self.messages_layout.setSpacing(8)  # Tighter spacing between messages
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Input area
        self.input_area = CleanInputArea()
        self.input_area.sendMessage.connect(self.add_user_message)
        layout.addWidget(self.input_area)
        
        # Add welcome message
        self.add_welcome_message()
    
    def add_welcome_message(self):
        """Add welcome message"""
        welcome_msg = CleanMessageCard(
            "Geode", 
            "Hi! I'm your AI assistant for managing your Obsidian vault. I can help you organize notes, search for information, and answer questions about your content.\n\nWhat would you like to work on?",
            is_user=False
        )
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, welcome_msg)
        # Add some spacing after welcome message
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, QWidget())
        self.scroll_to_bottom()
    
    def add_user_message(self, message: str):
        """Add user message"""
        user_msg = CleanMessageCard("You", message, is_user=True)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, user_msg)
        
        # Simulate AI response
        QTimer.singleShot(1000, lambda: self.add_ai_response(message))
        self.scroll_to_bottom()
    
    def add_ai_response(self, user_message: str):
        """Add AI response"""
        responses = [
            "I'd be happy to help you with that! Let me provide some guidance based on your request.",
            "That's a great question. Here's what I can suggest to help you get started.",
            "I can definitely assist you with organizing your notes. Here are some best practices.",
            "Let me help you with that. Here's a step-by-step approach we can take."
        ]
        
        import random
        response = random.choice(responses)
        
        ai_msg = CleanMessageCard("Geode", response, is_user=False)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, ai_msg)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll to bottom"""
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))


class CleanGeodeApp(QMainWindow):
    """Clean, professional Geode application"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Geode")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(800, 500)
        
        # Main styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #F1F5F9;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = CleanSidebar()
        main_layout.addWidget(self.sidebar)
        
        # Chat area
        self.chat_area = CleanChatArea()
        main_layout.addWidget(self.chat_area)
        
        # Connect signals
        self.sidebar.newChat.connect(self.new_chat)
        self.sidebar.openSettings.connect(self.open_settings)
    
    def new_chat(self):
        """Start new chat"""
        print("New chat started")
    
    def open_settings(self):
        """Open settings"""
        print("Settings opened")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set a clean, modern font
    app.setFont(QFont("Helvetica", 10))
    
    # Apply material theme if available (but don't rely on it)
    if QT_MATERIAL_AVAILABLE:
        try:
            apply_stylesheet(app, theme='dark_purple.xml')
        except:
            pass  # Fallback to our custom styling
    
    # Create and show window
    window = CleanGeodeApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()