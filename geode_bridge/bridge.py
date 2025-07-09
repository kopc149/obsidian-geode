# geode_bridge/bridge.py

import logging

from .config import Config
from .obsidian_api import ObsidianAPI, ObsidianTools
from .plugins import PluginManager
from .mcp_client import MCPClient
from .ai_client import create_ai_client
from .exceptions import GeminiAuthError, GeminiAPIError, GeodeException
from .exceptions import ObsidianAuthError, ObsidianConnectionError

logger = logging.getLogger(__name__)


class GeodeBridge:
    """
    The main backend engine for the Geode application.
    
    This class orchestrates all interactions between:
    - Configuration management
    - Obsidian API integration
    - Plugin system
    - Gemini AI model
    
    The bridge maintains a persistent chat session with the AI model
    and handles all tool calling and response processing.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the GeodeBridge with configuration and set up all components.
        
        Args:
            config: Configuration object containing API keys and settings
            
        Raises:
            GeminiAuthError: If Gemini API authentication fails
            GeminiAPIError: If Gemini API initialization fails
        """
        self.config = config
        self.obsidian_api = ObsidianAPI(config)
        self.tools = ObsidianTools(self.obsidian_api)
        
        # Initialize plugin system
        self._setup_plugins()
        
        # Initialize optional MCP integration
        self._setup_mcp_client()
        
        # Consolidate all available tools (built-in + plugins + MCP)
        self._setup_tool_functions()
        
        # Initialize AI client with tools
        self._setup_ai_client()
        
        # Create tool lookup map for efficient access
        self.tool_function_map = {func.__name__: func for func in self.tool_functions}

    def _setup_plugins(self):
        """Initialize and load the plugin system."""
        if not getattr(self.config, 'plugin_directory', None):
            logger.warning("No plugin directory specified in config. Plugins will not be loaded.")
            self.plugin_manager = PluginManager("")
        else:
            self.plugin_manager = PluginManager(self.config.plugin_directory)
            
        try:
            loaded_plugins = self.plugin_manager.load_plugins()
            logger.info(f"Loaded {len(loaded_plugins)} plugins: {loaded_plugins}")
        except Exception as e:
            logger.warning(f"Plugin loading failed: {e}", exc_info=True)

    def _setup_mcp_client(self):
        """Initialize optional MCP client for extended capabilities."""
        try:
            self.mcp_client = MCPClient(enabled=self.config.enable_mcp)
            
            if self.mcp_client.is_enabled():
                # Load MCP server configurations if they exist
                self.mcp_client.load_server_configs(self.config.mcp_config_file)
                
                # Create example config for users who want to add MCP servers
                from .mcp_client import create_example_config_file
                create_example_config_file()
                
                server_count = self.mcp_client.get_server_count()
                logger.info(f"MCP client initialized with {server_count} configured servers (optional)")
            else:
                logger.info("MCP integration disabled")
                
        except Exception as e:
            logger.warning(f"MCP client initialization failed: {e}", exc_info=True)
            # Fallback to disabled MCP client
            self.mcp_client = MCPClient(enabled=False)

    def _setup_tool_functions(self):
        """Set up all available tool functions (built-in + plugins + MCP)."""
        # Start with core Obsidian tools (always available)
        self.tool_functions = [
            self.tools.list_files,
            self.tools.list_all_files,
            self.tools.read_file,
            self.tools.create_or_update_file,
            self.tools.delete_file
        ]
        
        # Add plugin tools
        plugin_tools = self.plugin_manager.get_all_tools()
        self.tool_functions.extend(plugin_tools)
        
        # Add optional MCP tools
        mcp_tools = self.mcp_client.get_available_tools()
        self.tool_functions.extend(mcp_tools)
        
        tool_breakdown = {
            "obsidian": 5,
            "plugins": len(plugin_tools),
            "mcp": len(mcp_tools),
            "total": len(self.tool_functions)
        }
        
        logger.info(f"Configured tools - Obsidian: {tool_breakdown['obsidian']}, "
                   f"Plugins: {tool_breakdown['plugins']}, "
                   f"MCP: {tool_breakdown['mcp']}, "
                   f"Total: {tool_breakdown['total']}")

    def _setup_ai_client(self):
        """Initialize the AI client based on configuration."""
        try:
            self.ai_client = create_ai_client(self.config)
            self.ai_client.initialize(self.tool_functions)
            logger.info(f"Initialized {self.config.ai_provider} client with model: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}", exc_info=True)
            raise GeminiAuthError(f"Failed to initialize {self.config.ai_provider} client: {e}")

    def test_connection(self) -> tuple[bool, str]:
        """
        Test connections to both Obsidian and AI provider.
        
        Returns:
            tuple[bool, str]: (success, message) indicating connection status
        """
        # Test Obsidian connection
        obsidian_ok, obsidian_msg = self.obsidian_api.test_connection()
        if not obsidian_ok:
            return False, f"Obsidian Connection Failed: {obsidian_msg}"
        
        # Test AI provider connection
        ai_ok, ai_msg = self.ai_client.test_connection()
        if not ai_ok:
            return False, f"AI Provider Connection Failed: {ai_msg}"
        
        return True, f"All connections successful (Obsidian + {self.config.ai_provider.title()})."

    def send_message(self, prompt: str, signals):
        """
        Process a user prompt, handle tool calls, and emit signals for the UI.
        
        This method:
        1. Sends the user prompt to the AI model
        2. Processes any tool calls in the response
        3. Continues the conversation until no more tools are needed
        4. Emits appropriate signals for the UI to update
        
        Args:
            prompt: The user's message/question
            signals: Qt signals object for UI communication
        """
        try:
            # Send the initial message to the AI
            response = self.ai_client.send_message(prompt)
            
            # Process tool calls in a loop until conversation is complete
            self._process_tool_calls(response, signals)
            
            # Extract and emit the final text response
            final_text = self._extract_final_text(response)
            signals.message.emit("Geode", final_text or "(No text response)")

        except Exception as e:
            logger.error(f"Error in send_message: {e}", exc_info=True)
            error_msg = self._format_error_message(e)
            signals.error.emit(error_msg)
        finally:
            try:
                signals.finished.emit()
            except Exception as finish_exc:
                logger.error(f"Error emitting finished signal: {finish_exc}")

    def _process_tool_calls(self, response, signals):
        """
        Process all tool calls in the AI response.
        
        Args:
            response: The AI response that may contain tool calls
            signals: Qt signals object for UI communication
        """
        max_iterations = 10  # Safety limit to prevent infinite loops
        
        for iteration in range(max_iterations):
            # Check if response has function calls
            function_calls = self._extract_function_calls(response)
            if not function_calls:
                break
            
            # Process all function calls and collect responses
            function_responses = []
            for function_call in function_calls:
                try:
                    function_response = self._execute_function_call(function_call, signals)
                    function_responses.append(function_response)
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}", exc_info=True)
                    signals.error.emit(f"Tool execution failed: {e}")
                    return  # Exit on tool error
            
            # Send all function responses back to the AI
            if function_responses:
                try:
                    response = self.ai_client.send_message(function_responses)
                except Exception as e:
                    logger.error(f"Error sending function responses: {e}", exc_info=True)
                    signals.error.emit(f"Error sending function responses: {e}")
                    return
            
            # Check if we've reached the iteration limit
            if iteration == max_iterations - 1:
                logger.warning("Max tool-use iterations reached")
                signals.error.emit("Tool-use loop exceeded maximum iterations")
                break

    def _extract_function_calls(self, response):
        """
        Extract function calls from AI response.
        
        Args:
            response: The AI response object
            
        Returns:
            list: List of function call objects
        """
        function_calls = []
        
        if not (hasattr(response, 'candidates') and response.candidates):
            return function_calls
            
        candidate = response.candidates[0]
        if not (hasattr(candidate, 'content') and candidate.content):
            return function_calls
            
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)
                
        return function_calls

    def _execute_function_call(self, function_call, signals):
        """
        Execute a single function call and return the response.
        
        Args:
            function_call: The function call object from the AI
            signals: Qt signals object for UI communication
            
        Returns:
            types.FunctionResponse: The response to send back to the AI
            
        Raises:
            Exception: If the function call fails or function is unknown
        """
        function_name = function_call.name
        args = dict(function_call.args) if function_call.args else {}
        
        # Emit tool call signal for UI
        args_str = ", ".join([f"{k}='{v}'" for k, v in args.items()])
        signals.tool_call.emit(f"{function_name}({args_str})")
        
        # Look up and execute the function
        function_to_call = self.tool_function_map.get(function_name)
        if not function_to_call:
            raise Exception(f"Unknown tool function requested: {function_name}")
        
        # Execute the function with provided arguments
        tool_response = function_to_call(**args)
        
        # Ensure response is serializable
        if not isinstance(tool_response, (str, dict, int, float, list, bool, type(None))):
            tool_response = str(tool_response)
        
        # Create and return function response
        return types.FunctionResponse(
            name=function_name,
            response=tool_response
        )

    def _extract_final_text(self, response):
        """
        Extract the final text response from the AI.
        
        Args:
            response: The AI response object
            
        Returns:
            str: The extracted text content
        """
        final_text = ""
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_text += part.text
        
        return final_text

    def _format_error_message(self, error):
        """
        Format error messages for user display.
        
        Args:
            error: The exception that occurred
            
        Returns:
            str: User-friendly error message
        """
        if isinstance(error, (GeminiAuthError, ObsidianAuthError)):
            return "Authentication Error: Please check your API keys in settings."
        elif isinstance(error, ObsidianConnectionError):
            return "Obsidian Connection Error: Is Obsidian running with the Local REST API plugin?"
        else:
            return f"An unexpected error occurred: {error}"