#!/usr/bin/env python3
"""
Geode GUI v2 - Completely redesigned layout based on 2024 best practices
Following modern chat design patterns with proper spacing and typography
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

# Design constants based on 2024 best practices
SPACING = {
    'xs': 4,
    'sm': 8, 
    'md': 16,
    'lg': 24,
    'xl': 32
}

COLORS = {
    'background': '#0F0F0F',      # True dark for 2024
    'surface': '#1A1A1A',        # Card backgrounds
    'surface_elevated': '#242424', # Elevated surfaces
    'primary': '#A995F2',         # Your custom purple
    'primary_hover': '#8B7CE8',   # Hover state
    'text_primary': '#FFFFFF',    # High contrast white
    'text_secondary': '#A0A0A0',  # Secondary text
    'text_muted': '#666666',      # Muted text
    'border': '#2A2A2A',          # Subtle borders
    'accent': '#2563EB',          # Blue accent
    'success': '#10B981',         # Green
    'warning': '#F59E0B',         # Orange
}


class ModernMessageBubble(QFrame):
    """2024-style message bubble with proper spacing and typography"""
    
    def __init__(self, sender: str, message: str, is_user: bool = False, timestamp: str = ""):
        super().__init__()
        self.sender = sender
        self.message = message
        self.is_user = is_user
        self.timestamp = timestamp
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern message bubble"""
        self.setContentsMargins(0, 0, 0, 0)
        
        # Main container with proper margins
        container = QFrame()
        container.setContentsMargins(SPACING['lg'], SPACING['sm'], SPACING['lg'], SPACING['sm'])
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        
        bubble_layout = QHBoxLayout(container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(SPACING['md'])
        
        if self.is_user:
            # User messages - right aligned with max width
            bubble_layout.addStretch(1)
            bubble = self.create_user_bubble()
            bubble_layout.addWidget(bubble, 0)
        else:
            # AI messages - left aligned with avatar space
            avatar = self.create_avatar()
            bubble_layout.addWidget(avatar, 0)
            bubble = self.create_ai_bubble()
            bubble_layout.addWidget(bubble, 0)
            bubble_layout.addStretch(1)
    
    def create_avatar(self):
        """Create AI avatar"""
        avatar = QFrame()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary']};
                border-radius: 16px;
                border: none;
            }}
        """)
        
        # Add "G" label for Geode
        layout = QVBoxLayout(avatar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("G")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(label)
        
        return avatar
    
    def create_user_bubble(self):
        """Create user message bubble with 2024 styling"""
        bubble = QFrame()
        bubble.setMaximumWidth(480)  # Max width for readability
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary']};
                border-radius: 18px;
                border: none;
                padding: {SPACING['md']}px {SPACING['md']}px;
            }}
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(SPACING['sm'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        layout.setSpacing(SPACING['xs'])
        
        # Message text with proper typography
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.5;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(message_label)
        
        return bubble
    
    def create_ai_bubble(self):
        """Create AI message bubble with 2024 styling"""
        bubble = QFrame()
        bubble.setMaximumWidth(560)  # Slightly wider for AI responses
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_elevated']};
                border-radius: 18px;
                border: 1px solid {COLORS['border']};
                padding: {SPACING['md']}px {SPACING['md']}px;
            }}
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(SPACING['sm'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        layout.setSpacing(SPACING['sm'])
        
        # Sender header with bold typography (2024 trend)
        sender_label = QLabel(self.sender)
        sender_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['primary']};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(sender_label)
        
        # Message text
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 400;
                line-height: 1.5;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(message_label)
        
        return bubble


class ModernInputArea(QFrame):
    """2024-style input area with pill-shaped design"""
    
    sendMessage = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern input area"""
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Modern pill-shaped input container
        input_container = QFrame()
        input_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_elevated']};
                border: 2px solid {COLORS['border']};
                border-radius: 28px;
            }}
            QFrame:focus-within {{
                border-color: {COLORS['primary']};
            }}
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['sm'], SPACING['sm'])
        input_layout.setSpacing(SPACING['sm'])
        
        # Text input with modern styling
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Message Geode...")
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 400;
                padding: {SPACING['sm']}px 0px;
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """)
        self.text_input.returnPressed.connect(self.send_message)
        
        # Modern send button
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(64, 36)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.text_input, 1)
        input_layout.addWidget(self.send_button, 0)
        
        layout.addWidget(input_container)
    
    def send_message(self):
        """Send message and clear input"""
        text = self.text_input.text().strip()
        if text:
            self.sendMessage.emit(text)
            self.text_input.clear()


class ModernSidebar(QFrame):
    """2024-style sidebar with proper hierarchy"""
    
    newChat = pyqtSignal()
    loadChat = pyqtSignal(str)
    openSettings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern sidebar"""
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['lg'], SPACING['md'], SPACING['lg'])
        layout.setSpacing(SPACING['lg'])
        
        # Header with bold typography (2024 trend)
        header = QLabel("Geode")
        header.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 28px;
                font-weight: 800;
                padding: {SPACING['sm']}px 0px;
            }}
        """)
        layout.addWidget(header)
        
        # New chat button with modern styling
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setFixedHeight(44)
        new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        new_chat_btn.clicked.connect(self.newChat.emit)
        layout.addWidget(new_chat_btn)
        
        # Section spacing
        layout.addSpacing(SPACING['md'])
        
        # Recent chats section with proper typography
        recents_label = QLabel("RECENT CHATS")
        recents_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: {SPACING['sm']}px {SPACING['sm']}px;
            }}
        """)
        layout.addWidget(recents_label)
        
        # Chat list with modern styling
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
                padding: 0px;
            }}
            QListWidget::item {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: {SPACING['md']}px {SPACING['sm']}px;
                margin: {SPACING['xs']}px 0px;
                color: {COLORS['text_secondary']};
                font-size: 14px;
                font-weight: 400;
                min-height: 20px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(169, 149, 242, 0.1);
                color: {COLORS['text_primary']};
            }}
            QListWidget::item:selected {{
                background-color: rgba(169, 149, 242, 0.2);
                color: {COLORS['text_primary']};
            }}
        """)
        
        # Add sample chats
        sample_chats = [
            "💬 Material Design Discussion",
            "📝 Note Organization Tips", 
            "🔍 Advanced Search Help",
            "⚙️ Configuration Settings",
            "🎨 Theme Customization"
        ]
        for chat in sample_chats:
            self.chat_list.addItem(chat)
        
        layout.addWidget(self.chat_list)
        
        # Push settings to bottom
        layout.addStretch()
        
        # Settings button with subtle styling
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFixedHeight(40)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding-left: {SPACING['md']}px;
            }}
            QPushButton:hover {{
                background-color: rgba(169, 149, 242, 0.05);
                border-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        settings_btn.clicked.connect(self.openSettings.emit)
        layout.addWidget(settings_btn)


class ModernChatArea(QFrame):
    """2024-style chat area with proper message spacing"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern chat area"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat messages scroll area with modern scrollbar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, SPACING['lg'], 0, SPACING['lg'])
        self.messages_layout.setSpacing(SPACING['md'])
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Modern input area
        self.input_area = ModernInputArea()
        self.input_area.sendMessage.connect(self.add_user_message)
        layout.addWidget(self.input_area)
        
        # Add welcome message
        self.add_welcome_message()
    
    def add_welcome_message(self):
        """Add modern welcome message"""
        welcome_msg = ModernMessageBubble(
            "Geode", 
            "Welcome to the new Geode! ✨\n\nI'm your AI assistant for managing your Obsidian vault. I can help you organize notes, find information, and much more.\n\nWhat would you like to work on today?",
            is_user=False
        )
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, welcome_msg)
        self.scroll_to_bottom()
    
    def add_user_message(self, message: str):
        """Add user message with modern styling"""
        user_msg = ModernMessageBubble("You", message, is_user=True)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, user_msg)
        
        # Simulate AI response with delay
        QTimer.singleShot(800, lambda: self.add_ai_response(message))
        self.scroll_to_bottom()
    
    def add_ai_response(self, user_message: str):
        """Add AI response with modern styling"""
        responses = [
            "I'd be happy to help you with that! Let me provide you with some detailed guidance.\n\nHere are a few approaches we could take:",
            "That's a great question! Based on your request, I can suggest several strategies that might work well for your use case.",
            "Excellent! I can definitely assist you with organizing your notes more effectively. Let me share some best practices.",
            "I understand what you're looking for. Here's how we can approach this step by step to get the best results."
        ]
        
        import random
        response = random.choice(responses)
        
        ai_msg = ModernMessageBubble("Geode", response, is_user=False)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, ai_msg)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Smooth scroll to bottom"""
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))


class GeodeAppV2(QMainWindow):
    """Completely redesigned Geode application following 2024 best practices"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main application UI"""
        self.setWindowTitle("Geode")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        # Set dark background
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
            }}
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with no spacing
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
    
    def new_chat(self):
        """Start new chat"""
        print("Starting new chat...")
        # Clear messages and add welcome message
    
    def open_settings(self):
        """Open settings dialog"""
        print("Opening settings...")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Apply Material Design if available
    if QT_MATERIAL_AVAILABLE:
        apply_stylesheet(app, theme='dark_purple.xml')
    
    # Set modern font
    font = QFont("SF Pro Display", 10)  # macOS system font
    if not font.exactMatch():
        font = QFont("Segoe UI", 10)  # Windows fallback
    if not font.exactMatch():
        font = QFont("Inter", 10)  # Modern web font
    app.setFont(font)
    
    # Create and show main window
    window = GeodeAppV2()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()