# geode_bridge/__init__.py

"""
Geode Bridge - Backend package for the Geode Obsidian/Gemini AI application.

This package provides the core functionality for:
- Configuration management
- Obsidian API integration
- Gemini AI integration
- Plugin system
- Chat history management
- Error handling
"""

from .bridge import GeodeBridge
from .config import Config
from .exceptions import (
    GeodeException,
    ConfigurationError,
    FileOperationError,
    ObsidianError,
    ObsidianConnectionError,
    ObsidianAuthError,
    ObsidianAPIError,
    GeminiError,
    GeminiAuthError,
    GeminiAPIError,
    PluginError
)
from .history import ChatHistoryManager, ChatSession, ChatMessage
from .obsidian_api import ObsidianAPI, ObsidianTools
from .plugins import PluginManager, PluginProtocol
from .mcp_client import MCPClient, MCPServerConfig
from .ai_client import AIClient, create_ai_client

__version__ = "1.0.0"
__author__ = "Geode Development Team"

__all__ = [
    "GeodeBridge",
    "Config",
    "GeodeException",
    "ConfigurationError", 
    "FileOperationError",
    "ObsidianError",
    "ObsidianConnectionError",
    "ObsidianAuthError", 
    "ObsidianAPIError",
    "GeminiError",
    "GeminiAuthError",
    "GeminiAPIError",
    "PluginError",
    "ChatHistoryManager",
    "ChatSession",
    "ChatMessage",
    "ObsidianAPI",
    "ObsidianTools",
    "PluginManager",
    "PluginProtocol",
    "MCPClient",
    "MCPServerConfig",
    "AIClient",
    "create_ai_client"
]