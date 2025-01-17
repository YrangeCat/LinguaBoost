# providers/provider_factory.py
from core.config import Config
from core.errors import UnsupportedAIProviderError
from providers.implementations.gemini_ai_provider import GeminiAIProvider
from providers.implementations.openai_ai_provider import OpenAIAIProvider
from providers import AIProvider

def get_ai_provider(config: Config) -> AIProvider:
    """Returns an AI provider instance based on the configuration."""
    provider_name = config.get_ai_provider_name()
    if provider_name == "gemini":
        return GeminiAIProvider(config, provider_name)
    elif provider_name == "openai":
        return OpenAIAIProvider(config, provider_name)
    else:
        raise UnsupportedAIProviderError(provider_name)