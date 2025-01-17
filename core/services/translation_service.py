import time
import asyncio
from providers.provider_factory import get_ai_provider
from core.config import Config
from prompts.custom_prompt import generate_grammar_check_prompt, generate_translation_prompt, generate_analysis_prompt
from typing import Dict, Tuple


class TranslationService:
    def __init__(self, config: Config):
        self.config = config
        try:
            self.ai_provider = get_ai_provider(config)
        except Exception as e:
            print(f"Error: {e}")
            print(f"Please check the 'selected_provider' setting in your config.ini file.")
            raise  # Re-raise the exception to halt execution

    async def get_grammar_check_data(self, text: str) -> Tuple[Dict, float]:
        return await self._get_ai_data(text, generate_grammar_check_prompt)

    async def get_translation_data(self, text: str) -> Tuple[Dict, float]:
        return await self._get_ai_data(text, generate_translation_prompt)

    async def get_analysis_data(self, text: str) -> Tuple[Dict, float]:
        return await self._get_ai_data(text, generate_analysis_prompt)

    async def _get_ai_data(self, text: str, prompt_generator: callable) -> Tuple[Dict, float]:
        start_time = time.perf_counter()
        try:
            prompt = prompt_generator(text)
            raw_response = await asyncio.to_thread(self.ai_provider.generate_content, prompt)
            translation_data = self.ai_provider.parse_response(raw_response)
        except Exception as e:
            print(f"Error getting data: {e}")
            return {}, 0
        return translation_data, time.perf_counter() - start_time