from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

# Added a timeout of 60 seconds to prevent connection drops during upload
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=60.0
)


def transcribe_chunked_audio(chunk_paths: list):
    """
    Transcribes audio chunks using Groq's whisper-large-v3-turbo.
    """
    full_transcript = []
    print(f"\n[INFO] Starting Groq cloud transcription...")

    for i, path in enumerate(chunk_paths):
        file_name = os.path.basename(path)  # Extract just 'chunk_0.mp3'
        print(f"Sending Chunk {i+1}/{len(chunk_paths)} to Groq: {file_name}")

        try:
            with open(path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    # Use the base file_name here
                    file=(file_name, file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )

                if transcription.text:
                    full_transcript.append(transcription.text)

        except Exception as e:
            print(f"❌ Error transcribing {file_name}: {e}")
            # Optional: continue to next chunk even if one fails
            continue

    result = " ".join(full_transcript)

    with open("transcript_original.txt", "w", encoding="utf-8") as f:
        f.write(result)

    return result
