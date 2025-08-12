import asyncio
import threading


async def send_audio(ws, audio_chunk_generator, audio_during_response: bytearray, hearing_audio: asyncio.Event, interrupted_speech: threading.Event):

    # Get each audio chunk from the async generator
    async for chunk in audio_chunk_generator:
        await ws.send(chunk)  # Send each audio chunk to server

        # Store audio while A.I. is talking to the user
        if hearing_audio.is_set() and not interrupted_speech.is_set():
            audio_during_response.extend(chunk)  # Track user audio while A.I. is responding


