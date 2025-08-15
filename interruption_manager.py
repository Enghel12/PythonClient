import asyncio
import threading
from utilities import clear_previous_audio
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

            # If user interrupted mid-speech
            if interrupted:
                interrupted_speech.set()  # Set thread event to stop audio from playing
                print("🚨 MID-SPEECH INTERRUPTION DETECTED 🚨")
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


# Used to clear flags, reset buffers and do a complete clean-up during mid-speech interruptions
async def clean_up(interrupted_speech: threading.Event, audio_stopped: threading.Event, hearing_audio: asyncio.Event, audio_during_response: bytearray, sentence_queue: asyncio.Queue):
    # Detect properly when audio stopped playing using a separate thread
    await asyncio.to_thread(audio_stopped.wait)

    # 1.Clear all flags to prepare for the new conversation turn
    interrupted_speech.clear()
    audio_stopped.clear()
    hearing_audio.clear()

    # 2.Empty buffers and queues
    audio_during_response.clear()  # Clear audio recorded during mid-speech interruption
    await clear_previous_audio(sentence_queue)  # Clear the queue used to pass audio sentences
