import asyncio
from utilities import handle_json, clear_previous_audio


async def handle_id(ws):
    server_response = await ws.recv()  # Get first server message (client ID)
    data = handle_json(server_response)  # Parse JSON
    client_id = data.get("session_id")  # Get client ID
    print(f"ID: {client_id}")  # Make sure first message is client ID
    return client_id


# Used to receive conversation-related messages coming from server
async def conversation_reader(ws, sentence_queue: asyncio.Queue, audio_buffer: bytearray, hearing_audio: asyncio.Event):
    PLAY_SENTENCE = b"[play_sentence@@]"
    FULL_AUDIO    = b"[full_audio@@]"
    INTERRUPT_EARLY = b"[interrupted_early@@]"
    INTERRUPTED_MID_SPEECH = b"[interrupted_mid_speech@@]"

    print("conversation_reader: START")

    try:
        while True:
            # Cancellation-safe recv
            message = await asyncio.wait_for(ws.recv(), None)

            if message == INTERRUPT_EARLY and not hearing_audio.is_set():
                await clear_previous_audio(sentence_queue)
                print("Conversation_reader: Early interrupt, EXITING..")
                return

            if message == PLAY_SENTENCE:
                await sentence_queue.put(bytes(audio_buffer))
                audio_buffer.clear()

            elif message == FULL_AUDIO:
                await sentence_queue.put(None)
                return

            else:
                audio_buffer.extend(message)

    except asyncio.CancelledError:
        print("💤 Conversation_reader: CANCELLED 💤")
        raise
    finally:
        audio_buffer.clear()
        print("Conversation_reader: STOP")


async def start_conversation_reader(ws, sentence_queue: asyncio.Queue, hearing_audio: asyncio.Event):
    START_OF_CONVERSATION = b"[starting_conversation@@]"

    try:
        while True:
            msg = await ws.recv()

            if msg == START_OF_CONVERSATION:
                print("🗣️ Conversation turn changed:")
                await clear_previous_audio(sentence_queue)
                audio_buffer = bytearray()

                # Create the coroutine object to represent the inner task
                inner = conversation_reader(ws, sentence_queue, audio_buffer, hearing_audio)

                try:
                    await inner
                finally:
                    # Close the inner coroutine during cancellation
                    inner.close()

    except asyncio.CancelledError:
        print("1.Start conversation reader was cancelled..")
        raise
