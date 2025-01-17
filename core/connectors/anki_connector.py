import json
import requests
from core.config import Config
from core.cache import CacheManager
from core.errors import AnkiError
from typing import List, Dict

class AnkiConnector:
    def __init__(self, config: Config, cache_manager: CacheManager):
        self.config = config
        self.anki_config = config.anki
        self.base_url = self.anki_config.connect_url
        self.api_key = self.anki_config.api_key
        self.cache = cache_manager
        self.deck_name = self.anki_config.deck_name
        self.model_name = self.anki_config.model_name
        self.fields_mapping = self.anki_config.fields
        self.deck_and_model_checked = False

    def _request(self, action: str, **params) -> Dict:
        return {'action': action, 'params': params, 'version': 6}

    def invoke(self, action: str, **params) -> Dict:
        request_json = json.dumps(self._request(action, **params)).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            response = requests.post(self.base_url, data=request_json, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            response_data = response.json()

            if response_data.get('error'):
                raise AnkiError(f"AnkiConnect Error: {response_data['error']}")
            return response_data.get('result')
        except requests.exceptions.RequestException as e:
            raise AnkiError(f"Error connecting to AnkiConnect: {e}")

    def create_deck_if_not_exists(self, deck_name: str) -> bool:
        if self.cache.deck_exists(deck_name):
            print(f"Deck '{deck_name}' found in cache.")
            return False
        if deck_name not in self.invoke("deckNames"):
            self.invoke("createDeck", deck=deck_name)
            print(f"Deck '{deck_name}' created successfully.")
            self.cache.add_deck(deck_name)
            return True
        else:
            print(f"Deck '{deck_name}' already exists.")
            self.cache.add_deck(deck_name)
            return False

    def create_model_if_not_exists(self, model_name: str, fields: List[str], card_templates: List[Dict], css: str) -> bool:
        if self.cache.model_exists(model_name):
            print(f"Model '{model_name}' found in cache.")
            return False

        if model_name not in self.invoke("modelNames"):
            self.invoke("createModel", modelName=model_name, inOrderFields=fields, cardTemplates=card_templates, css=css)
            print(f"Model '{model_name}' created successfully.")
            self.cache.add_model(model_name)
            return True
        else:
            print(f"Model '{model_name}' already exists.")
            self.cache.add_model(model_name)
            return False

    def _generate_card_templates(self) -> List[Dict]:
        """Generates card templates for Anki model."""
        front_template = f"""
        <div style='font-family: "Arial"; color:red ;font-size: 15px;'>
        <span style='font-family: "Arial"; color:green ;font-size: 30px;'>{{{{{self.fields_mapping['_text']}}}}}</span>
        </a></div>
        <div id="modifiedContext">{{{{{self.fields_mapping['_context']}}}}}</div>
        <script>
            // 获取字段内容
            //var context = "{{{{{self.fields_mapping['_context']}}}}}";
            var text = "{{{{{self.fields_mapping['_text']}}}}}";
            var modifiedContextElement = document.getElementById("modifiedContext");

                // 创建正则表达式，忽略大小写，全局匹配
                var re = new RegExp(text, 'ig');
                // 将匹配到的内容替换成加粗的HTML标签
                var modifiedContext = modifiedContextElement.innerHTML.replaceAll(re, "<strong>$&</strong>");

                // 将修改后的内容设置为元素的 textContent
                modifiedContextElement.innerHTML = modifiedContext;


        </script>
        """
        back_template = f"""
        {{{{FrontSide}}}}
        <div style='font-family: "Arial"; font-size: 14px; color:gray;'>{{{{{self.fields_mapping['_context_translation']}}}}}</div>
        <hr id=answer>
        解释:{{{{{self.fields_mapping['_translation']}}}}}
        <br>
        <a href="goldendict://{{{{{self.fields_mapping['_text']}}}}}"><div style='font-family: "Arial"; font-size: 20px; color:gray;'>goldendict🔎 </a>
        <br>
        """
        return [{
            "Name": "Card 1",
            "Front": front_template,
            "Back": back_template,
        }]

    def add_note_to_anki(self, word: str, definition: str, context: str, context_translation: str) -> int:
        if not self.deck_and_model_checked:
            self.create_deck_if_not_exists(self.deck_name)
            model_fields = list(self.fields_mapping.values())
            card_templates = self._generate_card_templates()
            css = ".card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;}"
            self.create_model_if_not_exists(self.model_name, model_fields, card_templates, css)
            self.deck_and_model_checked = True

        fields = {}
        for key, anki_field_name in self.fields_mapping.items():
            if key == '_text':
                fields[anki_field_name] = word
            elif key == '_translation':
                fields[anki_field_name] = definition
            elif key == '_context':
                fields[anki_field_name] = context
            elif key == '_context_translation':
                fields[anki_field_name] = context_translation

        note = {
            "deckName": self.deck_name,
            "modelName": self.model_name,
            "fields": fields,
            "options": {
                "allowDuplicate": False
            },
            "tags": ["goldendict"]
        }

        return self.invoke("addNote", note=note)