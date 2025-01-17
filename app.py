import asyncio
from flask import Flask, request, jsonify, after_this_request
from flask_cors import CORS
from core.config import load_config, Config
from core.cache import CacheManager
from core.services.translation_service import TranslationService
from core.services.audio_service import AudioService
from core.connectors.anki_connector import AnkiConnector
from core.helpers import safe_json_loads
from core.errors import AnkiError, ConfigurationError, TranslationError
from core.types import Features
from core.html_generator import generate_goldendict_html, WordData, generate_grammar_check_html
from settings.settings import get_settings_handlers
from prompts.custom_prompt import detect_language
import re
from typing import Dict, List, Optional, Tuple

app = Flask(__name__)
CORS(app, resources={
    r"/add_note_to_anki": {"origins": "ifr://localhost"},
    r"/": {"origins": "ifr://localhost"},
    r"/update_settings": {"origins": "ifr://localhost"},
    r"/get_settings": {"origins": "ifr://localhost"},
    r"/refresh": {"origins": "ifr://localhost"},
    r"/grammar_check": {"origins": "ifr://localhost"}
})

# --- Constants ---
MAX_TRANSLATION_CACHE_SIZE = 10000
GRAMMAR_CHECK_PREFIX="~"
# --- Helper Functions ---

async def fetch_ai_data(text: str, features: Features, translation_service: TranslationService, audio_service: Optional[AudioService]) -> Tuple:
    """Fetches data from AI providers based on enabled features."""
    tasks = []
    if features.translation_enabled:
        tasks.append(translation_service.get_translation_data(text))
    if features.analysis_enabled:
        tasks.append(translation_service.get_analysis_data(text))
    if features.tts_enabled and audio_service:
        tasks.append(audio_service.generate_audio(text))
    if features.grammar_check_enabled:
        tasks.append(translation_service.get_grammar_check_data(text))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    translation_data, translation_time = {}, 0
    analysis_data, analysis_time = {}, 0
    audio_file_path, audio_time = "", 0
    grammar_check_data, grammar_check_time = {}, 0

    for result in results:
        if isinstance(result, Exception):
            print(f"Error during AI data fetching: {result}")
            # Handle the error appropriately, e.g., log it, retry, or set default values
            continue  # Skip to the next result

        if isinstance(result, tuple) and len(result) == 2:
            if isinstance(result[0], dict):
                if "Translation" in result[0]:
                    translation_data, translation_time = result
                elif "Words" in result[0]:
                    analysis_data, analysis_time = result
                elif "CorrectedSentence" in result[0]:
                    grammar_check_data, grammar_check_time = result
            elif isinstance(result[0], str) and isinstance(result[1], float):
                audio_file_path, audio_time = result

    return translation_data, translation_time, analysis_data, analysis_time, audio_file_path, audio_time, grammar_check_data, grammar_check_time

def process_ai_results(translation_data: Dict, analysis_data: Dict, grammar_check_data: Dict, features: Features) -> Tuple[str, List[WordData]]:
    """Processes the results from the AI providers."""
    if features.grammar_check_enabled:
        #translation = grammar_check_data.get("CorrectedSentence", "")  # Remove processing from here
        words = []  # No word analysis when grammar check is on
        translation = ""
    else:
        translation_data = merge_translation_and_analysis_data(translation_data, analysis_data, features.translation_enabled, features.analysis_enabled)
        words = translation_data.get("Words", [])
        translation = translation_data.get("Translation", "")
    return translation, words

def merge_translation_and_analysis_data(translation_data: Dict, analysis_data: Dict, translation_enabled: bool, analysis_enabled: bool) -> Dict:
    """Merges translation and analysis data, removing duplicates if necessary."""
    if analysis_enabled:
        analysis_words = prepare_word_data(analysis_data)
        if translation_enabled:
            if "Words" not in translation_data:
                translation_data["Words"] = []
            translation_data["Words"].extend(analysis_words)
            seen = set()
            translation_data["Words"] = [
                word_data for word_data in translation_data["Words"]
                if word_data.word not in seen and not seen.add(word_data.word)
            ]
        else:
            translation_data["Words"] = analysis_words
    return translation_data

def prepare_word_data(analysis_data: Dict) -> List[WordData]:
    """Prepares WordData objects from analysis data."""
    return [WordData(word=word_data["word"], definition=word_data["definition"]) for word_data in analysis_data.get("Words", [])]

def compile_word_pattern(words: List[WordData]) -> Optional[re.Pattern]:
    """Compiles a regex pattern for word highlighting."""
    if words:
        return re.compile(r'\b(' + '|'.join(re.escape(word_data.word) for word_data in words) + r')\b', flags=re.IGNORECASE)
    return None

# --- Request Handling ---

@app.after_request
def add_permissions_policy(response):
    response.headers['Permissions-Policy'] = 'clipboard-write=(self)'
    return response

@app.route('/add_note_to_anki', methods=['POST'])
async def add_note_to_anki():
    data = request.get_json()
    if not data:
        raise AnkiError('No data provided')

    word = data.get('word')
    definition = data.get('definition')
    context = data.get('context')
    context_translation = data.get('contextTranslation')

    if not word or not definition:
        raise AnkiError('Missing word or definition')

    try:
        anki_response = anki_connector.add_note_to_anki(word, definition, context, context_translation)
        return jsonify({'result': 'Note added successfully', 'noteId': anki_response})
    except Exception as e:
        raise AnkiError(f"Failed to add note to Anki: {e}")

async def translate_and_format_async(text: str, features: Features, config: Config, translation_service: TranslationService, audio_service: Optional[AudioService]) -> str:
    """Translates the text, analyzes it, generates audio, and formats the output as HTML."""

    translation_data, translation_time, analysis_data, analysis_time, audio_file_path, audio_time, grammar_check_data, grammar_check_time = await fetch_ai_data(
        text, features, translation_service, audio_service
    )

    translation, words = process_ai_results(translation_data, analysis_data, grammar_check_data, features)
    word_pattern = compile_word_pattern(words)

    # Pass grammar_check_data to generate_goldendict_html
    html_output = generate_goldendict_html(
        text,
        words,
        translation,
        config,
        audio_file_path,
        translation_time,
        analysis_time,
        audio_time,
        word_pattern,
        grammar_check_data,  # Pass grammar_check_data
        grammar_check_time
    )
    return html_output

async def process_text(text_to_translate: str, features: Features, config: Config, translation_service: TranslationService, audio_service: Optional[AudioService], force_refresh: bool = False) -> str:
    """Processes the text, utilizing caching and handling language-specific logic."""
    cache_key = f"{text_to_translate}-{features.translation_enabled}-{features.tts_enabled}-{features.analysis_enabled}-{features.grammar_check_enabled}"

    if not force_refresh and cache_key in translation_cache and len(text_to_translate) < MAX_TRANSLATION_CACHE_SIZE:
        print(f"Cache hit for: {cache_key}")
        return translation_cache[cache_key]
    else:
        print(f"Cache miss for: {cache_key}")

        if len(translation_cache) >= MAX_TRANSLATION_CACHE_SIZE:
            oldest_key = next(iter(translation_cache))
            translation_cache.pop(oldest_key)

        html_output = await translate_and_format_async(text_to_translate, features, config, translation_service, audio_service)

        if len(text_to_translate) < MAX_TRANSLATION_CACHE_SIZE:
            translation_cache[cache_key] = html_output

        return html_output

# @app.route('/', methods=['GET'])
# async def translate_text_get():
#     text_to_translate = request.args.get('text', '')
#     features = Features(
#         translation_enabled=config.get_setting('translationEnabled', True),
#         tts_enabled=config.get_setting('ttsEnabled', True),
#         analysis_enabled=config.get_setting('analysisEnabled', True),
#         grammar_check_enabled=False # Always disable grammar check for regular translation
#     )

#     detected_language = detect_language(text_to_translate)
#     if detected_language == "English":
#         if len(text_to_translate.split()) >= 2:
#             result = await process_text(text_to_translate, features, config, translation_service, audio_service)
#             return result
#         else:
#             return ""
#     elif detected_language == "Chinese":
#         result = await process_text(text_to_translate, features, config, translation_service, audio_service)
#         return result
#     else:
#         return ""

# @app.route('/grammar_check', methods=['GET'])
# async def grammar_check_get():
#     text_to_check = request.args.get('text', '')
#     if not text_to_check:
#         return "Please provide text to check via the 'text' query parameter."

#     features = Features(
#         translation_enabled=False,
#         tts_enabled=False,
#         analysis_enabled=False,
#         grammar_check_enabled=True  # Enable only grammar check
#     )

#     # Only fetch grammar check data
#     _, _, _, _, _, _, grammar_check_data, grammar_check_time = await fetch_ai_data(
#         text_to_check, features, translation_service, audio_service
#     )

#     # Generate HTML output using the grammar_check_data
#     html_output = generate_grammar_check_html(text_to_check, config, grammar_check_data, grammar_check_time)
    
#     return html_output


async def handle_translation_request(text_to_translate: str, config: Config, translation_service: TranslationService, audio_service: Optional[AudioService]) -> str:
    """Handles translation requests."""
    features = Features(
        translation_enabled=config.get_setting('translationEnabled', True),
        tts_enabled=config.get_setting('ttsEnabled', True),
        analysis_enabled=config.get_setting('analysisEnabled', True),
        grammar_check_enabled=False
    )
    detected_language = detect_language(text_to_translate)
    if detected_language == "English":
        if len(text_to_translate.split()) >= 2:
            result = await process_text(text_to_translate, features, config, translation_service, audio_service)
            return result
        else:
            return ""
    elif detected_language == "Chinese":
        result = await process_text(text_to_translate, features, config, translation_service, audio_service)
        return result
    else:
        return ""

async def handle_grammar_check_request(text_to_check: str, config: Config, translation_service: TranslationService, audio_service: Optional[AudioService]) -> str:
    """Handles grammar check requests."""
    features = Features(
        translation_enabled=False,
        tts_enabled=False,
        analysis_enabled=False,
        grammar_check_enabled=True
    )
    try:
        _, _, _, _, _, _, grammar_check_data, grammar_check_time = await fetch_ai_data(
            text_to_check, features, translation_service, audio_service
        )
        html_output = generate_grammar_check_html(text_to_check, config, grammar_check_data, grammar_check_time)
        return html_output
    except Exception as e:
        print(f"Error during grammar check: {e}")
        return f"Error during grammar check: {e}", 500

@app.route('/', methods=['GET'])
async def process_request():
    text_to_translate = request.args.get('text', '')
    print("kankan" ,text_to_translate)
    # Check for grammar check prefix using startswith
    if text_to_translate.startswith(GRAMMAR_CHECK_PREFIX):
        # Remove the prefix and any leading spaces for grammar check
        text_to_check = text_to_translate[len(GRAMMAR_CHECK_PREFIX):].lstrip()
        return await handle_grammar_check_request(text_to_check, config, translation_service, audio_service)
    else:
        return await handle_translation_request(text_to_translate, config, translation_service, audio_service)


@app.route('/get_settings', methods=['GET'])
def get_settings():
    settings = {
        'translationEnabled': config.get_setting('translationEnabled', True),
        'ttsEnabled': config.get_setting('ttsEnabled', True),
        'analysisEnabled': config.get_setting('analysisEnabled', True),
        'grammarCheckEnabled': config.get_setting('grammarCheckEnabled', False),
        'autoplayEnabled': config.audio.autoplay,
        'selectedProvider': config.get_ai_provider_name(),
        'apiKey': config.get_provider_config(config.selected_provider).api_key,
        'baseUrl': config.get_provider_config(config.selected_provider).base_url,
        'model': config.get_provider_config(config.selected_provider).model,
    }
    return jsonify(settings)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    global config_changed
    data = request.get_json()
    if not data:
        raise ConfigurationError('No data provided')

    for handler in settings_handlers:
        if handler.key in data:
            handler.handler(config, handler.key, data[handler.key])

    config.save_settings(config_path)
    config_changed = True
    # Refresh services and config if necessary
    config.refresh()
    translation_service = TranslationService(config)
    global audio_service
    audio_service = AudioService(config) if config.get_setting('ttsEnabled', True) else None
    # Update global variables
    global anki_connector, cache_manager
    cache_manager = CacheManager()
    anki_connector = AnkiConnector(config, cache_manager)
    return jsonify({'message': 'Settings updated successfully'})

@app.route('/refresh', methods=['GET'])
async def refresh_translation():
    text_to_translate = request.args.get('text', '')
    features = Features(
        translation_enabled=config.get_setting('translationEnabled', True),
        tts_enabled=config.get_setting('ttsEnabled', True),
        analysis_enabled=config.get_setting('analysisEnabled', True),
        grammar_check_enabled=config.get_setting('grammarCheckEnabled', False)
    )
    if text_to_translate:
        result = await process_text(text_to_translate, features, config, translation_service, audio_service, force_refresh=True)
        return result
    else:
        return "Please provide text to translate via the 'text' query parameter."

# --- Main ---

if __name__ == '__main__':
    # Initialize cache manager, config, and services
    cache_manager = CacheManager()
    config, config_path = load_config(cache_manager)
    anki_connector = AnkiConnector(config, cache_manager)
    translation_service = TranslationService(config)
    audio_service = AudioService(config) if config.get_setting('ttsEnabled', True) else None
    settings_handlers = get_settings_handlers(config)
    # --- In-Memory Cache for Translation Results ---
    translation_cache: Dict[str, str] = {}
    # --- Configuration Change Flag ---
    config_changed = False
    app.run(debug=False)