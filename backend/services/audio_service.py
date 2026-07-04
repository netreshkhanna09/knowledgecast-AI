# Audio generation service
# Libraries: gTTS, pydub, ElevenLabs

import os
import time
from gtts import gTTS
from pydub import AudioSegment

# ElevenLabs import — optional, only if API key exists
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# ElevenLabs voice IDs — change these to your preferred voices
ALEX_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
SAM_VOICE_ID = "AZnzlk1XvdvUeBnXmlld"   # Domi voice


def generate_audiobook_audio(script: str, filename_prefix: str = "audiobook") -> str:
    """
    Convert audiobook script to single-voice MP3 using gTTS.
    
    Args:
        script: full narration text
        filename_prefix: prefix for output filename
        
    Returns:
        path to generated MP3 file
    """
    timestamp = int(time.time())
    output_path = f"audio/{filename_prefix}_{timestamp}.mp3"
    temp_path = f"audio/temp_audiobook_{timestamp}.mp3"

    tts = gTTS(text=script, lang="en", slow=False)
    tts.save(temp_path)

    # speed up by 1.25x
    audio = AudioSegment.from_mp3(temp_path)
    faster = audio.speedup(playback_speed=1.1)
    faster.export(output_path, format="mp3")

    os.remove(temp_path)
    return output_path


def generate_podcast_audio_gtts(script: str, filename_prefix: str = "podcast") -> str:
    """
    Convert podcast script to two-voice MP3 using gTTS.
    Alex speaks at normal speed, Sam speaks slightly slower.
    Uses pydub to merge all lines in order.
    
    Args:
        script: podcast script with Alex:/Sam: format
        filename_prefix: prefix for output filename
        
    Returns:
        path to generated MP3 file
    """
    timestamp = int(time.time())
    output_path = f"audio/{filename_prefix}_{timestamp}.mp3"
    temp_files = []

    # parse script into lines
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

    # generate audio for each line
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=400)  # 400ms pause between lines

    for i, (speaker, text) in enumerate(lines):
        temp_path = f"audio/temp_{timestamp}_{i}.mp3"
        temp_files.append(temp_path)

        # alex normal speed, sam slightly slower
        slow = True if speaker == "sam" else False
        tts = gTTS(text=text, lang="en", slow=slow)
        tts.save(temp_path)

        segment = AudioSegment.from_mp3(temp_path)
        segment = segment.speedup(playback_speed=1.1)
        combined += segment + pause

    # export final merged audio
    combined.export(output_path, format="mp3")

    # cleanup temp files
    for temp_path in temp_files:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return output_path


def generate_podcast_audio_elevenlabs(script: str, filename_prefix: str = "podcast") -> str:
    """
    Convert podcast script to two-voice MP3 using ElevenLabs.
    Alex and Sam have genuinely different voices.
    
    Args:
        script: podcast script with Alex:/Sam: format
        filename_prefix: prefix for output filename
        
    Returns:
        path to generated MP3 file
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ElevenLabs API key not found. Set ELEVENLABS_API_KEY in .env")

    from elevenlabs.client import ElevenLabs
    from elevenlabs import save

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    timestamp = int(time.time())
    output_path = f"audio/{filename_prefix}_elevenlabs_{timestamp}.mp3"
    temp_files = []

    # parse script
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
        temp_path = f"audio/temp_el_{timestamp}_{i}.mp3"
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