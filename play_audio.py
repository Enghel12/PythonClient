import threading
import numpy as np
from pydub import AudioSegment
import io
import sounddevice as sd
import asyncio


# Used to interpret and play audio response
def play_audio(full_audio: bytes, interrupted_speech: threading.Event, audio_stopped: threading.Event):
    # Quick exit if user interrupted
    if interrupted_speech.is_set():
        audio_stopped.set()
        print("Stopping audio..")
        return

    # Decode and normalize each audio
    audio = AudioSegment.from_file(io.BytesIO(full_audio), format="mp3")
    samples = np.array(audio.get_array_of_samples(), np.float32) / 32767.0
    if audio.channels > 1:
        samples = samples.reshape(-1, audio.channels)

    # Stream audio sentence in ~1024-sample blocks
    block_size = 1024
    with sd.OutputStream(samplerate=audio.frame_rate, channels=audio.channels) as stream:
        for start in range(0, len(samples), block_size):
            # If user interrupted while A.I. was talking
            if interrupted_speech.is_set():
                audio_stopped.set()
                print("Stopping audio...")
                return  # stop current audio from playing
            stream.write(samples[start : start + block_size])


# Queues each audio sentence
async def playback_loop(sentence_queue: asyncio.Queue, hearing_audio: asyncio.Event, interrupted_speech: threading.Event, audio_stopped: threading.Event):
    sentences = []  # Stores each audio sentence from server
    loop = asyncio.get_running_loop()  # Get the event loop
    INTERRUPTED_MID_SPEECH = b"[interrupted_mid_speech@@]"


    while True:
        sentence = await sentence_queue.get()  # Wait for each audio
        print("Playback ran..")
        # If we got a new audio and user did not interrupt
        if sentence is not None:
            # If this is the start of the audio response, inform client
            if not hearing_audio.is_set():
                hearing_audio.set()

            # Launch a thread and play every audio sentence
            await loop.run_in_executor(None, play_audio, sentence, interrupted_speech, audio_stopped)


        # If user heard full audio without interrupting
        if sentence is None:
            # 2.Mark that client heard the full audio response
            if hearing_audio.is_set():
                hearing_audio.clear()

