import asyncio
from utilities import handle_json, clear_previous_audio


async def handle_id(ws, id_queue: asyncio.Queue):
    server_response = await ws.recv()  # Get first server message (client ID)
    data = handle_json(server_response)  # Parse JSON
    client_id = data.get("session_id")  # Get client ID
    print(f"ID: {client_id}")  # Make sure first message is client ID
    await id_queue.put(client_id)  # Place ID in queue
    return client_id


# Used to receive conversation-related messages coming from server
async def conversation_reader(ws, sentence_queue: asyncio.Queue, audio_buffer: bytearray, hearing_audio: asyncio.Event):
    PLAY_SENTENCE = b"[play_sentence@@]"
    FULL_AUDIO    = b"[full_audio@@]"
    INTERRUPT_EARLY = b"[interrupted_early@@]"
    INTERRUPTED_MID_SPEECH = b"[interrupted_mid_speech@@]"

    while True:
        message = await ws.recv()  # Get each server message

        # If user talked before hearing the audio response
        if message == INTERRUPT_EARLY and not hearing_audio.is_set():
            await clear_previous_audio(sentence_queue)
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

    try:
        while True:
            msg = await ws.recv()  # cancellable await
            if msg == START_OF_CONVERSATION:
                print("New conversation turn!")
                await clear_previous_audio(sentence_queue)
                audio_buffer = bytearray()

                # Create the coroutine object to represent the inner task
                inner = conversation_reader(ws, sentence_queue, audio_buffer, hearing_audio)

                try:
                    await inner
                finally:
                    # If this coroutine is cancelled while awaiting, explicitly close out the inner coroutine.
                    if not inner.cr_await is None:
                        inner.close()
                        print("Conversation_reader was forcibly closed by start_conversation_reader")

    except asyncio.CancelledError:
        print("2.Start conversation reader was cancelled..")
        raise
