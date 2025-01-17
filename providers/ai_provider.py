from core.config import Config
from core.errors import UnsupportedAIProviderError
from typing import Dict
from abc import ABC, abstractmethod
import re
from providers.implementations.gemini_ai_provider import GeminiAIProvider
from providers.implementations.openai_ai_provider import OpenAIAIProvider

class AIProvider(ABC):
    def __init__(self, config: Config, provider_name: str):
        self.config = config
        self.provider_name = provider_name

    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """Generates content based on the given prompt."""
        pass

    @abstractmethod
    def parse_response(self, response: str) -> dict:
        """Parses the raw response from the AI."""
        pass

def get_ai_provider(config: Config) -> AIProvider:
    """Returns an AI provider instance based on the configuration."""
    provider_name = config.get_ai_provider_name()
    if provider_name == "gemini":
        return GeminiAIProvider(config, provider_name)
    elif provider_name == "openai":
        return OpenAIAIProvider(config, provider_name)
    else:
        raise UnsupportedAIProviderError(provider_name)