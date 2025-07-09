# geode_bridge/exceptions.py

class GeodeException(Exception):
    """Base exception class for all Geode-related errors."""
    pass

class ConfigurationError(GeodeException):
    """Raised when there's a configuration problem."""
    pass

class FileOperationError(GeodeException):
    """Raised when file operations (like saving config or history) fail."""
    pass

class ObsidianError(GeodeException):
    """Base class for Obsidian-related errors."""
    pass

class ObsidianConnectionError(ObsidianError):
    """Raised when connection to Obsidian fails."""
    pass

class ObsidianAuthError(ObsidianError):
    """Raised when Obsidian authentication fails."""
    pass

class ObsidianAPIError(ObsidianError):
    """
    Raised when Obsidian API returns an error.
    Contains the HTTP status code for more specific handling.
    """
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class GeminiError(GeodeException):
    """Base class for Gemini AI-related errors."""
    pass

class GeminiAuthError(GeminiError):
    """Raised when Gemini authentication fails."""
    pass

class GeminiAPIError(GeminiError):
    """Raised when Gemini API returns an error."""
    pass

class PluginError(GeodeException):
    """Raised when there's a plugin-related error."""
    pass