from settings.setting_handler import SettingHandler
from typing import Dict, List
from core.config import Config
from core.types import AudioConfig

def update_config(config, key, value):
    config.set_setting(key, value)

def update_audio_config(config: Config, key: str, value: bool):
    config.audio = AudioConfig(autoplay=value)  # Correctly update the audio config

def update_provider_api_key(config, key, value):
    config.set_selected_provider_api_key(value)

def update_provider_base_url(config, key, value):
    config.set_selected_provider_base_url(value)

def update_provider_model(config, key, value):
    config.set_selected_provider_model(value)

def update_selected_provider(config, key, value):
    config.selected_provider = value

def update_grammar_check(config, key, value):
    config.set_setting(key, value)
    # Disable other features if grammar check is enabled
    if value:
        config.set_setting('translationEnabled', False)
        config.set_setting('ttsEnabled', False)
        config.set_setting('analysisEnabled', False)

def get_settings_handlers(config: Config) -> List[SettingHandler]:
    return [
        SettingHandler('translationEnabled', 'Translation:', config.get_setting("translationEnabled", True), 'checkbox', lambda c, k, v: update_config(c, k, v)),
        SettingHandler('ttsEnabled', 'TTS:', config.get_setting("ttsEnabled", True), 'checkbox', lambda c, k, v: update_config(c, k, v)),
        SettingHandler('analysisEnabled', 'Word/Phrase Analysis:', config.get_setting("analysisEnabled", True), 'checkbox', lambda c, k, v: update_config(c, k, v)),
        SettingHandler('autoplayEnabled', 'Autoplay:', config.audio.autoplay, 'checkbox', lambda c, k, v: update_audio_config(c, k, v)),
        # SettingHandler('grammarCheckEnabled', 'Grammar Check:', config.get_setting("grammarCheckEnabled", False), 'checkbox', lambda c, k, v: update_grammar_check(c, k, v)),
        SettingHandler('selectedProvider', 'AI Provider:', config.selected_provider, 'text' , lambda c, k, v: update_selected_provider(c, k, v)),
        SettingHandler('apiKey', 'API Key:', config.get_provider_config(config.selected_provider).api_key, 'text', lambda c, k, v: update_provider_api_key(c, k, v)),
        SettingHandler('baseUrl', 'Base URL:', config.get_provider_config(config.selected_provider).base_url, 'text', lambda c, k, v: update_provider_base_url(c, k, v)),
        SettingHandler('model', 'Model:', config.get_provider_config(config.selected_provider).model, 'text', lambda c, k, v: update_provider_model(c, k, v)),
    ]