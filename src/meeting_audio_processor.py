import os
import warnings
from typing import Optional

import soundcard as sc
import soundfile as sf
import numpy as np

from pydub import AudioSegment

warnings.filterwarnings("ignore")


def record_system_audio(
    duration: Optional[int] = None,
    samplerate=16000,
    channels=1,
    bitrate="64k",
    output_dir="recordings",
    stop_event=None
):
    """
    Records system audio using WASAPI loopback
    and converts it to MP3. If duration is None,
    press 'q' to stop recording.

    Returns:
        mp3_file_path (str)
    """

    # ================= CREATE OUTPUT DIR =================

    os.makedirs(output_dir, exist_ok=True)

    # ================= FILE NAMES =================

    temp_wav = os.path.join(
        output_dir,
        f"temp_audio.wav"
    )

    final_mp3 = os.path.join(
        output_dir,
        f"converted_audio.mp3"
    )

    try:

        # ================= GET SPEAKER =================

        speaker = sc.default_speaker()

        print(f"\nUsing Speaker: {speaker.name}")

        print("\nRecording system audio...")

        # ================= RECORD AUDIO =================

        with sc.get_microphone(
            id=str(speaker.name),
            include_loopback=True
        ).recorder(
            samplerate=samplerate,
            channels=channels
        ) as mic:
            if duration and duration > 0:
                data = mic.record(
                    numframes=samplerate * duration
                )
            else:
                try:
                    import msvcrt
                except ImportError:
                    print("Manual stop is only supported on Windows.")
                    return None

                print("Press 'q' to stop recording...")
                chunk_seconds = 0.5
                chunk_frames = int(samplerate * chunk_seconds)
                frames = []

                while True:
                    chunk = mic.record(numframes=chunk_frames)
                    frames.append(chunk)

                    if stop_event and stop_event.is_set():
                        break

                    try:
                        if msvcrt.kbhit():
                            key = msvcrt.getwch()
                            if key.lower() == "q":
                                break
                    except Exception:
                        pass


                data = (
                    np.concatenate(frames, axis=0)
                    if frames
                    else np.empty((0, channels), dtype="float32")
                )

            if data.size == 0:
                print("No audio captured.")
                return None

            sf.write(
                temp_wav,
                data,
                samplerate
            )

        print("\nWAV recording saved!")

        # ================= CONVERT TO MP3 =================

        print("\nConverting to MP3...")

        audio = AudioSegment.from_wav(temp_wav)

        audio.export(
            final_mp3,
            format="mp3",
            bitrate=bitrate
        )

        print("\nMP3 saved successfully!")

        # ================= DELETE TEMP WAV =================

        os.remove(temp_wav)

        print("\nTemporary WAV deleted!")

        # ================= FILE INFO =================

        file_size = os.path.getsize(final_mp3) / (1024 * 1024)

        print("\n========== RECORDING COMPLETE ==========")

        print(f"Saved File : {final_mp3}")

        print(f"File Size  : {file_size:.2f} MB")

        print("========================================")

        return final_mp3

    except Exception as e:

        print("\nRecording failed!")
        print(e)

        return None
