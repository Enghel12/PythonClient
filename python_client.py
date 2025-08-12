import asyncio
import os
import threading
from dotenv import load_dotenv
from websockets.asyncio.client import connect
from handle_server_messages import start_conversation_reader, handle_id
from send_audio import send_audio
from record_audio import AudioRecorder
from play_audio import playback_loop
from update_server import monitor_conversation
from interruption_checker import handle_interruptions
from interruption_manager import mid_speech_interruption

load_dotenv()
token = os.getenv("CLIENT_TOKEN")
headers = {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────────────────────
# 📝 TO DO LIST — THE QUEST FOR FUNCTIONAL GRACE AND SYNCHRONY
# ──────────────────────────────────────────────────────────────────────────────
# 1. ✨ Use threading event to make sure audio stops from playing
#    before starting the mid-speech interruption logic
#
# 2. 🛑 Make sure playback always stops during mid-speech interruption
#    and that it can later start again cleanly
# ──────────────────────────────────────────────────────────────────────────────


async def client():
    server_url = "wss://prototype.ngrok.dev/audio"
    sentence_queue = asyncio.Queue()  # Stores each audio response from server
    hearing_audio = asyncio.Event()  # Tracks whether user hears audio or not
    id_queue = asyncio.Queue()  # Used to pass client ID around

    audio_during_response = bytearray()  # Stores user audio while A.I. is responding
    interrupted_speech = threading.Event()  # Stops current audio response if user interrupts
    client_id = ""  # Saved client ID for the duration of current session

    async with connect(server_url, additional_headers=headers) as ws:
        print(f"Connected to {server_url}")
        client_id = await handle_id(ws, id_queue)  # Get client ID
        recorder = AudioRecorder()  # Used to read and return user audio

        # Start non-interruptible tasks
        send_task = asyncio.create_task(send_audio(ws,recorder.get_audio_chunks(),audio_during_response,hearing_audio,interrupted_speech))
        mid_speech_task = asyncio.create_task(mid_speech_interruption(interrupted_speech,sentence_queue,hearing_audio))

        with recorder.start_stream():
            print("Recording... Press Ctrl+C to stop.")

            try:
                while True:
                    print("Interruptible coroutines started..")
                    # Start all interruptible tasks
                    start_conversation_task = asyncio.create_task(start_conversation_reader(ws, sentence_queue, hearing_audio))
                    monitor_task = asyncio.create_task(monitor_conversation(hearing_audio, id_queue, interrupted_speech))
                    interruption_task = asyncio.create_task(handle_interruptions(hearing_audio, interrupted_speech, audio_during_response))
                    playback_task = asyncio.create_task(playback_loop(sentence_queue, hearing_audio, interrupted_speech))

                    # Await the 4 interruptible tasks until they all exit due to a mid-speech interruption
                    await asyncio.gather(start_conversation_task,monitor_task,interruption_task,playback_task)

            except KeyboardInterrupt:
                print("Streaming stopped by user.")



if __name__ == "__main__":
    asyncio.run(client())
