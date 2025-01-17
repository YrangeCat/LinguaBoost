import os
import tempfile
import time
from edge_tts.communicate import Communicate
from core.config import Config
from core.types import AudioConfig
from typing import Tuple
from core.errors import AIProviderError

class AudioService:
    def __init__(self, config: Config):
        self.config = config
        self.audio_config = config.audio

    async def generate_audio(self, text: str) -> Tuple[str, float]:
        start_time = time.perf_counter()
        voice = self.config.voice_default
        # Create a temporary directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)  # Ensure the directory exists
        audio_file_path = os.path.join(temp_dir, next(tempfile._get_candidate_names()) + ".mp3")
        try:
            communicator = Communicate(text, voice)
            await communicator.save(audio_file_path)
        except Exception as e:
            print(f"Error generating audio: {e}")
            raise AIProviderError(f"Error generating audio with edge-tts: {e}")
        return audio_file_path, time.perf_counter() - start_time