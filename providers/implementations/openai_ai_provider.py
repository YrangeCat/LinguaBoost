import json
import openai
from core.errors import JSONParsingError
from core.helpers import remove_trailing_commas
import re
from openai import OpenAI
from providers import AIProvider

class OpenAIAIProvider(AIProvider):
    def __init__(self, config, provider_name):
        super().__init__(config, provider_name)
        provider_config = config.get_provider_config(provider_name)

        self.client = OpenAI(
            api_key=provider_config.api_key,
            base_url=provider_config.base_url
        )
        self.model_name = provider_config.model
        self.parameters = {}
        for key, value in provider_config.parameters.items():
            if key == "messages":
                self.parameters[key] = json.loads(value)
            elif value.startswith(("{", "[")) and value.endswith(("}", "]")):
                try:
                    self.parameters[key] = json.loads(value)
                except json.JSONDecodeError:
                    self.parameters[key] = value
            else:
                self.parameters[key] = value

    def generate_content(self, prompt: str) -> str:
        try:
            messages = [
                {
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"].replace("##PROMPT##", prompt)}]
                }
                for msg in self.parameters["messages"]
            ]
            stream = self.parameters.get("stream", False)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=stream,
                max_tokens=512,
            )
            return "".join(chunk.choices[0].delta.content for chunk in response if chunk.choices[0].delta.content is not None) if stream else response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating content with OpenAI: {e}")

    def parse_response(self, response: str) -> dict:
        try:
            return json.loads(remove_trailing_commas(response))
        except json.JSONDecodeError:
            try:
                match = re.search(r"\{.*\}", response, re.DOTALL)
                if not match:
                    raise ValueError("No JSON object found in response.")
                json_string = match.group(0)
                cleaned_response = remove_trailing_commas(json_string)
                return json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                raise JSONParsingError(f"Error decoding JSON: {e}", response)