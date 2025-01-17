# providers/__init__.py
from abc import ABC, abstractmethod
from typing import Dict
from core.config import Config
from core.errors import UnsupportedAIProviderError

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