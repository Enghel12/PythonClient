import asyncio
import threading
from utilities import handle_json, clear_previous_audio


async def handle_id(ws, id_queue: asyncio.Queue):
    server_response = await ws.recv()  # Get first server message (client ID)
    data = handle_json(server_response)  # Parse JSON
    client_id = data.get("session_id")  # Get client ID
    print(f"ID: {client_id}")  # Make sure first message is client ID
    await id_queue.put(client_id)  # Place ID in queue
    return client_id

async def conversation_reader(ws, sentence_queue: asyncio.Queue, audio_buffer: bytearray, hearing_audio: asyncio.Event, close_conversation_reader: asyncio.Event):
    PLAY_SENTENCE = b"[play_sentence@@]"
    FULL_AUDIO    = b"[full_audio@@]"
    INTERRUPT_EARLY = b"[interrupted_early@@]"
    INTERRUPTED_MID_SPEECH = b"[interrupted_mid_speech@@]"

    while True:
        message = await ws.recv()  # Get each server message

        # If user interrupted mid-speech(very early)
        if message == INTERRUPTED_MID_SPEECH:
            await clear_previous_audio(sentence_queue)  # Clear leftover audio
            print("Closing inner message receiver..")
            close_conversation_reader.set()
            break

        # If user talked before hearing the audio response
        if message == INTERRUPT_EARLY and not hearing_audio.is_set():
            print("User interrupted early, dropping audio garbage..")
            return

        if message == PLAY_SENTENCE:
            # Send the buffered audio sentence to Playback
            await sentence_queue.put(bytes(audio_buffer))
            audio_buffer.clear()

        elif message == FULL_AUDIO:
            # Inform Playback that server finished sending audio
            await sentence_queue.put(None)
            return

        else:
            # Accumulate audio bytes to get each sentence
            audio_buffer.extend(message)


async def start_conversation_reader(ws, sentence_queue: asyncio.Queue, hearing_audio: asyncio.Event):
    START_OF_CONVERSATION = b"[starting_conversation@@]"
    INTERRUPTED_MID_SPEECH = b"[interrupted_mid_speech@@]"

    # Used to manually close conversation reader if user interrupts mid-speech
    close_conversation_reader = asyncio.Event()

    while True:
        msg = await ws.recv()
        if msg == START_OF_CONVERSATION:
            print("New conversation turn!")
            await clear_previous_audio(sentence_queue)
            audio_buffer = bytearray()

            # Start conversation reader after each turn
            await conversation_reader(ws, sentence_queue, audio_buffer, hearing_audio, close_conversation_reader)


        # If user interrupted mid-speech(mid conversation or later)
        if msg == INTERRUPTED_MID_SPEECH or close_conversation_reader.is_set():
            print("Closing outer message receiver..")  # Clear leftover audio
            break
