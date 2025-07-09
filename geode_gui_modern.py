#!/usr/bin/env python3
"""
Geode GUI - Modern chat layout with profile pictures
Clean, modern chat interface with sleek design
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QListWidget, QListWidgetItem, QScrollArea,
    QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QDesktopServices

# Material Design Theme
try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ChatMessage(QFrame):
    """Modern chat message with profile picture and clean layout"""
    
    def __init__(self, sender: str, message: str, is_user: bool = False, show_avatar: bool = True):
        super().__init__()
        self.sender_name = sender
        self.message = message
        self.is_user = is_user
        self.show_avatar = show_avatar
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern chat message"""
        self.setContentsMargins(0, 0, 0, 0)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(16)
        
        # Profile picture (left side for both user and AI)
        avatar = self.create_avatar()
        main_layout.addWidget(avatar, 0)
        
        # Message content area
        content_area = self.create_content_area()
        main_layout.addWidget(content_area, 1)
        
        # Add some right padding
        main_layout.addSpacing(16)
    
    def create_avatar(self):
        """Create profile picture"""
        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        
        if self.is_user:
            # User gets rock emoji
            avatar_container.setStyleSheet("""
                QWidget {
                    background-color: #5865F2;
                    border-radius: 20px;
                    font-size: 20px;
                }
            """)
            
            layout = QVBoxLayout(avatar_container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            emoji_label = QLabel("🪨")
            emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emoji_label.setStyleSheet("""
                QLabel {
                    background: transparent;
                    font-size: 20px;
                }
            """)
            layout.addWidget(emoji_label)
        else:
            # AI gets purple circle with "G"
            avatar_container.setStyleSheet("""
                QWidget {
                    background-color: #A995F2;
                    border-radius: 20px;
                }
            """)
            
            layout = QVBoxLayout(avatar_container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            label = QLabel("G")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            layout.addWidget(label)
        
        return avatar_container
    
    def create_content_area(self):
        """Create message content area"""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        # Header with sender name and timestamp
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Sender name
        sender_label = QLabel(self.sender_name)
        sender_label.setStyleSheet(f"""
            QLabel {{
                color: {'#5865F2' if self.is_user else '#A995F2'};
                font-size: 14px;
                font-weight: 600;
            }}
        """)
        header_layout.addWidget(sender_label)
        
        # Timestamp (optional)
        timestamp_label = QLabel("now")
        timestamp_label.setStyleSheet("""
            QLabel {
                color: #72767d;
                font-size: 11px;
                font-weight: 400;
            }
        """)
        header_layout.addWidget(timestamp_label)
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # Message content
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #dcddde;
                font-size: 14px;
                line-height: 1.4;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        content_layout.addWidget(message_label)
        
        return content_widget


class ChatInputArea(QFrame):
    """Modern chat input area"""
    
    sendMessage = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern chat input area"""
        self.setFixedHeight(68)
        self.setStyleSheet("""
            QFrame {
                background-color: #36393f;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)
        
        # Input container with modern rounded rectangle
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #40444b;
                border-radius: 8px;
                border: none;
            }
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 0, 16, 0)
        input_layout.setSpacing(8)
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Message Geode...")
        self.text_input.setFixedHeight(44)
        self.text_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #dcddde;
                font-size: 14px;
                padding: 0px;
            }
            QLineEdit::placeholder {
                color: #72767d;
            }
        """)
        self.text_input.returnPressed.connect(self.send_message)
        
        input_layout.addWidget(self.text_input)
        
        # Send button (optional - can send with Enter)
        self.send_button = QPushButton("📤")
        self.send_button.setFixedSize(32, 32)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(input_container)
    
    def send_message(self):
        """Send message and clear input"""
        text = self.text_input.text().strip()
        if text:
            self.sendMessage.emit(text)
            self.text_input.clear()


class ModernSidebar(QFrame):
    """Modern sidebar for Geode"""
    
    newChat = pyqtSignal()
    openSettings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern sidebar"""
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # App header - clickable to open GitHub
        header = QPushButton("🪨 Geode")
        header.setFixedHeight(48)
        header.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
                border: none;
                text-align: left;
                padding: 8px 0px;
            }
            QPushButton:hover {
                color: #A995F2;
            }
        """)
        header.clicked.connect(self.open_github)
        layout.addWidget(header)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setFixedHeight(40)
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
        
        # Chat history section
        history_label = QLabel("RECENT CHATS")
        history_label.setStyleSheet("""
            QLabel {
                color: #8e9297;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px 0px;
            }
        """)
        layout.addWidget(history_label)
        
        # Chat history list
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
                padding: 10px 12px;
                margin: 2px 0px;
                color: #b9bbbe;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background-color: #36393f;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #5865F2;
                color: white;
            }
        """)
        
        # Add sample chat history
        sample_chats = [
            "💬 Material Design Help",
            "📝 Note Organization Tips", 
            "🔍 Search Best Practices",
            "📊 Vault Statistics",
            "🎯 Workflow Optimization"
        ]
        for chat in sample_chats:
            self.chat_list.addItem(chat)
        
        layout.addWidget(self.chat_list)
        
        layout.addStretch()
        
        # Bottom section with user info
        bottom_section = QFrame()
        bottom_section.setStyleSheet("""
            QFrame {
                background-color: #292b2f;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        # User info
        user_container = QFrame()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)
        
        # User avatar
        user_avatar = QWidget()
        user_avatar.setFixedSize(32, 32)
        user_avatar.setStyleSheet("""
            QWidget {
                background-color: #5865F2;
                border-radius: 16px;
            }
        """)
        
        avatar_layout = QVBoxLayout(user_avatar)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        avatar_emoji = QLabel("🪨")
        avatar_emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_emoji.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 16px;
            }
        """)
        avatar_layout.addWidget(avatar_emoji)
        
        user_layout.addWidget(user_avatar)
        
        # User name and status
        user_info = QWidget()
        user_info_layout = QVBoxLayout(user_info)
        user_info_layout.setContentsMargins(0, 0, 0, 0)
        user_info_layout.setSpacing(2)
        
        username = QLabel("You")
        username.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        user_info_layout.addWidget(username)
        
        
        user_layout.addWidget(user_info)
        user_layout.addStretch()
        
        bottom_layout.addWidget(user_container)
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFixedHeight(32)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #b9bbbe;
                border: 1px solid #40444b;
                border-radius: 6px;
                font-size: 13px;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover {
                background-color: #36393f;
                border-color: #A995F2;
                color: #ffffff;
            }
        """)
        settings_btn.clicked.connect(self.openSettings.emit)
        bottom_layout.addWidget(settings_btn)
        
        layout.addWidget(bottom_section)
    
    def open_github(self):
        """Open GitHub repository in browser"""
        QDesktopServices.openUrl(QUrl("https://github.com/KOPC149/obsidian-geode"))


class ChatArea(QFrame):
    """Modern chat area"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern chat area"""
        self.setStyleSheet("""
            QFrame {
                background-color: #36393f;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet("""
            QFrame {
                background-color: #36393f;
                border-bottom: 1px solid #40444b;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(8)
        
        # Chat info
        chat_name = QLabel("Chat")
        chat_name.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        header_layout.addWidget(chat_name)
        
        divider = QLabel("•")
        divider.setStyleSheet("""
            QLabel {
                color: #72767d;
                font-size: 14px;
                padding: 0 8px;
            }
        """)
        header_layout.addWidget(divider)
        
        description = QLabel("Chat with your AI assistant")
        description.setStyleSheet("""
            QLabel {
                color: #72767d;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(description)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #36393f;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2f3136;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #202225;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5865F2;
            }
        """)
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 16, 0, 16)
        self.messages_layout.setSpacing(4)  # Tight spacing for clean look
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)
        
        # Input area
        self.input_area = ChatInputArea()
        self.input_area.sendMessage.connect(self.add_user_message)
        layout.addWidget(self.input_area)
        
        # Add welcome message
        self.add_welcome_message()
    
    def add_welcome_message(self):
        """Add modern welcome message"""
        welcome_msg = ChatMessage(
            "Geode", 
            "Welcome to Geode! 🎉\n\nI'm your AI assistant for managing your Obsidian vault. I can help you:\n• Organize and structure your notes\n• Search for specific information\n• Answer questions about your content\n• Suggest improvements to your workflow\n\nWhat would you like to work on today?",
            is_user=False
        )
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, welcome_msg)
        self.scroll_to_bottom()
    
    def add_user_message(self, message: str):
        """Add user message"""
        user_msg = ChatMessage("You", message, is_user=True)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, user_msg)
        
        # Simulate AI response
        QTimer.singleShot(1000, lambda: self.add_ai_response(message))
        self.scroll_to_bottom()
    
    def add_ai_response(self, user_message: str):
        """Add AI response"""
        responses = [
            "Great question! Let me help you with that. Here's what I'd recommend based on best practices for note organization...",
            "I can definitely assist you with that! Here are a few approaches we could take to solve this effectively.",
            "That's an excellent point. Let me break this down into actionable steps that you can implement right away.",
            "Perfect! I have some specific suggestions that should work well for your use case. Let's start with the most important ones."
        ]
        
        import random
        response = random.choice(responses)
        
        ai_msg = ChatMessage("Geode", response, is_user=False)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, ai_msg)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll to bottom"""
        def scroll():
            scrollbar = self.scroll_area.verticalScrollBar()
            if scrollbar is not None:
                scrollbar.setValue(scrollbar.maximum())
        
        QTimer.singleShot(50, scroll)


class ModernGeodeApp(QMainWindow):
    """Modern Geode application"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Geode")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        # Modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #36393f;
                color: #dcddde;
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
        self.sidebar = ModernSidebar()
        main_layout.addWidget(self.sidebar)
        
        # Chat area
        self.chat_area = ChatArea()
        main_layout.addWidget(self.chat_area)
        
        # Connect signals
        self.sidebar.openSettings.connect(self.open_settings)
    
    def open_settings(self):
        """Open settings"""
        print("Settings opened")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set font
    app.setFont(QFont("Segoe UI", 10))
    
    # Create and show window
    window = ModernGeodeApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()