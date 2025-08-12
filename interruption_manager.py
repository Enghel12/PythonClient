import asyncio
import threading
from utilities import clear_previous_audio


async def reset(interrupted_speech: threading.Event, sentence_queue: asyncio.Queue, hearing_audio:asyncio.Event):
    # Clear and reset everything after a mid-speech interruption
    await clear_previous_audio(sentence_queue)
    hearing_audio.clear()
    interrupted_speech.clear()
    print("Reset successful!")


# Waits for a mid-speech interruption to take place
async def mid_speech_interruption(interrupted_speech: threading.Event, sentence_queue: asyncio.Queue, hearing_audio:asyncio.Event):

    while True:
        # If user interrupted mid-speech, reset everything once
        if interrupted_speech.is_set():
            await asyncio.sleep(0.05)  # Small pause to allow audio to stop playing
            await reset(interrupted_speech, sentence_queue, hearing_audio)

        await asyncio.sleep(0.01)  # Yield control
