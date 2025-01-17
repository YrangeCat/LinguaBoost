# LinguaBoost

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com//YrangeCat/LinguaBoost/blob/main/LICENSE)

**LinguaBoost** is a powerful AI-powered extension for GoldenDict that enhances your language learning experience. It provides instant translations, contextual definitions, grammar checking, and seamless Anki integration, all within your favorite dictionary software.

## Features

*   **Instant Translation:** Translate sentences on the fly as you look them up in GoldenDict.
*   **Contextual Definitions:** Hover over highlighted words to see their definitions within the context of the sentence.
*   **Smart Highlighting:** Automatically highlights key vocabulary and phrases for enhanced understanding.
*   **Grammar Check:**  Provides in-depth analysis and suggestions for more complex grammatical issues. Triggered by adding `~` before your sentence.
*   **Anki Integration:** One-click addition of words, definitions, and example sentences to your Anki decks.
*   **Automatic Pronunciation:** Leverages Microsoft TTS for automatic audio playback of words and sentences.
*   **Customizable:** Configure settings like AI provider, API keys, Anki deck, and more.

## Getting Started

### Prerequisites

*   **GoldenDict:**  Make sure you have the latest version of GoldenDict installed.
*   **Python 3.7+:** Ensure you have Python 3.7 or a later version installed on your system.
*   **Anki & AnkiConnect:** For Anki integration, you'll need Anki installed and running with the AnkiConnect add-on (ID: `2055492159`).
*   **API Keys:** Obtain API keys for your chosen AI provider (e.g., Google AI for Gemini, OpenAI compatible APIs like SiliconFlow).

### Installation

1.  **Clone the Repository:**

    ```bash
    git clone [https://github.com//YrangeCat/LinguaBoost.git](https://github.com//YrangeCat/LinguaBoost.git) # Replace with your repository URL
    cd yourrepository
    ```

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Copy `config.ini.example` to `config.ini`:**

    ```bash
    cp config.ini.example config.ini
    ```

2.  **Edit `config.ini`:**
    *   **`[providers]`:** Select your preferred `selected_provider` (e.g., `gemini`, `openai`).
    *   **`[providers.your_selected_provider]`:** Fill in your `api_key`, `model`, and other necessary details.
        *   **Gemini API:**
            *   Obtain an API key from [Google AI Studio](https://ai.google.dev/).
        *   **OpenAI Compatible API (e.g., SiliconFlow):**
            *   Register and obtain an API key from a compatible provider like [SiliconFlow](https://siliconflow.cn/).
            *   You may also need to adjust the `base_url`.
    *   **`[anki]`:** Configure `ankiconnecturl`, `deckname`, and `modelname` for Anki integration.
    *   **`[anki.fields]`:** Map the fields in your Anki model to the corresponding data provided by LinguaBoost.
    *   **`[voice]`:** Specify the default voice for text-to-speech.
    *   **`[audio]`:** Configure autoplay behavior.
    *   **`[settings]`:** Enable or disable features like `translationenabled`, `ttsenabled`, and `analysisenabled`.
    *   **`[html_template]`:** Adjust HTML template options.

### Running LinguaBoost

1.  **Start the Application:**

    ```bash
    python app.py
    ```
    Keep this process running in the background.

### GoldenDict Setup

1.  **Open GoldenDict's Dictionary Sources:** Go to *Edit* -> *Dictionaries* -> *Sources* -> *Websites*.

2.  **Add LinguaBoost:**
    *   Click *Add*.
    *   **Enabled:** Checked
    *   **Name:**  `LinguaBoost` (or any name you prefer)
    *   **Address:** `http://127.0.0.1:5000/?text=%GDWORD%`
    *   Click *Apply*.

3.  **Add LinguaBoost Grammar Check (Optional):**
    *   Click *Add*.
    *   **Enabled:** Checked
    *   **Name:** `LinguaBoost Grammar Check` (or any name you prefer)
    *   **Address:** `http://127.0.0.1:5000/?text=~%GDWORD%`
    *   Click *Apply*.

4.  **Save Settings:** Click *OK* to save your changes.

### Usage

*   **Basic Translation and Analysis:** Look up a sentence in GoldenDict. LinguaBoost will automatically translate it and highlight key words. Hover over highlighted words for contextual definitions.

*   **Grammar Check:**
    *   **Complex Mode:** Add `~` at the beginning of a sentence (e.g., `~This is a setence.`) to trigger a detailed grammar check.
    *   **Simple Mode:** Select `simple` mode from the gear icon within the LinguaBoost interface for basic grammar corrections.
    *   **Note:** Grammar Check has its own panel in GoldenDict, be sure to add it in GoldenDict's settings.

*   **Anki Integration:** Click on a highlighted word to add it to your Anki deck. The card will include the word, its definition, and the original sentence.

*   **Settings:** Click the gear icon in the top right corner of the LinguaBoost panel to adjust settings like AI provider, API keys, and enabled features.

## Troubleshooting

*   **AnkiConnect Not Connecting:** Make sure Anki is running in the background and that the AnkiConnect add-on is installed and enabled.
*   **API Key Issues:** Double-check that your API keys are correct and that your chosen AI provider is properly configured in `config.ini`.
*   **Errors in the LinguaBoost Panel:** Check the console where you ran `app.py` for error messages.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to the repository.

## License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/url?sa=E&source=gmail&q=LICENSE) file for details.
