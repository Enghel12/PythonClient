import asyncio
import threading
import httpx


# Used to send updates to the server regarding conversation
async def update_server(conversation_update: str, client_id: str):
    server_endpoint = "https://prototype.ngrok.dev/update_conversation"

    conversation = {
        "conversation_info": conversation_update,
        "id": client_id  # Return current user ID to the server
    }

    # Update server with the current conversation status
    async with httpx.AsyncClient() as client:
        response = await client.post(server_endpoint, json=conversation)


async def monitor_conversation(hearing_audio: asyncio.Event, id_queue: asyncio.Queue,
                               interrupted_speech: threading.Event):
    inform_server = False
    client_id = await id_queue.get()  # Pause until ID is ready
    AUDIO_PLAYING = "[audio_playing@@]"
    AUDIO_FINISHED = "[audio_finished@@]"

    while True:
        if interrupted_speech.is_set():
            print("Closing server updater..")
            break

        # If user starts hearing audio
        if hearing_audio.is_set() and not inform_server:
            await update_server(AUDIO_PLAYING, client_id)  # Tell server audio started playing
            inform_server = True

        # If audio response finished without user interrupting
        elif not hearing_audio.is_set() and inform_server:
            await update_server(AUDIO_FINISHED, client_id)  # Tell server audio finished
            inform_server = False

        await asyncio.sleep(0.01)  # Yield control for a bit
