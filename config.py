import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
    SALUTE_SPEECH_AUTH_KEY = os.getenv('SALUTE_SPEECH_AUTH_KEY')
    SALUTE_SPEECH_SCOPE = os.getenv('SALUTE_SPEECH_SCOPE', 'SALUTE_SPEECH_PERS')
    FFMPEG_PATH = os.getenv('FFMPEG_PATH')

    TEMP_DIR = "temp_audio"

    SALUTE_SPEECH_URL = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
    SALUTE_SPEECH_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
