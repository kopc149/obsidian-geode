# geode_bridge/ai_client.py

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from .config import Config
from .exceptions import GeminiAuthError, GeminiAPIError

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI provider clients."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.chat = None
    
    @abstractmethod
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the AI client and create a chat session."""
        pass
    
    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to the AI service."""
        pass
    
    @abstractmethod
    def send_message(self, prompt: str):
        """Send a message and return the response."""
        pass
    
    @abstractmethod
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a new chat session with tools."""
        pass


class GeminiClient(AIClient):
    """Gemini AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Gemini client."""
        try:
            from google import genai
            from google.genai import types
            
            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=self.config.get_current_api_key())
            self.create_chat_session(tool_functions)
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create Gemini client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create Gemini client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Gemini API."""
        try:
            logger.info("Testing connection to Gemini API...")
            test_response = self.client.models.generate_content(
                model=self.config.model_name,
                contents="Hello"
            )
            if test_response and test_response.text:
                logger.info("Gemini API connection successful.")
                return True, "Gemini connection successful."
            else:
                logger.warning("Gemini API test failed: No text in response.")
                return False, "Gemini: Failed to get a valid response."
        except Exception as e:
            logger.error(f"Gemini API test failed: {e}", exc_info=True)
            return False, f"Gemini Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a Gemini chat session with tools."""
        try:
            config_params = {}
            if tool_functions:
                config_params['config'] = self.types.GenerateContentConfig(tools=tool_functions)
            
            self.chat = self.client.chats.create(
                model=self.config.model_name,
                **config_params
            )
            logger.info(f"Initialized Gemini model: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to create Gemini chat session: {e}", exc_info=True)
            raise GeminiAPIError(f"Failed to create Gemini chat session '{self.config.model_name}': {e}")
    
    def send_message(self, prompt: str):
        """Send message to Gemini."""
        return self.chat.send_message(prompt)


class ClaudeClient(AIClient):
    """Claude AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Claude client."""
        try:
            import anthropic
            
            self.anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=self.config.get_current_api_key())
            self.tool_functions = tool_functions or []
            logger.info("Claude client initialized successfully")
        except ImportError:
            raise GeminiAuthError("Anthropic package not installed. Install with: pip install anthropic")
        except Exception as e:
            logger.error(f"Failed to create Claude client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create Claude client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Claude API."""
        try:
            logger.info("Testing connection to Claude API...")
            test_response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            if test_response and test_response.content:
                logger.info("Claude API connection successful.")
                return True, "Claude connection successful."
            else:
                return False, "Claude: Failed to get a valid response."
        except Exception as e:
            logger.error(f"Claude API test failed: {e}", exc_info=True)
            return False, f"Claude Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a Claude chat session (Claude uses stateless messages)."""
        self.tool_functions = tool_functions or []
        self.messages = []  # Track conversation history
        logger.info(f"Initialized Claude model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to Claude."""
        self.messages.append({"role": "user", "content": prompt})
        
        # Convert tools to Claude format if any
        tools = []
        if self.tool_functions:
            for tool in self.tool_functions:
                # This would need proper tool schema conversion
                # For now, this is a placeholder
                tools.append({
                    "name": tool.__name__,
                    "description": tool.__doc__ or f"Tool function {tool.__name__}",
                    "input_schema": {"type": "object", "properties": {}}
                })
        
        response = self.client.messages.create(
            model=self.config.model_name,
            max_tokens=4096,
            messages=self.messages,
            tools=tools if tools else None
        )
        
        # Add assistant response to history
        if response.content:
            self.messages.append({"role": "assistant", "content": response.content[0].text})
        
        return response


class OpenAIClient(AIClient):
    """OpenAI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the OpenAI client."""
        try:
            import openai
            
            self.openai = openai
            self.client = openai.OpenAI(api_key=self.config.get_current_api_key())
            self.tool_functions = tool_functions or []
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            raise GeminiAuthError("OpenAI package not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create OpenAI client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to OpenAI API."""
        try:
            logger.info("Testing connection to OpenAI API...")
            test_response = self.client.chat.completions.create(
                model=self.config.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            if test_response and test_response.choices:
                logger.info("OpenAI API connection successful.")
                return True, "OpenAI connection successful."
            else:
                return False, "OpenAI: Failed to get a valid response."
        except Exception as e:
            logger.error(f"OpenAI API test failed: {e}", exc_info=True)
            return False, f"OpenAI Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create an OpenAI chat session (OpenAI uses stateless messages)."""
        self.tool_functions = tool_functions or []
        self.messages = []  # Track conversation history
        logger.info(f"Initialized OpenAI model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to OpenAI."""
        self.messages.append({"role": "user", "content": prompt})
        
        # Convert tools to OpenAI format if any
        tools = []
        if self.tool_functions:
            for tool in self.tool_functions:
                # This would need proper tool schema conversion
                # For now, this is a placeholder
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or f"Tool function {tool.__name__}",
                        "parameters": {"type": "object", "properties": {}}
                    }
                })
        
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=self.messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None
        )
        
        # Add assistant response to history
        if response.choices and response.choices[0].message:
            self.messages.append(response.choices[0].message.model_dump())
        
        return response


class CohereClient(AIClient):
    """Cohere AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Cohere client."""
        try:
            import cohere
            
            self.cohere = cohere
            self.client = cohere.Client(api_key=self.config.get_current_api_key())
            self.tool_functions = tool_functions or []
            logger.info("Cohere client initialized successfully")
        except ImportError:
            raise GeminiAuthError("Cohere package not installed. Run: pip install cohere\nOr try a different AI provider like Gemini (no extra packages needed).")
        except Exception as e:
            logger.error(f"Failed to create Cohere client: {e}", exc_info=True)
            if "api_key" in str(e).lower():
                raise GeminiAuthError(f"Invalid Cohere API key. Get one at: https://dashboard.cohere.com/api-keys")
            raise GeminiAuthError(f"Failed to create Cohere client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Cohere API."""
        try:
            logger.info("Testing connection to Cohere API...")
            test_response = self.client.chat(
                model=self.config.model_name,
                message="Hello",
                max_tokens=10
            )
            if test_response and test_response.text:
                logger.info("Cohere API connection successful.")
                return True, "Cohere connection successful."
            else:
                return False, "Cohere: Failed to get a valid response."
        except Exception as e:
            logger.error(f"Cohere API test failed: {e}", exc_info=True)
            return False, f"Cohere Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a Cohere chat session (Cohere uses stateless messages)."""
        self.tool_functions = tool_functions or []
        self.chat_history = []  # Track conversation history
        logger.info(f"Initialized Cohere model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to Cohere."""
        # Convert tools to Cohere format if any
        tools = []
        if self.tool_functions:
            for tool in self.tool_functions:
                # Convert to Cohere tool format
                tools.append({
                    "name": tool.__name__,
                    "description": tool.__doc__ or f"Tool function {tool.__name__}",
                    "parameter_definitions": {}  # Would need proper schema conversion
                })
        
        response = self.client.chat(
            model=self.config.model_name,
            message=prompt,
            chat_history=self.chat_history,
            tools=tools if tools else None,
            max_tokens=4096
        )
        
        # Add to chat history
        self.chat_history.append({"role": "USER", "message": prompt})
        if response.text:
            self.chat_history.append({"role": "CHATBOT", "message": response.text})
        
        return response


class MistralClient(AIClient):
    """Mistral AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Mistral client."""
        try:
            from mistralai.client import MistralClient as MistralSDK
            
            self.mistral_sdk = MistralSDK
            self.client = MistralSDK(api_key=self.config.get_current_api_key())
            self.tool_functions = tool_functions or []
            self.messages = []
            logger.info("Mistral client initialized successfully")
        except ImportError:
            raise GeminiAuthError("Mistral package not installed. Install with: pip install mistralai")
        except Exception as e:
            logger.error(f"Failed to create Mistral client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create Mistral client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Mistral API."""
        try:
            logger.info("Testing connection to Mistral API...")
            from mistralai.models.chat_completion import ChatMessage
            
            test_response = self.client.chat(
                model=self.config.model_name,
                messages=[ChatMessage(role="user", content="Hello")],
                max_tokens=10
            )
            if test_response and test_response.choices:
                logger.info("Mistral API connection successful.")
                return True, "Mistral connection successful."
            else:
                return False, "Mistral: Failed to get a valid response."
        except Exception as e:
            logger.error(f"Mistral API test failed: {e}", exc_info=True)
            return False, f"Mistral Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a Mistral chat session."""
        self.tool_functions = tool_functions or []
        self.messages = []
        logger.info(f"Initialized Mistral model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to Mistral."""
        from mistralai.models.chat_completion import ChatMessage
        
        self.messages.append(ChatMessage(role="user", content=prompt))
        
        response = self.client.chat(
            model=self.config.model_name,
            messages=self.messages,
            max_tokens=4096
        )
        
        if response.choices and response.choices[0].message:
            self.messages.append(response.choices[0].message)
        
        return response


class OllamaClient(AIClient):
    """Ollama local AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Ollama client."""
        try:
            import requests
            
            self.requests = requests
            self.base_url = self.config.ollama_base_url
            self.tool_functions = tool_functions or []
            self.messages = []
            logger.info("Ollama client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create Ollama client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create Ollama client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Ollama API."""
        try:
            logger.info("Testing connection to Ollama API...")
            response = self.requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                logger.info("Ollama API connection successful.")
                return True, "Ollama connection successful."
            else:
                return False, f"Ollama: Failed to connect (status: {response.status_code})"
        except Exception as e:
            logger.error(f"Ollama API test failed: {e}", exc_info=True)
            return False, f"Ollama Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create an Ollama chat session."""
        self.tool_functions = tool_functions or []
        self.messages = []
        logger.info(f"Initialized Ollama model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to Ollama."""
        self.messages.append({"role": "user", "content": prompt})
        
        response = self.requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.config.model_name,
                "messages": self.messages,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if "message" in result:
                self.messages.append(result["message"])
            return result
        else:
            raise Exception(f"Ollama API error: {response.status_code}")


class PerplexityClient(AIClient):
    """Perplexity AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Perplexity client."""
        try:
            import openai  # Perplexity uses OpenAI-compatible API
            
            self.openai = openai
            self.client = openai.OpenAI(
                api_key=self.config.get_current_api_key(),
                base_url="https://api.perplexity.ai"
            )
            self.tool_functions = tool_functions or []
            self.messages = []
            logger.info("Perplexity client initialized successfully")
        except ImportError:
            raise GeminiAuthError("OpenAI package required for Perplexity. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to create Perplexity client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create Perplexity client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Perplexity API."""
        try:
            logger.info("Testing connection to Perplexity API...")
            test_response = self.client.chat.completions.create(
                model=self.config.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            if test_response and test_response.choices:
                logger.info("Perplexity API connection successful.")
                return True, "Perplexity connection successful."
            else:
                return False, "Perplexity: Failed to get a valid response."
        except Exception as e:
            logger.error(f"Perplexity API test failed: {e}", exc_info=True)
            return False, f"Perplexity Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a Perplexity chat session."""
        self.tool_functions = tool_functions or []
        self.messages = []
        logger.info(f"Initialized Perplexity model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to Perplexity."""
        self.messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=self.messages
        )
        
        if response.choices and response.choices[0].message:
            self.messages.append(response.choices[0].message.model_dump())
        
        return response


class TogetherClient(AIClient):
    """Together AI client implementation."""
    
    def initialize(self, tool_functions: List[Callable] = None):
        """Initialize the Together client."""
        try:
            import together
            
            self.together = together
            together.api_key = self.config.get_current_api_key()
            self.tool_functions = tool_functions or []
            self.messages = []
            logger.info("Together client initialized successfully")
        except ImportError:
            raise GeminiAuthError("Together package not installed. Install with: pip install together")
        except Exception as e:
            logger.error(f"Failed to create Together client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to create Together client: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Together API."""
        try:
            logger.info("Testing connection to Together API...")
            test_response = self.together.Complete.create(
                prompt="Hello",
                model=self.config.model_name,
                max_tokens=10
            )
            if test_response and 'output' in test_response:
                logger.info("Together API connection successful.")
                return True, "Together connection successful."
            else:
                return False, "Together: Failed to get a valid response."
        except Exception as e:
            logger.error(f"Together API test failed: {e}", exc_info=True)
            return False, f"Together Error: {e}"
    
    def create_chat_session(self, tool_functions: List[Callable] = None):
        """Create a Together chat session."""
        self.tool_functions = tool_functions or []
        self.messages = []
        logger.info(f"Initialized Together model: {self.config.model_name}")
    
    def send_message(self, prompt: str):
        """Send message to Together."""
        self.messages.append({"role": "user", "content": prompt})
        
        # Convert messages to prompt format for Together
        prompt_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages])
        
        response = self.together.Complete.create(
            prompt=prompt_text,
            model=self.config.model_name,
            max_tokens=4096
        )
        
        if response and 'output' in response:
            self.messages.append({"role": "assistant", "content": response['output']['text']})
        
        return response


def create_ai_client(config: Config) -> AIClient:
    """Factory function to create the appropriate AI client based on configuration."""
    if config.ai_provider == "gemini":
        return GeminiClient(config)
    elif config.ai_provider == "claude":
        return ClaudeClient(config)
    elif config.ai_provider == "openai":
        return OpenAIClient(config)
    elif config.ai_provider == "cohere":
        return CohereClient(config)
    elif config.ai_provider == "mistral":
        return MistralClient(config)
    elif config.ai_provider == "ollama":
        return OllamaClient(config)
    elif config.ai_provider == "perplexity":
        return PerplexityClient(config)
    elif config.ai_provider == "together":
        return TogetherClient(config)
    else:
        raise ValueError(f"Unsupported AI provider: {config.ai_provider}")