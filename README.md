# Voice2Summary

> Telegram-бот, который слушает ваши встречи и делает по ним нормальные конспекты

Надоело конспектировать встречи? Просто запишите голосовое сообщение в Telegram — бот сам всё разберёт и структурирует.

## Что умеет

- Распознаёт речь из голосовых и аудио
- Вытаскивает главное через AI
- Пишет понятное резюме: кто был, что решили, кто что делает

## Установка

**1. Поставьте зависимости:**
```bash
pip install -r requirements.txt
```

**2. Создайте `.env` файл:**
```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
MISTRAL_API_KEY=ваш_ключ_mistral
SALUTE_SPEECH_AUTH_KEY=ваш_токен_salutespeech
```

Токены берите тут:
- Telegram — [@BotFather](https://t.me/botfather)
- Mistral — [console.mistral.ai](https://console.mistral.ai)
- SaluteSpeech — developerssber

**3. Запустите:**
```bash
python main.py
```

## Как пользоваться

1. Напишите боту `/start`
2. Отправьте голосовое сообщение или аудиофайл
3. Получите резюме через пару секунд

Можно даже просто скинуть текст встречи — бот его тоже разберёт.

## Что получите на выходе

<img width="728" height="776" alt="изображение" src="https://github.com/user-attachments/assets/cf42dce1-f944-4c30-8e10-9a4f1fc04cb2" />

<img width="676" height="735" alt="изображение" src="https://github.com/user-attachments/assets/ad13a4a2-1938-4cbe-a2ea-5d3adb55d502" />

<img width="712" height="815" alt="изображение" src="https://github.com/user-attachments/assets/fd41244d-0800-4422-94c2-4ab2b6119dfa" />

*Естественно, если подключить посильнее модель, то результат будет сильно лучше.


## Технологии

Python-telegram-bot, SaluteSpeech, Mistral AI, FFmpeg

---

MIT License
