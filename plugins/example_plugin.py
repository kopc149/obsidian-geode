"""
Example Geode Plugin
This demonstrates how to create a plugin for Geode.
"""

from datetime import datetime

class ExamplePlugin:
    """Example plugin with utility functions"""
    
    def get_name(self) -> str:
        return "example_utilities"
    
    def get_description(self) -> str:
        return "Example plugin with basic utility functions"
    
    def get_tools(self) -> list:
        return [self.get_current_time, self.calculate_word_count, self.reverse_text]
    
    def get_current_time(self) -> str:
        """Get the current date and time"""
        try:
            return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        except Exception as e:
            return f"Error getting current time: {e}"
    
    def calculate_word_count(self, text: str) -> str:
        """Calculate word count for given text"""
        try:
            if not text:
                return "No text provided"
            
            words = len(text.split())
            chars = len(text)
            chars_no_spaces = len(text.replace(' ', ''))
            lines = len(text.split('\n'))
            
            return f"Text statistics:\n- Words: {words}\n- Characters: {chars}\n- Characters (no spaces): {chars_no_spaces}\n- Lines: {lines}"
        except Exception as e:
            return f"Error calculating word count: {e}"
    
    def reverse_text(self, text: str) -> str:
        """Reverse the given text"""
        try:
            if not text:
                return "No text provided"
            return f"Reversed text: {text[::-1]}"
        except Exception as e:
            return f"Error reversing text: {e}"
