import asyncio
import threading
from utilities import clear_previous_audio
import contextlib
from perform_vad import perform_vad


# Detects if the user is rude and interrupts A.I. mid-sentence
async def handle_interruptions(hearing_audio: asyncio.Event, interrupted_speech: threading.Event, audio_during_response: bytearray):
    sample_rate = 16000
    loop = asyncio.get_running_loop()

    while True:
        await asyncio.sleep(0.3)  # Look for interruptions every 300 ms

        # If A.I. is talking to the user, look for mid-speech interruptions
        if hearing_audio.is_set() and not interrupted_speech.is_set():
            interrupted = await loop.run_in_executor(None, perform_vad, bytes(audio_during_response), sample_rate)

            if interrupted:
                audio_during_response.clear()  # Clear audio recorded during mid-speech interruption
                interrupted_speech.set()  # Set thread event to stop audio from playing
                print("1.Interruption checker is closing itself..")
                break


# Used to externally cancel all coroutines during mid-speech interruptions
async def nuke_all(*tasks: asyncio.Task):

    # For each task passed
    for task in tasks:
        task.cancel()  # Cancel the current task

        try:
            await task
        except asyncio.CancelledError:
            pass
