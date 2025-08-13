import asyncio
import threading
from utilities import clear_previous_audio
import contextlib

async def reset(interrupted_speech: threading.Event, sentence_queue: asyncio.Queue, hearing_audio:asyncio.Event):
    # Clear and reset everything after a mid-speech interruption
    await clear_previous_audio(sentence_queue)
    hearing_audio.clear()
    interrupted_speech.clear()
    print("Reset successful!")


# Waits for a mid-speech interruption to take place
async def mid_speech_interruption(interrupted_speech: threading.Event, sentence_queue: asyncio.Queue, hearing_audio:asyncio.Event, audio_stopped: threading.Event):

    while True:
        # If user interrupted mid-speech
        if interrupted_speech.is_set():
            await asyncio.to_thread(audio_stopped.wait)  # Wait until audio completely stops
            await reset(interrupted_speech, sentence_queue, hearing_audio)  # Reset flags

        await asyncio.sleep(0.01)  # Yield control every 1 ms


# Used to forcefully stop Playback during a mid-speech interruption
async def kill_playback(interrupted_speech: threading.Event, playback_task: asyncio.Task):
    # Wait until user interrupts mid-speech
    await asyncio.to_thread(interrupted_speech.wait)

    # Nuke playback because it does not play nice
    playback_task.cancel()
    print("Playback got nuked!")

    # Let it process cancellation & cleanup
    with contextlib.suppress(asyncio.CancelledError):
        await playback_task
