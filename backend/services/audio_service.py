# Audio generation service
# Libraries: gTTS, pydub, ElevenLabs

import os
import time
from gtts import gTTS
from pydub import AudioSegment

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ALEX_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
SAM_VOICE_ID = "AZnzlk1XvdvUeBnXmlld"


def generate_audiobook_audio(script: str, filename_prefix: str = "audiobook") -> str:
    timestamp = int(time.time())
    output_path = f"/tmp/{filename_prefix}_{timestamp}.mp3"
    temp_path = f"/tmp/temp_audiobook_{timestamp}.mp3"

    tts = gTTS(text=script, lang="en", slow=False)
    tts.save(temp_path)

    audio = AudioSegment.from_mp3(temp_path)
    faster = audio.speedup(playback_speed=1.1)
    faster.export(output_path, format="mp3")

    os.remove(temp_path)
    return output_path


def generate_podcast_audio_gtts(script: str, filename_prefix: str = "podcast") -> str:
    timestamp = int(time.time())
    output_path = f"/tmp/{filename_prefix}_{timestamp}.mp3"
    temp_files = []  # fixed — defined here

    lines = []
    for line in script.split("\n"):
        line = line.strip()
        if line.startswith("Alex:"):
            text = line.replace("Alex:", "").strip()
            if text:
                lines.append(("alex", text))
        elif line.startswith("Sam:"):
            text = line.replace("Sam:", "").strip()
            if text:
                lines.append(("sam", text))

    if not lines:
        raise ValueError("No valid Alex:/Sam: lines found in script.")

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=400)

    for i, (speaker, text) in enumerate(lines):
        temp_path = f"/tmp/temp_{timestamp}_{i}.mp3"  # fixed — /tmp not audio/
        temp_files.append(temp_path)

        slow = False
        tts = gTTS(text=text, lang="en", slow=slow)
        tts.save(temp_path)

        segment = AudioSegment.from_mp3(temp_path)
        segment = segment.speedup(playback_speed=1.1)
        combined += segment + pause

    combined.export(output_path, format="mp3")

    for temp_path in temp_files:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return output_path


def generate_podcast_audio_elevenlabs(script: str, filename_prefix: str = "podcast") -> str:
    if not ELEVENLABS_API_KEY:
        raise ValueError("ElevenLabs API key not found.")

    from elevenlabs.client import ElevenLabs
    from elevenlabs import save

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    timestamp = int(time.time())
    output_path = f"/tmp/{filename_prefix}_elevenlabs_{timestamp}.mp3"
    temp_files = []  # fixed — defined here

    lines = []
    for line in script.split("\n"):
        line = line.strip()
        if line.startswith("Alex:"):
            text = line.replace("Alex:", "").strip()
            if text:
                lines.append(("alex", text))
        elif line.startswith("Sam:"):
            text = line.replace("Sam:", "").strip()
            if text:
                lines.append(("sam", text))

    if not lines:
        raise ValueError("No valid Alex:/Sam: lines found in script.")

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=400)

    for i, (speaker, text) in enumerate(lines):
        temp_path = f"/tmp/temp_el_{timestamp}_{i}.mp3"  # fixed — /tmp
        temp_files.append(temp_path)

        voice_id = ALEX_VOICE_ID if speaker == "alex" else SAM_VOICE_ID

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
        )
        save(audio, temp_path)

        segment = AudioSegment.from_mp3(temp_path)
        combined += segment + pause

    combined.export(output_path, format="mp3")

    for temp_path in temp_files:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return output_path