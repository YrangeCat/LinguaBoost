from typing import NamedTuple, Dict, Any

class Features(NamedTuple):
    translation_enabled: bool
    tts_enabled: bool
    analysis_enabled: bool
    grammar_check_enabled: bool

class AnkiConfig(NamedTuple):
    deck_name: str
    model_name: str
    connect_url: str
    api_key: str
    fields: Dict[str, str]

class AudioConfig(NamedTuple):
    autoplay: bool

class HTMLTemplateConfig(NamedTuple):
    show_translation: bool
    show_timing_info: bool

class ProviderConfig(NamedTuple):
    api_key: str
    base_url: str
    model: str
    parameters: Dict[str, Any]  # type: ignore