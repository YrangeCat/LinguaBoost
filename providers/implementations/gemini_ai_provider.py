import google.generativeai as genai
from core.errors import JSONParsingError
from core.helpers import remove_trailing_commas
from google.generativeai.types import GenerationConfig
import re
import json
from providers import AIProvider

class GeminiAIProvider(AIProvider):
    def __init__(self, config, provider_name):
        super().__init__(config, provider_name)
        provider_config = config.get_provider_config(provider_name)
        genai.configure(api_key=provider_config.api_key)
        self.model = genai.GenerativeModel(provider_config.model)
        self.generation_config = GenerationConfig(
            temperature=float(provider_config.parameters.get("temperature", 0.1)),
        )

    def generate_content(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            raise Exception(f"Error generating content with Gemini: {e}")

    def parse_response(self, response: str) -> dict:
        try:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in response.")
            json_string = match.group(0)
            cleaned_response = remove_trailing_commas(json_string)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise JSONParsingError(f"Error decoding JSON: {e}", response)