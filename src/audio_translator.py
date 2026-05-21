from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=60.0
)


def translate_chunked_audio(chunk_paths: list):
    """
    Translates audio chunks directly to English using Groq's whisper-large-v3.
    Note: The 'translations' endpoint always outputs English.
    """
    full_translation = []
    print(f"\n[INFO] Starting Groq cloud translation (Audio -> English)...")

    for i, path in enumerate(chunk_paths):
        file_name = os.path.basename(path)
        print(f"Translating Chunk {i+1}/{len(chunk_paths)}: {file_name}")

        try:
            with open(path, "rb") as file:
                # Use 'translations' instead of 'transcriptions'
                translation = client.audio.translations.create(
                    file=(file_name, file.read()),
                    model="whisper-large-v3",
                    response_format="verbose_json",
                )

                if translation.text:
                    full_translation.append(translation.text)

        except Exception as e:
            print(f"❌ Error translating {file_name}: {e}")
            continue

    result = " ".join(full_translation)

    with open("translation_english.txt", "w", encoding="utf-8") as f:
        f.write(result)

    return result
