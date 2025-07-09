# geode_bridge/mcp_client.py

import asyncio
import json
import logging
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    name: str
    command: List[str]
    args: List[str] = None
    env: Dict[str, str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}


class MCPClient:
    """
    Optional MCP (Model Context Protocol) client for extending Geode's capabilities.
    
    This allows users to optionally connect to MCP servers to add additional
    tools and capabilities beyond the core Obsidian integration.
    
    Note: This is an OPTIONAL feature - Geode works perfectly fine without any
    MCP servers. This is for users who want to extend functionality further.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the MCP client.
        
        Args:
            enabled: Whether MCP integration is enabled (default: True)
        """
        self.enabled = enabled
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connected_servers: Dict[str, Any] = {}
        self.available_tools: List[Callable] = []
        
        if not self.enabled:
            logger.info("MCP integration is disabled")
            return
        
        logger.info("MCP client initialized (optional extension)")
    
    def add_server_config(self, config: MCPServerConfig) -> bool:
        """
        Add an MCP server configuration.
        
        Args:
            config: MCP server configuration
            
        Returns:
            bool: True if added successfully
        """
        if not self.enabled:
            logger.warning("MCP is disabled, cannot add server config")
            return False
        
        self.servers[config.name] = config
        logger.info(f"Added MCP server config: {config.name}")
        return True
    
    def load_server_configs(self, config_path: str = "mcp_servers.json") -> bool:
        """
        Load MCP server configurations from file.
        
        Args:
            config_path: Path to MCP server config file
            
        Returns:
            bool: True if loaded successfully
        """
        if not self.enabled:
            return False
        
        config_file = Path(config_path)
        if not config_file.exists():
            logger.info("No MCP server config file found. MCP servers are optional.")
            return True
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            for server_data in data.get('servers', []):
                config = MCPServerConfig(**server_data)
                self.add_server_config(config)
            
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load MCP server configs: {e}")
            return False
    
    def save_server_configs(self, config_path: str = "mcp_servers.json") -> bool:
        """
        Save MCP server configurations to file.
        
        Args:
            config_path: Path to save MCP server config file
            
        Returns:
            bool: True if saved successfully
        """
        if not self.enabled:
            return False
        
        try:
            data = {
                'servers': [
                    {
                        'name': config.name,
                        'command': config.command,
                        'args': config.args,
                        'env': config.env,
                        'enabled': config.enabled
                    }
                    for config in self.servers.values()
                ]
            }
            
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Saved MCP server configurations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save MCP server configs: {e}")
            return False
    
    async def connect_to_servers(self) -> Dict[str, bool]:
        """
        Connect to all enabled MCP servers.
        
        Returns:
            Dict[str, bool]: Connection status for each server
        """
        if not self.enabled:
            return {}
        
        connection_results = {}
        
        for name, config in self.servers.items():
            if not config.enabled:
                logger.info(f"Skipping disabled MCP server: {name}")
                connection_results[name] = False
                continue
            
            try:
                # This is a placeholder for actual MCP connection logic
                # In a real implementation, you'd use the MCP SDK
                logger.info(f"Attempting to connect to MCP server: {name}")
                
                # Simulate connection (replace with actual MCP client code)
                # connected = await self._connect_mcp_server(config)
                connected = False  # Placeholder
                
                connection_results[name] = connected
                
                if connected:
                    logger.info(f"Successfully connected to MCP server: {name}")
                    # self.connected_servers[name] = connection
                else:
                    logger.warning(f"Failed to connect to MCP server: {name}")
                    
            except Exception as e:
                logger.error(f"Error connecting to MCP server {name}: {e}")
                connection_results[name] = False
        
        return connection_results
    
    def get_available_tools(self) -> List[Callable]:
        """
        Get all available tools from connected MCP servers.
        
        Returns:
            List[Callable]: List of available tool functions
        """
        if not self.enabled:
            return []
        
        # In a real implementation, this would query connected MCP servers
        # for their available tools and return them as callable functions
        return self.available_tools.copy()
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all configured MCP servers.
        
        Returns:
            Dict[str, Dict[str, Any]]: Server status information
        """
        if not self.enabled:
            return {"mcp_disabled": {"status": "disabled", "message": "MCP integration is disabled"}}
        
        status = {}
        
        for name, config in self.servers.items():
            status[name] = {
                "enabled": config.enabled,
                "connected": name in self.connected_servers,
                "command": config.command,
                "tool_count": 0  # Would be populated by actual MCP connection
            }
        
        return status
    
    def disconnect_all(self) -> bool:
        """
        Disconnect from all MCP servers.
        
        Returns:
            bool: True if all disconnected successfully
        """
        if not self.enabled:
            return True
        
        try:
            for name, connection in self.connected_servers.items():
                # In real implementation: await connection.disconnect()
                logger.info(f"Disconnected from MCP server: {name}")
            
            self.connected_servers.clear()
            self.available_tools.clear()
            
            logger.info("Disconnected from all MCP servers")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from MCP servers: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if MCP integration is enabled."""
        return self.enabled
    
    def get_server_count(self) -> int:
        """Get the number of configured MCP servers."""
        return len(self.servers) if self.enabled else 0
    
    def get_connected_count(self) -> int:
        """Get the number of connected MCP servers."""
        return len(self.connected_servers) if self.enabled else 0


# Example MCP server configurations for users to reference
EXAMPLE_MCP_CONFIGS = {
    "filesystem": MCPServerConfig(
        name="filesystem",
        command=["npx", "-y", "@modelcontextprotocol/server-filesystem"],
        args=["/path/to/directory"],
        enabled=False  # Disabled by default
    ),
    "sqlite": MCPServerConfig(
        name="sqlite",
        command=["npx", "-y", "@modelcontextprotocol/server-sqlite"],
        args=["--db-path", "/path/to/database.db"],
        enabled=False  # Disabled by default
    ),
    "github": MCPServerConfig(
        name="github",
        command=["npx", "-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"},
        enabled=False  # Disabled by default
    )
}


def create_example_config_file(config_path: str = "mcp_servers.json.example") -> bool:
    """
    Create an example MCP server configuration file for users to reference.
    
    Args:
        config_path: Path where to create the example file
        
    Returns:
        bool: True if created successfully
    """
    try:
        data = {
            "_comment": "Example MCP server configurations for Geode",
            "_note": "Copy this to mcp_servers.json and modify as needed",
            "_warning": "MCP servers are OPTIONAL - Geode works fine without them",
            "servers": [
                {
                    "name": config.name,
                    "command": config.command,
                    "args": config.args,
                    "env": config.env,
                    "enabled": config.enabled
                }
                for config in EXAMPLE_MCP_CONFIGS.values()
            ]
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Created example MCP config file: {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create example MCP config: {e}")
        return False