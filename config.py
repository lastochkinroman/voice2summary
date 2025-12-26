import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
    SALUTE_SPEECH_TOKEN = os.getenv('SALUTE_SPEECH_TOKEN')
    FFMPEG_PATH = os.getenv('FFMPEG_PATH')

    TEMP_DIR = "temp_audio"

    SALUTE_SPEECH_URL = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
