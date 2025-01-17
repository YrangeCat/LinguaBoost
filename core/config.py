import configparser
import os
import sys
from typing import Tuple, Dict, Any
from core.cache import CacheManager
from core.errors import ConfigurationError
from core.types import AnkiConfig, AudioConfig, HTMLTemplateConfig, ProviderConfig


class Config:
    def __init__(self, config_path: str, cache_manager: CacheManager):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.cache_manager = cache_manager
        self.load_from_cache_or_file()

    def load_from_cache_or_file(self):
        cached_config = self.cache_manager.config
        if cached_config:
            self.config.read_dict(cached_config)
        else:
            self.load_config_from_file()
            self.cache_manager.update_config(self.config._sections)

    def load_config_from_file(self):
        if not os.path.exists(self.config_path):
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config.read_file(f)
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")

    def refresh(self):
        """Reloads the configuration from the file."""
        self.load_config_from_file()
        self.cache_manager.update_config(self.config._sections)

    def _get_config_value(self, section: str, key: str, fallback: Any = None) -> Any:
        try:
            value = self.config.get(section, key, fallback=fallback)
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
            else:
                return value
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ConfigurationError(f"Missing configuration: {e}")

    def _set_config_value(self, section: str, key: str, value: Any):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    @property
    def anki(self) -> AnkiConfig:
        fields = {}
        try:
            fields = dict(self.config.items("anki.fields"))
        except configparser.NoSectionError as e:
            raise ConfigurationError(f"Missing configuration section: {e}")
        return AnkiConfig(
            deck_name=self._get_config_value("anki", "deckName"),
            model_name=self._get_config_value("anki", "modelName"),
            connect_url=self._get_config_value("anki", "ankiConnectUrl", fallback="http://localhost:8765"),
            api_key=self._get_config_value("anki", "api_key", fallback=None),
            fields=fields,
        )

    @property
    def audio(self) -> AudioConfig:
        return AudioConfig(
            autoplay=self.config.getboolean("audio", "autoplay", fallback=False)
        )

    @audio.setter
    def audio(self, value: AudioConfig):
        self._set_config_value("audio", "autoplay", value.autoplay)

    @property
    def voice_default(self) -> str:
        return self._get_config_value("voice", "default_voice", fallback="en-US-ChristopherNeural")

    @property
    def html_template(self) -> HTMLTemplateConfig:
        return HTMLTemplateConfig(
            show_translation=self.config.getboolean("html_template", "show_translation", fallback=True),
            show_timing_info=self.config.getboolean("html_template", "show_timing_info", fallback=True)
        )

    @property
    def selected_provider(self) -> str:
        return self._get_config_value("providers", "selected_provider")

    @selected_provider.setter
    def selected_provider(self, value: str):
        self._set_config_value("providers", "selected_provider", value)

    def get_ai_provider_name(self) -> str:
        return self.selected_provider

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        try:
            items = dict(self.config.items(f"providers.{provider_name}"))
            params_items = {}
            config_section = f"providers.{provider_name}.parameters"
            if self.config.has_section(config_section):
                params_items = dict(self.config.items(config_section))
            # else:
            #     print(f"No parameters found for provider: {provider_name}")

            # Provide default values if keys are missing
            api_key = items.get("api_key", "")
            base_url = items.get("base_url", "")
            model = items.get("model", "")

            return ProviderConfig(
                api_key=api_key,
                base_url=base_url,
                model=model,
                parameters=params_items
            )
        except configparser.NoSectionError as e:
            raise ConfigurationError(f"Missing configuration section: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._get_config_value("settings", key, fallback=default)

    def set_setting(self, key: str, value: Any):
        self._set_config_value("settings", key, value)

    def save_settings(self, config_path: str):
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                self.config.write(f)
        except Exception as e:
            raise ConfigurationError(f"Error writing to configuration file: {e}")

    def set_selected_provider_api_key(self, api_key: str):
        self._set_config_value(f"providers.{self.selected_provider}", "api_key", api_key)

    def set_selected_provider_base_url(self, base_url: str):
        self._set_config_value(f"providers.{self.selected_provider}", "base_url", base_url)

    def set_selected_provider_model(self, model: str):
        self._set_config_value(f"providers.{self.selected_provider}", "model", model)

def _get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        application_path = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(application_path, "..", "config.ini")
    return config_path

def load_config(cache_manager: CacheManager) -> Tuple[Config, str]:
    config_path = _get_config_path()
    return Config(config_path, cache_manager), config_path