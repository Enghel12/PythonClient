import torch
import numpy as np
import threading
import asyncio


# Load Silero VAD from torch.hub
silero_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad')
(get_speech_timestamps, _, read_audio, _, _) = utils


def perform_vad(audio_buffer: bytes, sample_rate):
    # Covert the byte string to a numpy array, float 32 for each audio sample
    numpy_16 = np.frombuffer(audio_buffer, np.int16)
    numpy_float_32 = numpy_16.astype(np.float32) / 32768.0

    # Run Silero VAD synchronously on the separate thread
    speech_timestamps = get_speech_timestamps(numpy_float_32, silero_model, sampling_rate=sample_rate)

    # Return true if here is speech detected, false otherwise
    return bool(speech_timestamps)


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
                print("Closing interruption checker..")
                break
                