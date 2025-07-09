# geode_bridge/obsidian_api.py

import requests
import urllib.parse
import logging
from typing import Tuple

from .config import Config
from .exceptions import (
    ObsidianConnectionError, 
    ObsidianAuthError, 
    ObsidianAPIError, 
    ObsidianError
)

logger = logging.getLogger(__name__)


class ObsidianAPI:
    """
    A resilient API client for the Obsidian Local REST API plugin.
    
    This class provides a robust interface to interact with Obsidian's Local REST API,
    including proper error handling, timeouts, and connection management.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the Obsidian API client.
        
        Args:
            config: Configuration object containing connection details
        """
        self.config = config
        self.base_url = config.get_obsidian_url()
        self.headers = config.get_request_headers()
        
        # Create a persistent session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info(f"Obsidian API client initialized for {self.base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with comprehensive error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for the request
            
        Returns:
            requests.Response: The response object
            
        Raises:
            ObsidianConnectionError: For connection-related issues
            ObsidianAuthError: For authentication failures
            ObsidianAPIError: For API-specific errors
            ObsidianError: For other unexpected errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.config.request_timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout as e:
            error_msg = "Request timed out. Check your network or Obsidian's responsiveness."
            logger.error(f"Timeout error for {method} {url}: {e}")
            raise ObsidianConnectionError(error_msg) from e
            
        except requests.exceptions.ConnectionError as e:
            error_msg = "Connection failed. Is Obsidian running with the Local REST API plugin enabled?"
            logger.error(f"Connection error for {method} {url}: {e}")
            raise ObsidianConnectionError(error_msg) from e
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            
            if status_code == 401:
                error_msg = "Authentication failed (401). Check your Obsidian API key."
                logger.error(f"Auth error for {method} {url}: {e}")
                raise ObsidianAuthError(error_msg)
                
            elif status_code == 404:
                error_msg = f"Resource not found (404) at '{endpoint}'"
                logger.error(f"404 error for {method} {url}: {e}")
                raise ObsidianAPIError(error_msg, status_code=404)
                
            else:
                error_msg = f"HTTP Error {status_code}: {e.response.text}"
                logger.error(f"HTTP error for {method} {url}: {e}")
                raise ObsidianAPIError(error_msg, status_code=status_code)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"An unexpected request error occurred: {e}"
            logger.error(f"Request error for {method} {url}: {e}")
            raise ObsidianError(error_msg) from e

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the Obsidian API.
        
        Returns:
            Tuple[bool, str]: (success, message) indicating connection status
        """
        try:
            logger.info("Testing Obsidian API connection...")
            self._make_request('GET', "/")
            logger.info("Obsidian API connection successful")
            return True, "Obsidian connection successful."
            
        except ObsidianError as e:
            logger.warning(f"Obsidian connection test failed: {e}")
            return False, str(e)


class ObsidianTools:
    """
    A collection of tool functions that AI models can use to interact with Obsidian.
    
    These tools provide file and directory operations within the Obsidian vault,
    with proper error handling and user-friendly response messages.
    """
    
    def __init__(self, api: ObsidianAPI):
        """
        Initialize the tools with an API client.
        
        Args:
            api: ObsidianAPI instance for making requests
        """
        self.api = api
        logger.info("Obsidian tools initialized")
    
    def list_files(self, directory: str = ".") -> str:
        """
        List files and folders in a specified directory within the Obsidian vault.
        
        Args:
            directory: The directory path to list (relative to vault root)
            
        Returns:
            str: Success message with file list or error message
        """
        try:
            safe_directory = urllib.parse.quote(directory)
            response = self.api._make_request('GET', f"/vault/{safe_directory}")
            data = response.json()
            
            # Extract and format the directory contents
            folders = [f"{name}/" for name in data.get('subfolders', [])]
            files = data.get('files', [])
            all_items = sorted(folders + files)
            
            if not all_items:
                return f"SUCCESS: The directory '{directory}' is empty."
            
            return f"SUCCESS:\\n" + "\\n".join(all_items)
            
        except ObsidianError as e:
            logger.error(f"API Error listing files in '{directory}': {e}")
            return f"ERROR: Could not list files in '{directory}'. Reason: {e}"
            
        except Exception as e:
            logger.error(f"Unexpected error listing files in '{directory}': {e}")
            return f"ERROR: An unexpected error occurred. Check logs."

    def list_all_files(self) -> str:
        """
        List all files and folders recursively from the vault root.
        
        Returns:
            str: Success message with complete file list or error message
        """
        all_paths = []
        
        def fetch_directory(path: str) -> None:
            """Recursively fetch directory contents."""
            try:
                response_str = self.list_files(path)
                
                if response_str.startswith("ERROR"):
                    logger.warning(f"Could not fully scan vault. Error at '{path}': {response_str}")
                    return
                
                # Process the response from list_files
                lines = response_str.replace("SUCCESS:\\n", "").strip().split('\\n')
                for item in lines:
                    if not item:
                        continue
                    
                    # Reconstruct the full path
                    if path == ".":
                        full_path = item
                    else:
                        full_path = f"{path.rstrip('/')}/{item}"
                    
                    all_paths.append(full_path)
                    
                    # If it's a directory, recurse into it
                    if item.endswith('/'):
                        fetch_directory(full_path)
                        
            except Exception as e:
                logger.error(f"Failed during recursive file listing at '{path}': {e}", exc_info=True)

        # Start the recursive listing from the root
        fetch_directory(".")
        
        if not all_paths:
            return "ERROR: No files or folders found in the vault, or the vault root could not be read."
        
        # Remove duplicates and sort
        unique_paths = sorted(list(set(all_paths)))
        return "SUCCESS:\\n" + "\\n".join(unique_paths)

    def read_file(self, file_path: str) -> str:
        """
        Read the full contents of a specific file from the vault.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            str: File contents or error message
        """
        try:
            safe_path = urllib.parse.quote(file_path)
            response = self.api._make_request('GET', f"/vault/{safe_path}")
            return response.text
            
        except ObsidianAPIError as e:
            if e.status_code == 404:
                return f"ERROR: The file '{file_path}' was not found in the vault."
            
            logger.error(f"API Error reading file '{file_path}': {e}")
            return f"ERROR: Could not read file. Reason: {e}"
            
        except Exception as e:
            logger.error(f"Unexpected error reading file '{file_path}': {e}")
            return f"ERROR: An unexpected error occurred. Check logs."

    def create_or_update_file(self, file_path: str, content: str) -> str:
        """
        Create a new file or completely overwrite an existing file.
        
        Args:
            file_path: Path where the file should be created/updated
            content: Content to write to the file
            
        Returns:
            str: Success message or error message
        """
        try:
            safe_path = urllib.parse.quote(file_path)
            self.api._make_request(
                'PUT',
                f"/vault/{safe_path}",
                data=content.encode('utf-8'),
                headers={"Content-Type": "text/markdown"}
            )
            
            logger.info(f"File '{file_path}' saved successfully")
            return f"SUCCESS: The file '{file_path}' was saved successfully."
            
        except ObsidianError as e:
            logger.error(f"API Error writing file '{file_path}': {e}")
            return f"ERROR: Could not write to file. Reason: {e}"
            
        except Exception as e:
            logger.error(f"Unexpected error writing file '{file_path}': {e}")
            return f"ERROR: An unexpected error occurred. Check logs."

    def delete_file(self, file_path: str) -> str:
        """
        Delete a specific file from the vault.
        
        Warning: This action is permanent and cannot be undone.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            str: Success message or error message
        """
        try:
            safe_path = urllib.parse.quote(file_path)
            self.api._make_request('DELETE', f"/vault/{safe_path}")
            
            logger.info(f"File '{file_path}' deleted successfully")
            return f"SUCCESS: The file '{file_path}' was deleted."
            
        except ObsidianAPIError as e:
            if e.status_code == 404:
                return f"ERROR: Could not delete the file '{file_path}' because it was not found."
            
            logger.error(f"API Error deleting file '{file_path}': {e}")
            return f"API Error: Could not delete file. Reason: {e}"
            
        except Exception as e:
            logger.error(f"Unexpected error deleting file '{file_path}': {e}")
            return f"ERROR: An unexpected error occurred. Check logs."
    
    def get_vault_info(self) -> str:
        """
        Get information about the Obsidian vault.
        
        Returns:
            str: Vault information or error message
        """
        try:
            response = self.api._make_request('GET', "/")
            data = response.json()
            
            vault_info = {
                "name": data.get("name", "Unknown"),
                "path": data.get("path", "Unknown"),
                "version": data.get("version", "Unknown")
            }
            
            info_text = "\\n".join([f"{key}: {value}" for key, value in vault_info.items()])
            return f"SUCCESS: Vault Information:\\n{info_text}"
            
        except ObsidianError as e:
            logger.error(f"API Error getting vault info: {e}")
            return f"ERROR: Could not get vault information. Reason: {e}"
            
        except Exception as e:
            logger.error(f"Unexpected error getting vault info: {e}")
            return f"ERROR: An unexpected error occurred. Check logs."