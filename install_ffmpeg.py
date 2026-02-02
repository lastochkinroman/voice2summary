import os
import sys
import zipfile
import requests
from pathlib import Path

def download_ffmpeg():
    print("📥 Скачивание ffmpeg...")

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    download_path = "ffmpeg.zip"
    extract_path = "ffmpeg"

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("✅ ffmpeg скачан")

        print("📦 Распаковка...")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file == "ffmpeg.exe":
                    ffmpeg_path = os.path.join(root, file)
                    print(f"✅ ffmpeg найден: {ffmpeg_path}")

                    update_env_file(ffmpeg_path)
                    return

        print("❌ ffmpeg.exe не найден в архиве")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

def update_env_file(ffmpeg_path):
    env_path = ".env"

    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    ffmpeg_line = f'FFMPEG_PATH={ffmpeg_path}\n'

    found = False
    for i, line in enumerate(lines):
        if line.startswith('FFMPEG_PATH='):
            lines[i] = ffmpeg_line
            found = True
            break

    if not found:
        lines.append(ffmpeg_line)
    with open(env_path, 'w') as f:
        f.writelines(lines)

    print("✅ .env файл обновлен с путем к ffmpeg")

if __name__ == '__main__':
    download_ffmpeg()
