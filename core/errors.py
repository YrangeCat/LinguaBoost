class AIProviderError(Exception):
    """Base class for exceptions related to AI providers."""
    pass

class UnsupportedAIProviderError(AIProviderError):
    """Raised when an unsupported AI provider is specified."""
    def __init__(self, provider_name: str):
        super().__init__(f"Unsupported AI provider: {provider_name}")

class JSONParsingError(AIProviderError):
    """Raised when there is an error parsing the JSON response from the AI."""
    def __init__(self, message: str, response: str = None):
        super().__init__(message)
        self.response = response

class AnkiError(Exception):
    """Base class for exceptions related to Anki interactions."""
    pass

class ConfigurationError(Exception):
    """Base class for exceptions related to configuration."""
    pass

class CacheError(Exception):
    """Base class for exceptions related to caching."""
    pass

class TranslationError(Exception):
    """Base class for exceptions related to translation."""
    pass