from pydub import AudioSegment
import os

OUTPUT_DIR = "recordings"


def chunk_audio(
    audio_path: str,
    chunk_minutes: int = 10,
    output_dir: str = OUTPUT_DIR,
) -> list[str]:
    """Chunks the audio file into smaller segments for Groq."""
    os.makedirs(output_dir, exist_ok=True)

    audio = AudioSegment.from_file(audio_path)
    chunk_ms = chunk_minutes * 60 * 1000
    base_name = os.path.splitext(os.path.basename(audio_path))[0]

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = os.path.join(output_dir, f"{base_name}_chunk_{i}.mp3")
        chunk.export(chunk_path, format="mp3", bitrate="128k")
        chunks.append(chunk_path)

    return chunks
