import os
import asyncio
import uuid
import logging
from pathlib import Path
from datetime import datetime

import aiofiles
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from mistralai.client import MistralClient
from pydub import AudioSegment

from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
mistral_client = MistralClient(api_key=Config.MISTRAL_API_KEY)
Path(Config.TEMP_DIR).mkdir(exist_ok=True)


class AudioProcessor:

    @staticmethod
    async def download_audio(file_url: str, file_path: str):
        try:
            response = requests.get(file_url)
            response.raise_for_status()

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(response.content)

            logger.info(f"Audio downloaded: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return False

    @staticmethod
    async def convert_to_wav(input_path: str, output_path: str):
        try:
            filename, file_extension = os.path.splitext(input_path)
            file_extension = file_extension.lower()
            
            if file_extension == '.ogg':
                import shutil
                shutil.copy(input_path, output_path)
                logger.info(f"Audio copied (no conversion needed): {output_path}")
                return True
                
            import subprocess
            import sys
            
            ffmpeg_cmd = [
                Config.FFMPEG_PATH,
                "-i", input_path,
                "-ar", "16000",
                "-ac", "1",
                "-sample_fmt", "s16",
                output_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion error: {result.stderr.decode('cp1251')}")
                return False
                
            logger.info(f"Audio converted: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return False


class SpeechRecognizer:

    def __init__(self):
        self.api_url = Config.SALUTE_SPEECH_URL
        self.oauth_url = Config.SALUTE_SPEECH_OAUTH_URL
        self.auth_key = Config.SALUTE_SPEECH_AUTH_KEY
        self.scope = Config.SALUTE_SPEECH_SCOPE
        self.access_token = None
        self.token_expires_at = 0

    async def _get_access_token(self) -> str:
        try:
            current_time = datetime.now().timestamp() * 1000
            if self.access_token and (self.token_expires_at - current_time) > 60000:
                return self.access_token

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': str(uuid.uuid4()),
                'Authorization': f'Basic {self.auth_key}'
            }

            data = {
                'scope': self.scope
            }

            response = requests.post(
                self.oauth_url,
                headers=headers,
                data=data,
                verify=False
            )
            response.raise_for_status()
            result = response.json()

            self.access_token = result.get('access_token')
            self.token_expires_at = result.get('expires_at')

            logger.info("Получен новый Access Token")
            return self.access_token
        except Exception as e:
            logger.error(f"Ошибка получения Access Token: {e}")
            raise

    async def recognize(self, audio_file_path: str) -> str:
        try:
            token = await self._get_access_token()

            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()

            filename, file_extension = os.path.splitext(audio_file_path)
            file_extension = file_extension.lower()
            
            if file_extension == '.ogg':
                headers = {
                    'Content-Type': 'audio/ogg;codecs=opus',
                    'Authorization': f'Bearer {token}',
                    'X-Request-ID': str(uuid.uuid4())
                }
            elif file_extension == '.wav' or file_extension == '.pcm':
                headers = {
                    'Content-Type': 'audio/x-pcm;bit=16;rate=16000',
                    'Authorization': f'Bearer {token}',
                    'X-Request-ID': str(uuid.uuid4())
                }
            elif file_extension == '.mp3':
                headers = {
                    'Content-Type': 'audio/mpeg',
                    'Authorization': f'Bearer {token}',
                    'X-Request-ID': str(uuid.uuid4())
                }
            else:
                logger.error(f"Unsupported audio format: {file_extension}")
                return ""

            response = requests.post(
                self.api_url,
                headers=headers,
                data=audio_data,
                verify=False
            )
            response.raise_for_status()
            result = response.json()
            text = result.get('result', '')
            logger.info(f"Speech recognized: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return ""


class MeetingAnalyzer:

    async def analyze_meeting(self, transcript: str) -> str:
        try:
            prompt = f"""
            Ты ассистент для анализа деловых встреч. Проанализируй текст встречи и создай структурированное резюме.

            Текст встречи:
            {transcript}

            Создай краткое содержание по следующей структуре:
            1. Участники встречи (кто присутствовал)
            2. Основные темы обсуждения
            3. Принятые решения и выводы
            4. Назначенные задачи (что, кто, сроки)
            5. Следующие шаги и дата следующей встречи

            Будь лаконичным и выделяй самое важное.

            не составляй никаких таблиц
            """

            response = mistral_client.chat(
                model="mistral-medium",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный ассистент для анализа деловых встреч. Ты создаешь четкие, структурированные резюме."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )

            analysis = response.choices[0].message.content
            logger.info("Meeting analysis completed")
            return analysis

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return "Не удалось проанализировать встречу."


async def handle_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    await message.reply_text("🎤 Обрабатываю ваше аудио сообщение...")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_id = f"{user.id}_{timestamp}"
        original_file = os.path.join(Config.TEMP_DIR, f"{audio_id}_original.ogg")
        if message.voice:
            file = await message.voice.get_file()
        elif message.audio:
            file = await message.audio.get_file()
        else:
            await message.reply_text("❌ Не удалось получить аудио файл.")
            return
        processor = AudioProcessor()
        if not await processor.download_audio(file.file_path, original_file):
            await message.reply_text("❌ Ошибка при загрузке аудио.")
            return
        
        await message.reply_text("🔍 Распознаю речь...")
        recognizer = SpeechRecognizer()
        transcript = await recognizer.recognize(original_file)
        if not transcript:
            await message.reply_text("❌ Не удалось распознать речь. Попробуйте ещё раз.")
            return
        logger.info(f"Transcript for user {user.id}: {transcript[:100]}...")
        await message.reply_text("🤖 Анализирую содержание...")
        analyzer = MeetingAnalyzer()
        summary = await analyzer.analyze_meeting(transcript)
        response_text = f"📋 **Анализ встречи**\n\n{summary}"
        if len(response_text) > 4000:
            parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            for part in parts:
                await message.reply_text(part, parse_mode='Markdown')
        else:
            await message.reply_text(response_text, parse_mode='Markdown')
        transcript_preview = transcript[:500] + "..." if len(transcript) > 500 else transcript
        await message.reply_text(
            f"📝 **Распознанный текст (фрагмент):**\n\n{transcript_preview}",
            parse_mode='Markdown'
        )
        await cleanup_files([original_file])
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await message.reply_text("⚠️ Произошла ошибка при обработке. Попробуйте ещё раз.")


async def cleanup_files(file_paths):
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎤 **Голосовой ассистент для встреч**

Отправьте мне голосовое сообщение, аудиофайл или текст с записью встречи, и я:
1. 🎵 Распознаю речь через SaluteSpeech (при отправке аудио)
2. 🤖 Проанализирую содержание через Mistral AI
3. 📋 Создам структурированное резюме встречи

**Что я выделяю:**
• Участники встречи
• Основные темы обсуждения
• Принятые решения
• Назначенные задачи
• Следующие шаги

Просто отправьте голосовое сообщение, аудиофайл или текст и получите анализ!
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    text = message.text.strip()
    
    await message.reply_text("📝 Обрабатываю ваш текст...")
    try:
        logger.info(f"Text received from user {user.id}: {text[:100]}...")
        await message.reply_text("🤖 Анализирую содержание...")
        analyzer = MeetingAnalyzer()
        summary = await analyzer.analyze_meeting(text)
        response_text = f"📋 **Анализ встречи**\n\n{summary}"
        if len(response_text) > 4000:
            parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            for part in parts:
                await message.reply_text(part, parse_mode='Markdown')
        else:
            await message.reply_text(response_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        await message.reply_text("⚠️ Произошла ошибка при обработке. Попробуйте ещё раз.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📋 **Как использовать бота:**

1. **Запись встречи**: Запишите голосовое сообщение во время встречи
2. **Отправка**: Отправьте аудио сообщение или текст боту
3. **Обработка**: Бот автоматически:
   - Распознает речь (при отправке аудио)
   - Проанализирует содержание через AI
   - Создаст структурированное резюме

**Поддерживаемые форматы:**
• Голосовые сообщения (лучшее качество)
• Аудио файлы (MP3, OGG, WAV)
• Текстовые сообщения (для прямого анализа)

**Советы для лучшего качества:**
• Говорите четко и разборчиво
• Избегайте фонового шума
• Записывайте в тихом помещении
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


def main():
    required_vars = ['TELEGRAM_TOKEN', 'MISTRAL_API_KEY', 'SALUTE_SPEECH_AUTH_KEY']
    for var in required_vars:
        if not getattr(Config, var, None):
            logger.error(f"❌ {var} не указан в .env файле")
            return
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO,
        handle_audio_message
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))
    from telegram.ext import CommandHandler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    print("🤖 Голосовой ассистент для встреч запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
