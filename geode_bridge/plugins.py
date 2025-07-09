# geode_bridge/plugins.py

import importlib.util
import logging
from pathlib import Path
from typing import List, Dict, Protocol, Any, Callable

logger = logging.getLogger(__name__)


class PluginProtocol(Protocol):
    """
    Protocol defining the interface that all Geode plugins must implement.
    
    Any class that implements these methods can be loaded as a plugin,
    providing extensible functionality to the Geode application.
    """
    
    def get_name(self) -> str:
        """
        Return the unique name of the plugin.
        
        Returns:
            str: A unique identifier for this plugin
        """
        ...
    
    def get_description(self) -> str:
        """
        Return a brief description of what the plugin does.
        
        Returns:
            str: Human-readable description of plugin functionality
        """
        ...
    
    def get_tools(self) -> List[Callable]:
        """
        Return a list of callable tool functions this plugin provides to the AI.
        
        Returns:
            List[Callable]: List of functions that can be called by the AI
        """
        ...


class PluginManager:
    """
    Discovers, loads, and manages all plugins for the Geode application.
    
    The plugin manager handles the entire plugin lifecycle:
    - Discovery of plugin files
    - Dynamic loading and validation
    - Tool function registration
    - Error handling and logging
    """
    
    def __init__(self, plugin_dir: str):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dir: Directory path where plugin files are located
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PluginProtocol] = {}
        self.tools: List[Callable] = []
        
        logger.info(f"Plugin manager initialized for directory: {self.plugin_dir}")

    def load_plugins(self) -> List[str]:
        """
        Dynamically load all valid plugins from the plugin directory.
        
        This method:
        1. Creates the plugin directory if it doesn't exist
        2. Scans for Python files
        3. Dynamically imports each file
        4. Validates plugin classes
        5. Registers valid plugins
        
        Returns:
            List[str]: Names of successfully loaded plugins
        """
        loaded_plugins = []
        
        # Ensure plugin directory exists
        if not self._ensure_plugin_directory():
            return []
        
        # Scan for plugin files
        plugin_files = list(self.plugin_dir.glob("*.py"))
        logger.info(f"Found {len(plugin_files)} potential plugin files")
        
        for plugin_file in plugin_files:
            if self._should_skip_file(plugin_file):
                continue
            
            plugin_name = self._load_single_plugin(plugin_file)
            if plugin_name:
                loaded_plugins.append(plugin_name)
        
        logger.info(f"Successfully loaded {len(loaded_plugins)} plugins: {loaded_plugins}")
        return loaded_plugins

    def _ensure_plugin_directory(self) -> bool:
        """
        Ensure the plugin directory exists, creating it if necessary.
        
        Returns:
            bool: True if directory exists or was created successfully
        """
        if not self.plugin_dir.exists():
            try:
                self.plugin_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created plugin directory at: {self.plugin_dir}")
                return True
            except OSError as e:
                logger.error(f"Could not create plugin directory: {e}")
                return False
        return True

    def _should_skip_file(self, plugin_file: Path) -> bool:
        """
        Determine if a file should be skipped during plugin loading.
        
        Args:
            plugin_file: Path to the potential plugin file
            
        Returns:
            bool: True if the file should be skipped
        """
        return plugin_file.name.startswith("__")

    def _load_single_plugin(self, plugin_file: Path) -> str:
        """
        Load a single plugin file and register it if valid.
        
        Args:
            plugin_file: Path to the plugin file to load
            
        Returns:
            str: Name of the loaded plugin, or empty string if loading failed
        """
        try:
            logger.debug(f"Attempting to load plugin from {plugin_file}")
            
            # Dynamically import the module
            module = self._import_plugin_module(plugin_file)
            if not module:
                return ""
            
            # Find and validate plugin class
            plugin_instance = self._find_plugin_class(module, plugin_file)
            if not plugin_instance:
                return ""
            
            # Register the plugin
            return self._register_plugin(plugin_instance, plugin_file)
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_file}: {e}", exc_info=True)
            return ""

    def _import_plugin_module(self, plugin_file: Path) -> Any:
        """
        Import a plugin module from its file path.
        
        Args:
            plugin_file: Path to the plugin file
            
        Returns:
            module: The imported module, or None if import failed
        """
        try:
            spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
            if not (spec and spec.loader):
                logger.warning(f"Could not create module spec for {plugin_file}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
            
        except Exception as e:
            logger.error(f"Failed to import module from {plugin_file}: {e}")
            return None

    def _find_plugin_class(self, module: Any, plugin_file: Path) -> PluginProtocol:
        """
        Find and instantiate a valid plugin class from the module.
        
        Args:
            module: The imported plugin module
            plugin_file: Path to the plugin file (for logging)
            
        Returns:
            PluginProtocol: Instance of the plugin class, or None if not found
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a class with the required plugin methods
            if (isinstance(attr, type) and 
                hasattr(attr, 'get_name') and 
                hasattr(attr, 'get_description') and 
                hasattr(attr, 'get_tools')):
                
                try:
                    plugin_instance = attr()
                    logger.debug(f"Found plugin class '{attr_name}' in {plugin_file}")
                    return plugin_instance
                except Exception as e:
                    logger.error(f"Failed to instantiate plugin class '{attr_name}': {e}")
                    continue
        
        logger.warning(f"No valid plugin class found in {plugin_file}")
        return None

    def _register_plugin(self, plugin_instance: PluginProtocol, plugin_file: Path) -> str:
        """
        Register a validated plugin instance.
        
        Args:
            plugin_instance: The plugin instance to register
            plugin_file: Path to the plugin file (for logging)
            
        Returns:
            str: Name of the registered plugin, or empty string if registration failed
        """
        try:
            plugin_name = plugin_instance.get_name()
            
            # Check for duplicate names
            if plugin_name in self.plugins:
                logger.warning(f"Duplicate plugin name '{plugin_name}' found. Skipping {plugin_file}.")
                return ""
            
            # Register the plugin
            self.plugins[plugin_name] = plugin_instance
            
            # Register plugin tools
            plugin_tools = plugin_instance.get_tools()
            self.tools.extend(plugin_tools)
            
            logger.info(f"Successfully loaded plugin: '{plugin_name}' from {plugin_file.name}")
            logger.debug(f"Plugin '{plugin_name}' provides {len(plugin_tools)} tools")
            
            return plugin_name
            
        except Exception as e:
            logger.error(f"Failed to register plugin from {plugin_file}: {e}")
            return ""

    def get_all_tools(self) -> List[Callable]:
        """
        Get a consolidated list of all tool functions from all loaded plugins.
        
        Returns:
            List[Callable]: Copy of all available tool functions
        """
        return self.tools.copy()

    def get_plugin_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all loaded plugins.
        
        Returns:
            Dict[str, str]: Mapping of plugin names to their descriptions
        """
        descriptions = {}
        for name, plugin in self.plugins.items():
            try:
                descriptions[name] = plugin.get_description()
            except Exception as e:
                logger.error(f"Failed to get description for plugin '{name}': {e}")
                descriptions[name] = f"Error getting description: {e}"
        
        return descriptions

    def get_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive information about all loaded plugins.
        
        Returns:
            Dict[str, Dict[str, Any]]: Detailed information about each plugin
        """
        plugin_info = {}
        
        for name, plugin in self.plugins.items():
            try:
                tools = plugin.get_tools()
                tool_names = [getattr(tool, '__name__', str(tool)) for tool in tools]
                
                plugin_info[name] = {
                    'name': name,
                    'description': plugin.get_description(),
                    'tool_count': len(tools),
                    'tool_names': tool_names,
                    'status': 'loaded'
                }
            except Exception as e:
                logger.error(f"Failed to get info for plugin '{name}': {e}")
                plugin_info[name] = {
                    'name': name,
                    'description': f"Error: {e}",
                    'tool_count': 0,
                    'tool_names': [],
                    'status': 'error'
                }
        
        return plugin_info

    def reload_plugins(self) -> List[str]:
        """
        Reload all plugins by clearing current state and loading fresh.
        
        Returns:
            List[str]: Names of successfully reloaded plugins
        """
        logger.info("Reloading all plugins...")
        
        # Clear current state
        self.plugins.clear()
        self.tools.clear()
        
        # Load plugins fresh
        return self.load_plugins()

    def get_plugin_count(self) -> int:
        """
        Get the number of currently loaded plugins.
        
        Returns:
            int: Number of loaded plugins
        """
        return len(self.plugins)

    def has_plugin(self, plugin_name: str) -> bool:
        """
        Check if a specific plugin is loaded.
        
        Args:
            plugin_name: Name of the plugin to check
            
        Returns:
            bool: True if the plugin is loaded
        """
        return plugin_name in self.plugins