#!/usr/bin/env python3
"""
Material Design Examples for Geode App
Quick visual examples to test different Material Design themes and layouts
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QListWidget, QFrame, QSplitter,
    QTabWidget, QGroupBox, QLineEdit, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False
    print("qt-material not installed. Install with: pip install qt-material")


class MaterialDesignDemo(QMainWindow):
    """Demo window showing Material Design layouts for Geode"""
    
    def __init__(self, theme='dark_purple'):
        super().__init__()
        self.theme = theme
        self.setup_ui()
        self.setWindowTitle(f"Geode Material Design Demo - {theme}")
        self.setGeometry(100, 100, 1200, 800)
    
    def setup_ui(self):
        """Setup the demo UI with Material Design components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - horizontal splitter like current Geode
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)
        
        # Right content area
        content_area = self.create_content_area()
        splitter.addWidget(content_area)
        
        # Set splitter sizes
        splitter.setSizes([300, 900])
    
    def create_sidebar(self):
        """Create Material Design sidebar"""
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setFixedHeight(48)
        new_chat_btn.setObjectName("primary_button")
        layout.addWidget(new_chat_btn)
        
        # Recents label
        recents_label = QLabel("RECENTS")
        recents_label.setObjectName("section_label")
        layout.addWidget(recents_label)
        
        # Chat list
        chat_list = QListWidget()
        chat_list.setObjectName("chat_list")
        chat_list.addItems([
            "💬 Chat about Material Design",
            "📝 Notes organization help",
            "🔍 Search functionality",
            "⚙️ Settings configuration",
            "🎨 Theme customization"
        ])
        layout.addWidget(chat_list)
        
        layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFixedHeight(40)
        settings_btn.setObjectName("settings_button")
        layout.addWidget(settings_btn)
        
        return sidebar
    
    def create_content_area(self):
        """Create Material Design content area"""
        content = QFrame()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Chat area
        chat_area = self.create_chat_area()
        layout.addWidget(chat_area)
        
        # Input area
        input_area = self.create_input_area()
        layout.addWidget(input_area)
        
        return content
    
    def create_chat_area(self):
        """Create Material Design chat area"""
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Sample messages
        messages = [
            ("user", "Hello! I'd like to organize my notes better."),
            ("assistant", "I'd be happy to help you organize your notes! Here are some suggestions:\n\n1. Use consistent naming conventions\n2. Create folder structures by topic\n3. Add tags to make notes searchable\n4. Use templates for recurring note types"),
            ("user", "That's great! Can you help me create a template?"),
            ("assistant", "Absolutely! Let me create a note template for you...")
        ]
        
        for sender, text in messages:
            message_card = self.create_message_card(sender, text)
            layout.addWidget(message_card)
        
        layout.addStretch()
        return chat_widget
    
    def create_message_card(self, sender, text):
        """Create Material Design message card"""
        card = QFrame()
        card.setObjectName("message_card")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Sender label
        sender_label = QLabel("You" if sender == "user" else "Geode")
        sender_label.setObjectName("sender_label")
        layout.addWidget(sender_label)
        
        # Message text
        message_text = QLabel(text)
        message_text.setWordWrap(True)
        message_text.setObjectName("message_text")
        layout.addWidget(message_text)
        
        return card
    
    def create_input_area(self):
        """Create Material Design input area"""
        input_frame = QFrame()
        input_frame.setFixedHeight(80)
        input_frame.setObjectName("input_frame")
        
        layout = QHBoxLayout(input_frame)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(12)
        
        # Text input
        text_input = QLineEdit()
        text_input.setPlaceholderText("Type your message here...")
        text_input.setFixedHeight(48)
        text_input.setObjectName("message_input")
        layout.addWidget(text_input)
        
        # Send button
        send_btn = QPushButton("Send")
        send_btn.setFixedSize(80, 48)
        send_btn.setObjectName("send_button")
        layout.addWidget(send_btn)
        
        return input_frame


class ThemeSelector(QWidget):
    """Theme selector widget for quick theme switching"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setWindowTitle("Geode Material Design Theme Selector")
        self.setGeometry(50, 50, 400, 300)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Choose Material Design Theme")
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Theme buttons
        themes = [
            ("Dark Purple", "dark_purple"),
            ("Dark Teal", "dark_teal"),
            ("Dark Blue", "dark_blue"),
            ("Light Purple", "light_purple"),
            ("Light Teal", "light_teal"),
            ("Light Blue", "light_blue")
        ]
        
        for name, theme_id in themes:
            btn = QPushButton(name)
            btn.setFixedHeight(44)
            btn.setObjectName("theme_button")
            btn.clicked.connect(lambda checked, t=theme_id: self.show_theme_demo(t))
            layout.addWidget(btn)
        
        layout.addStretch()
    
    def show_theme_demo(self, theme):
        """Show demo with selected theme"""
        if not QT_MATERIAL_AVAILABLE:
            print(f"Would show {theme} theme (qt-material not available)")
            return
        
        demo = MaterialDesignDemo(theme)
        apply_stylesheet(QApplication.instance(), theme=f'{theme}.xml')
        demo.show()


def main():
    """Main function to run the Material Design examples"""
    app = QApplication(sys.argv)
    
    if QT_MATERIAL_AVAILABLE:
        # Apply default theme
        apply_stylesheet(app, theme='dark_purple.xml')
    else:
        # Basic styling without qt-material
        app.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
                color: #f1f5f9;
            }
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QFrame {
                background-color: #2d2d44;
                border-radius: 8px;
            }
            QLabel {
                color: #f1f5f9;
            }
            QLineEdit {
                background-color: #2d2d44;
                border: 2px solid #475569;
                border-radius: 8px;
                padding: 8px;
                color: #f1f5f9;
            }
            QListWidget {
                background-color: #2d2d44;
                border: none;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #7c3aed;
            }
        """)
    
    # Show theme selector
    selector = ThemeSelector()
    selector.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()