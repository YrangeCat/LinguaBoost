import json
import os
import sys
from typing import Dict, Any
from core.errors import CacheError

class CacheManager:
    def __init__(self, cache_file_path: str = None):
        if cache_file_path is None:
            cache_file_path = self._get_default_cache_path()
        self.cache_file_path = cache_file_path
        self._decks = None
        self._models = None
        self._config = None

    def _get_default_cache_path(self) -> str:
        if getattr(sys, 'frozen', False):
            application_path = os.path.join(os.path.dirname(sys.executable), "_internal")
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, "..", "anki_cache.json")

    @property
    def decks(self) -> Dict[str, bool]:
        if self._decks is None:
            self.load()
        return self._decks

    @property
    def models(self) -> Dict[str, bool]:
        if self._models is None:
            self.load()
        return self._models

    @property
    def config(self) -> Dict[str, Any]:
        if self._config is None:
            self.load()
        return self._config

    def load(self):
        try:
            with open(self.cache_file_path, "r") as f:
                cache_data = json.load(f)
                self._decks = cache_data.get("decks", {})
                self._models = cache_data.get("models", {})
                self._config = cache_data.get("config", {})
            print("Cache loaded from file.")
        except FileNotFoundError:
            print("Cache file not found. Starting with an empty cache.")
            self._decks = {}
            self._models = {}
            self._config = {}
        except json.JSONDecodeError as e:
            raise CacheError(f"Error decoding JSON from cache file: {e}")


    def save(self):
        cache_data = {
            "decks": self.decks,
            "models": self.models,
            "config": self.config
        }
        try:
            with open(self.cache_file_path, "w") as f:
                json.dump(cache_data, f)
            print("Cache saved to file.")
        except Exception as e:
            raise CacheError(f"Error saving cache to file: {e}")

    def deck_exists(self, deck_name: str) -> bool:
        return self.decks.get(deck_name, False)

    def add_deck(self, deck_name: str):
        self.decks[deck_name] = True
        self.save()

    def model_exists(self, model_name: str) -> bool:
        return self.models.get(model_name, False)

    def add_model(self, model_name: str):
        self.models[model_name] = True
        self.save()

    def update_config(self, config_data: Dict[str, Any]):
        self._config = config_data
        self.save()