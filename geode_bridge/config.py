# geode_bridge/config.py

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

from PyQt6.QtCore import QMutex, QMutexLocker
from .exceptions import ConfigurationError, FileOperationError

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """
    Configuration management for the Geode application.
    
    This class handles loading, validation, and saving of application configuration.
    It supports environment variable overrides and thread-safe operations.
    """
    
    # API Configuration
    gemini_api_key: str = ""
    claude_api_key: str = ""
    openai_api_key: str = ""
    cohere_api_key: str = ""
    mistral_api_key: str = ""
    perplexity_api_key: str = ""
    together_api_key: str = ""
    obsidian_api_key: str = ""
    
    # Local/Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # AI Model Configuration
    ai_provider: str = "gemini"  # gemini, claude, openai, cohere, mistral, ollama, perplexity, together
    model_name: str = "gemini-2.5-pro"
    
    # Obsidian Connection Settings
    obsidian_port: str = "27124"
    obsidian_host: str = "127.0.0.1"
    verify_ssl: bool = False
    request_timeout: int = 30
    
    # Application Behavior
    plugin_directory: str = "plugins"
    chat_history_file: str = "chat_history.json"
    max_chat_history: int = 50
    max_file_cache_depth: int = 5
    allowed_file_extensions: List[str] = None
    
    # Logging Configuration
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # UI Settings
    theme_name: str = "dark"
    font_size: int = 14
    
    # Performance Settings
    auto_save_drafts: bool = True
    draft_save_interval: int = 30
    enable_rate_limiting: bool = True
    api_calls_per_minute: int = 60
    cache_ttl_seconds: int = 300
    enable_metrics: bool = True
    keyboard_shortcuts_enabled: bool = True
    
    # MCP Integration (Optional)
    enable_mcp: bool = True
    mcp_config_file: str = "mcp_servers.json"
    
    def __post_init__(self):
        """Initialize default values and thread-safe mutex."""
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = ['.md', '.txt', '.json', '.csv', '.yaml', '.yml']
        self._file_mutex = QMutex()
    
    @classmethod
    def load(cls) -> 'Config':
        """
        Load configuration from file and environment variables.
        
        Returns:
            Config: Loaded configuration instance
            
        Raises:
            ConfigurationError: If configuration file is invalid
        """
        config_file = Path("config.json")
        config_data = {}
        
        # Load from file if it exists
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                logger.info("Configuration loaded from config.json")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load config file: {e}")
                raise ConfigurationError(f"Failed to load configuration file: {e}")
        
        # Apply environment variable overrides
        config_data = cls._apply_env_overrides(config_data)
        
        # Filter out invalid keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_config_data = {k: v for k, v in config_data.items() if k in valid_keys}

        return cls(**filtered_config_data)
    
    @classmethod
    def _apply_env_overrides(cls, config_data: dict) -> dict:
        """
        Apply environment variable overrides to configuration data.
        
        Args:
            config_data: Base configuration data
            
        Returns:
            dict: Configuration data with environment overrides applied
        """
        env_overrides = {
            'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            'claude_api_key': os.getenv('CLAUDE_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'cohere_api_key': os.getenv('COHERE_API_KEY'),
            'mistral_api_key': os.getenv('MISTRAL_API_KEY'),
            'perplexity_api_key': os.getenv('PERPLEXITY_API_KEY'),
            'together_api_key': os.getenv('TOGETHER_API_KEY'),
            'obsidian_api_key': os.getenv('OBSIDIAN_API_KEY'),
            'ollama_base_url': os.getenv('OLLAMA_BASE_URL'),
            'ai_provider': os.getenv('AI_PROVIDER'),
            'model_name': os.getenv('AI_MODEL'),
            'obsidian_host': os.getenv('OBSIDIAN_HOST'),
            'obsidian_port': os.getenv('OBSIDIAN_PORT'),
        }
        
        for key, value in env_overrides.items():
            if value:
                config_data[key] = value
                logger.info(f"Overriding config with environment variable for: {key}")
        
        return config_data
    
    def save(self) -> bool:
        """
        Save configuration to file in a thread-safe manner.
        
        Returns:
            bool: True if save was successful
            
        Raises:
            FileOperationError: If save operation fails
        """
        with QMutexLocker(self._file_mutex):
            try:
                # Convert dataclass to dict, excluding internal attributes
                data_to_save = asdict(self)
                data_to_save.pop('_file_mutex', None)

                with open("config.json", 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=4, sort_keys=True)
                
                logger.info("Configuration saved successfully.")
                return True
                
            except IOError as e:
                logger.error(f"Failed to save config: {e}")
                raise FileOperationError(f"Failed to save configuration: {e}")
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate all configuration settings.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        # Validate AI provider and corresponding API key
        if self.ai_provider == "gemini":
            if not self._is_valid_string(self.gemini_api_key):
                return False, "Gemini API key cannot be empty when using Gemini provider."
        elif self.ai_provider == "claude":
            if not self._is_valid_string(self.claude_api_key):
                return False, "Claude API key cannot be empty when using Claude provider."
        elif self.ai_provider == "openai":
            if not self._is_valid_string(self.openai_api_key):
                return False, "OpenAI API key cannot be empty when using OpenAI provider."
        elif self.ai_provider == "cohere":
            if not self._is_valid_string(self.cohere_api_key):
                return False, "Cohere API key cannot be empty when using Cohere provider."
        elif self.ai_provider == "mistral":
            if not self._is_valid_string(self.mistral_api_key):
                return False, "Mistral API key cannot be empty when using Mistral provider."
        elif self.ai_provider == "perplexity":
            if not self._is_valid_string(self.perplexity_api_key):
                return False, "Perplexity API key cannot be empty when using Perplexity provider."
        elif self.ai_provider == "together":
            if not self._is_valid_string(self.together_api_key):
                return False, "Together API key cannot be empty when using Together provider."
        elif self.ai_provider == "ollama":
            # Ollama doesn't require API key, just validate base URL
            if not self._is_valid_string(self.ollama_base_url):
                return False, "Ollama base URL cannot be empty when using Ollama provider."
        else:
            valid_providers = ['gemini', 'claude', 'openai', 'cohere', 'mistral', 'ollama', 'perplexity', 'together']
            return False, f"Invalid AI provider: {self.ai_provider}. Must be one of: {', '.join(valid_providers)}"
        
        if not self._is_valid_string(self.obsidian_api_key):
            return False, "Obsidian API key cannot be empty."
        
        # Validate model name
        if not self._is_valid_string(self.model_name):
            return False, "Model name cannot be empty."
        
        # Validate network settings
        if not self._is_valid_string(self.obsidian_host):
            return False, "Obsidian host cannot be empty."
        
        # Validate port
        try:
            port = int(self.obsidian_port)
            if not (1 <= port <= 65535):
                return False, "Obsidian port must be a number between 1 and 65535."
        except ValueError:
            return False, "Obsidian port must be a valid number."
        
        # Validate timeout values
        if self.request_timeout <= 0:
            return False, "Request timeout must be a positive number."
        
        # Validate file paths
        if not self._is_valid_string(self.chat_history_file):
            return False, "Chat history file path cannot be empty."
        
        if not self._is_valid_string(self.plugin_directory):
            return False, "Plugin directory cannot be empty."
        
        return True, "Configuration is valid."
    
    def _is_valid_string(self, value: str) -> bool:
        """Check if a string value is valid (not None or empty)."""
        return value is not None and value.strip() != ""
    
    def get_obsidian_url(self) -> str:
        """Get the complete Obsidian API base URL."""
        return f"http://{self.obsidian_host}:{self.obsidian_port}"
    
    def get_request_headers(self) -> dict:
        """Get the standard request headers for Obsidian API calls."""
        return {
            "Authorization": f"Bearer {self.obsidian_api_key}",
            "Content-Type": "application/json"
        }
    
    def is_development_mode(self) -> bool:
        """Check if running in development mode based on environment."""
        return os.getenv('GEODE_ENV', 'production').lower() == 'development'
    
    def get_log_level(self) -> str:
        """Get the effective log level."""
        if self.is_development_mode():
            return "DEBUG"
        return self.log_level
    
    def get_current_api_key(self) -> str:
        """Get the API key for the currently selected AI provider."""
        if self.ai_provider == "gemini":
            return self.gemini_api_key
        elif self.ai_provider == "claude":
            return self.claude_api_key
        elif self.ai_provider == "openai":
            return self.openai_api_key
        elif self.ai_provider == "cohere":
            return self.cohere_api_key
        elif self.ai_provider == "mistral":
            return self.mistral_api_key
        elif self.ai_provider == "perplexity":
            return self.perplexity_api_key
        elif self.ai_provider == "together":
            return self.together_api_key
        elif self.ai_provider == "ollama":
            return ""  # Ollama doesn't use API keys
        else:
            return ""
    
    def get_recommended_model(self, provider: str = None) -> str:
        """Get the recommended model for a provider."""
        provider = provider or self.ai_provider
        recommendations = {
            "gemini": "gemini-2.5-pro",  # Best balance of speed and quality
            "claude": "claude-3-5-sonnet-20241022",  # Best for writing and analysis
            "openai": "gpt-4o",  # Most popular OpenAI model
            "cohere": "command-r-plus",  # Best Cohere model for complex tasks
            "mistral": "mistral-large-latest",  # Most capable Mistral model
            "ollama": "llama3.1:8b",  # Good balance of speed and quality for local
            "perplexity": "llama-3.1-sonar-large-128k-online",  # Best for research
            "together": "meta-llama/Llama-3-70b-chat-hf"  # High quality open source
        }
        return recommendations.get(provider, "gemini-2.5-pro")
    
    def get_available_models(self) -> dict:
        """Get available models for each provider."""
        return {
            "gemini": [
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ],
            "claude": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "openai": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ],
            "cohere": [
                "command-r-plus",
                "command-r",
                "command",
                "command-nightly",
                "command-light"
            ],
            "mistral": [
                "mistral-large-latest",
                "mistral-medium-latest",
                "mistral-small-latest",
                "codestral-latest",
                "mistral-embed"
            ],
            "ollama": [
                "llama3.1:70b",
                "llama3.1:8b",
                "llama3.1:405b",
                "codestral:22b",
                "gemma2:27b",
                "phi3:medium",
                "mistral:7b",
                "qwen2:72b"
            ],
            "perplexity": [
                "llama-3.1-sonar-large-128k-online",
                "llama-3.1-sonar-small-128k-online",
                "llama-3.1-sonar-huge-128k-online",
                "llama-3.1-8b-instruct",
                "llama-3.1-70b-instruct"
            ],
            "together": [
                "meta-llama/Llama-3-70b-chat-hf",
                "meta-llama/Llama-3-8b-chat-hf",
                "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
                "teknium/OpenHermes-2.5-Mistral-7B"
            ]
        }
    
    def is_mcp_compatible_provider(self) -> bool:
        """Check if the current AI provider supports MCP."""
        # Note: MCP support varies by provider and model
        # This is a simplified check - in practice you'd want more granular control
        return self.ai_provider in ["claude", "openai", "cohere", "mistral", "together"]  # Some providers have better MCP support