#!/usr/bin/env python3
"""
Custom Material Design theme for Geode
Using RGB(169, 149, 242) as the primary purple color
"""

import sys
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet


def create_geode_material_theme():
    """Create a custom Material Design theme with Geode's purple color"""
    
    # Your custom purple: RGB(169, 149, 242) = #A995F2
    custom_colors = {
        'primaryColor': '#A995F2',           # Your custom purple
        'primaryLightColor': '#C4B5F7',      # Lighter version
        'primaryDarkColor': '#8B7CE8',       # Darker version
        'secondaryColor': '#2563EB',         # Keep your blue accent
        'secondaryLightColor': '#3B82F6',    # Light blue
        'secondaryDarkColor': '#1E40AF',     # Dark blue
        'primaryTextColor': '#F1F5F9',       # Light text
        'secondaryTextColor': '#A78BFA',     # Purple-tinted text
        'surfaceColor': '#2D2D44',           # Your surface color
        'backgroundColor': '#1A1A2E',        # Your background color
    }
    
    return custom_colors


def apply_geode_material_theme(app):
    """Apply the custom Geode Material Design theme"""
    
    # Start with dark_purple as base
    apply_stylesheet(app, theme='dark_purple.xml')
    
    # Get custom colors
    custom_colors = create_geode_material_theme()
    
    # Additional custom styling
    additional_styles = f"""
    /* Custom Geode Material Design Overrides */
    
    /* Primary buttons with your custom purple */
    QPushButton {{
        background-color: {custom_colors['primaryColor']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: {custom_colors['primaryDarkColor']};
    }}
    
    QPushButton:pressed {{
        background-color: {custom_colors['primaryDarkColor']};
    }}
    
    /* Chat message cards with elevated Material Design look */
    QFrame[class="message_card"] {{
        background-color: {custom_colors['surfaceColor']};
        border: none;
        border-radius: 12px;
        padding: 16px;
    }}
    
    /* Input field with Material Design styling */
    QLineEdit, QTextEdit {{
        background-color: {custom_colors['surfaceColor']};
        border: 2px solid transparent;
        border-radius: 8px;
        padding: 12px;
        color: {custom_colors['primaryTextColor']};
        font-size: 14px;
    }}
    
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {custom_colors['primaryColor']};
    }}
    
    /* Sidebar with Material Design elevation */
    QFrame[class="sidebar"] {{
        background-color: {custom_colors['surfaceColor']};
        border: none;
    }}
    
    /* List items with Material Design ripple effect simulation */
    QListWidget::item {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        padding: 12px;
        margin: 2px 0px;
    }}
    
    QListWidget::item:hover {{
        background-color: rgba(169, 149, 242, 0.1);
    }}
    
    QListWidget::item:selected {{
        background-color: {custom_colors['primaryColor']};
        color: white;
    }}
    
    /* Typography with Material Design font weights */
    QLabel[class="sender_label"] {{
        font-weight: 600;
        font-size: 13px;
        color: {custom_colors['primaryColor']};
    }}
    
    QLabel[class="message_text"] {{
        font-weight: 400;
        font-size: 14px;
        line-height: 1.4;
        color: {custom_colors['primaryTextColor']};
    }}
    
    /* Section headers */
    QLabel[class="section_label"] {{
        font-weight: 700;
        font-size: 11px;
        color: {custom_colors['secondaryTextColor']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Elevated cards with shadow simulation */
    QFrame[class="elevated_card"] {{
        background-color: {custom_colors['surfaceColor']};
        border: none;
        border-radius: 12px;
        /* Shadow simulation with border */
        border: 1px solid rgba(169, 149, 242, 0.1);
    }}
    """
    
    # Apply additional styles
    current_stylesheet = app.styleSheet()
    app.setStyleSheet(current_stylesheet + additional_styles)


def demo_theme():
    """Demo function to test the custom theme"""
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QLabel, QLineEdit, QListWidget, QFrame
    )
    
    class ThemeDemo(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Geode Material Design Theme Demo")
            self.setGeometry(100, 100, 800, 600)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 24, 24, 24)
            
            # Header
            header = QLabel("Geode Material Design Theme")
            header.setProperty("class", "sender_label")
            layout.addWidget(header)
            
            # Sample message card
            card = QFrame()
            card.setProperty("class", "message_card")
            card_layout = QVBoxLayout(card)
            
            sender_label = QLabel("Geode")
            sender_label.setProperty("class", "sender_label")
            card_layout.addWidget(sender_label)
            
            message_text = QLabel("This is how your chat messages will look with the new Material Design theme using your custom purple color RGB(169, 149, 242)!")
            message_text.setProperty("class", "message_text")
            message_text.setWordWrap(True)
            card_layout.addWidget(message_text)
            
            layout.addWidget(card)
            
            # Input area
            input_layout = QHBoxLayout()
            
            input_field = QLineEdit()
            input_field.setPlaceholderText("Type your message here...")
            input_layout.addWidget(input_field)
            
            send_btn = QPushButton("Send")
            input_layout.addWidget(send_btn)
            
            layout.addLayout(input_layout)
            
            # Sample list
            list_widget = QListWidget()
            list_widget.addItems([
                "💬 Chat about Material Design",
                "📝 Notes organization",
                "🎨 Custom themes",
                "⚙️ Settings"
            ])
            layout.addWidget(list_widget)
    
    app = QApplication(sys.argv)
    
    # Apply the custom theme
    apply_geode_material_theme(app)
    
    demo = ThemeDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    demo_theme()