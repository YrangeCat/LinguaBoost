# prompts/custom_prompt.py
from typing import Callable
import re

def detect_language(text: str) -> str:
    """
    Detects the language of the given text based on Unicode character ranges.

    Args:
        text: The text to analyze.

    Returns:
        "Chinese" if the text primarily contains Chinese characters, "English" otherwise.
    """
    chinese_count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # Basic CJK Unified Ideographs
            chinese_count += 1
    
    if chinese_count / len(text) > 0.1:
        return "Chinese"
    else:
        return "English"

def generate_translation_prompt(text: str) -> str:
    """
    Generates a prompt for translating a sentence, automatically detecting the source language.

    Args:
        text: The sentence to translate.

    Returns:
        A string containing the complete prompt.
    """
    source_language = detect_language(text)

    if source_language == "Chinese":
        target_language = "English"
    else:
        target_language = "simplified Chinese"

    return f"""
        Translate the following sentence into {target_language}.

        Input Sentence: {text}

        Instructions:
        1. **Translation:**
            *   Translate the entire sentence into accurate, {target_language}.
            *   Maintain the original grammatical structure.
            *   Use precise {target_language} equivalents for technical terms.
            *   Output a JSON object that contains the translation as a single JSON string named "Translation".
        """

def generate_analysis_prompt(text: str, definition_language: str = "English") -> str:
    """
    Generates a prompt for extracting vocabulary from a sentence.

    Args:
        text: The sentence to analyze.
        definition_language: The desired language for definitions.

    Returns:
        A string containing the complete prompt.
    """
    return f"""
        Extract vocabulary from the following sentence.

        Input Sentence: {text}

        Output a JSON object as follows:

        ```json
        {{
        "Words": [
            {{"word": "word/phrase", "definition": "definition in {definition_language}"}},
            ...
        ]
        }}
        ```

        Instructions:
        1. **Vocabulary Extraction:**
            *   Identify and extract both:
                *   **Idioms and collocations:**  (e.g., "in terms of," "kick the bucket").
                *   **Complex Words:** Vocabulary exceeding the CET-4 requirements
            *   For each extracted word or phrase, create a JSON object within the "Words" array:
                *   "word": The word or phrase (string).
                *   "definition": Its {definition_language} definition, considering the context (string).
        """

def generate_grammar_check_prompt(text: str) -> str:
    """
    Generates a prompt for correcting grammatical errors in a sentence.

    Args:
        text: The sentence to check.

    Returns:
        A string containing the complete prompt.
    """
    return f"""
        Correct any grammatical errors in the following sentence and provide a guide for correction.

        Input Sentence: {text}

        Instructions:
        1. **Correction:**
            *   Identify and correct any grammatical errors in the sentence.
            *   Maintain the original meaning and sentence structure as much as possible..
            *   If Chinese appears in the sentence, please replace it with a suitable English expression.
        2. **Guide**
            *   Provide specific guidance on the grammatical errors found and how they were corrected.
            *   Structure the guide using the following **markdown** format (not json):
                1.  **Error 1 Title (e.g., Spelling Error, Subject-Verb Agreement):**
                    *   **Description:** Briefly describe the error.
                    *   **Rule/Principle:** Explain the grammatical rule or principle involved.
                    *   **Example:** (Optional) Provide an example of the correct usage.
                2.  **Error 2 Title:**
                    *   **Description:** ...
                    *   **Rule/Principle:** ...
                    *   **Example:** ...
                (Continue with numbered items for each error found)
        3. **Output**
            *   Output a JSON object that contains the following:
                * "CorrectedSentence": The corrected sentence as a single JSON string. Please bold the modified parts.
                * "CorrectionGuide": specific guidance on the grammatical errors found as a single JSON string.
        """
