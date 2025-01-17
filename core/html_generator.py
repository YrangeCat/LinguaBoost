import re
import json
import os
import sys
from core.config import Config
from typing import Dict, List, Callable, Optional, NamedTuple
from jinja2 import Environment, FileSystemLoader, select_autoescape
from settings.settings import get_settings_handlers

# --- Data Structures ---
class WordData(NamedTuple):
    word: str
    definition: str

# --- Jinja2 Setup ---
def _get_templates_path() -> str:
    if getattr(sys, 'frozen', False):
        # The application is frozen (packaged)
        application_path = os.path.join(os.path.dirname(sys.executable), "_internal")
        templates_path = os.path.join(application_path, "templates")
    else:
        # The application is not frozen (running from source)
        application_path = os.path.dirname(os.path.abspath(__file__))
        templates_path = os.path.join(application_path, "..","templates")

    return templates_path

TEMPLATES_DIR = _get_templates_path()
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

# --- Helper Functions ---
def _get_static_path() -> str:
    if getattr(sys, 'frozen', False):
        # The application is frozen (packaged)
        application_path = os.path.join(os.path.dirname(sys.executable), "_internal")
        static_path = os.path.join(application_path, "static")
    else:
        # The application is not frozen (running from source)
        application_path = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(application_path, "..", "static")

    return static_path

def load_content(file_name: str) -> str:
    """Loads content from a file in the static directory, returning an empty string if not found."""
    static_path = _get_static_path()
    full_path = os.path.join(static_path, file_name)

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: file not found at {full_path}")
        return ""

def create_anki_link(word: str, definition: str) -> str:
    """Creates an Anki link with the given word and definition."""
    return f'<a href="#" class="highlighted-term" data-definition="{definition}">{word}</a>'

def highlight_words(text: str, words_data: List[WordData], word_highlighter: Optional[Callable[[str, List[WordData]], str]]) -> str:
    """Highlights words in the text using the provided highlighting function.
    If no function is provided, returns the original text."""
    if not word_highlighter:
        return text
    return word_highlighter(text, words_data)

def create_word_highlighter(compiled_pattern: re.Pattern) -> Callable[[str, List[WordData]], str]:
    """Creates a word highlighting function based on a compiled regex pattern."""
    def word_highlighter(text: str, words_data: List[WordData]) -> str:
        """Highlights words in the text based on the pre-compiled pattern."""
        word_to_definition = {word_data.word: word_data.definition for word_data in words_data}

        def replace_with_link(match: re.Match) -> str:
            """Replaces a matched word with an Anki link."""
            word = match.group(0)
            definition = word_to_definition.get(word, "")
            return create_anki_link(word, definition)

        return compiled_pattern.sub(replace_with_link, text)
    return word_highlighter

# --- Main Function ---

def generate_goldendict_html(
    text: str,
    words: List[WordData],
    translation: str,
    config: Config,
    audio_file_path: str = "",
    translation_time: float = 0,
    analysis_time: float = 0,
    audio_time: float = 0,
    compiled_pattern: Optional[re.Pattern] = None,
    grammar_check_data: Dict = None,
    grammar_check_time: float = 0
) -> str:
    """Generates the complete HTML output for GoldenDict."""
    template = env.get_template("goldendict_output.html")
    css_content = load_content("styles.css")
    js_content = load_content("scripts.js")
    settings_handlers = get_settings_handlers(config)
    word_highlighter = create_word_highlighter(compiled_pattern) if compiled_pattern else None
    highlighted_text = highlight_words(text, words, word_highlighter)

    # Extract corrected sentence and guide if available
    corrected_sentence = ""
    correction_guide = ""
    if grammar_check_data:
        corrected_sentence = grammar_check_data.get("CorrectedSentence", "")
        correction_guide = grammar_check_data.get("CorrectionGuide", "")

    return template.render(
        settings_handlers=settings_handlers,
        css_content=css_content,
        highlighted_text=highlighted_text,
        translation=translation,
        audio_file_path=audio_file_path,
        autoplay=config.audio.autoplay,
        translation_time=translation_time,
        analysis_time=analysis_time,
        audio_time=audio_time,
        anki_config_js=json.dumps({
            "deckName": config.anki.deck_name,
            "modelName": config.anki.model_name,
            "fields": config.anki.fields,
            "ankiConnectUrl": config.anki.connect_url,
            "api_key": config.anki.api_key
        }),
        js_content=js_content,
        show_translation=config.html_template.show_translation,
        show_timing_info=config.html_template.show_timing_info,
        grammar_check_time=grammar_check_time,
        original_text=text if grammar_check_data else '',  # Pass original text if grammar check data is available
        corrected_text=corrected_sentence,  # Pass corrected sentence
        correction_guide=correction_guide  # Pass correction guide
    )

def generate_grammar_check_html(original_text: str, config: Config, grammar_check_data: Dict = None, grammar_check_time: float = None) -> str:
    """Generates the HTML output for grammar check results, reusing goldendict_output.html."""
    template = env.get_template("grammar_check.html")
    css_content = load_content("styles.css")
    js_content = load_content("scripts.js")
    settings_handlers = get_settings_handlers(config)

    # Extract corrected sentence and guide if available
    corrected_sentence = ""
    correction_guide = ""
    if grammar_check_data:
        corrected_sentence = grammar_check_data.get("CorrectedSentence", "")
        correction_guide = grammar_check_data.get("CorrectionGuide", "")

    # Handle None for grammar_check_time here:
    if grammar_check_time is None:
        grammar_check_time = 0.0

    return template.render(
        settings_handlers=settings_handlers,
        css_content=css_content,
        original_text=original_text,
        translation=corrected_sentence,  # Use corrected text as translation
        correction_guide=correction_guide,
        audio_file_path="",  # No audio for grammar check
        autoplay=False,
        translation_time=0,  # No translation time
        analysis_time=0,  # No analysis time
        audio_time=0,  # No audio time
        anki_config_js="{}",  # Empty Anki config
        js_content=js_content,
        show_translation=True,  # Show the "translation" section
        show_timing_info=config.html_template.show_timing_info,
        grammar_check_time=grammar_check_time
    )