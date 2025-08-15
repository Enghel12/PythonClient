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
from interruption_manager import  handle_interruptions, nuke_all, clean_up

load_dotenv()
token = os.getenv("CLIENT_TOKEN")
headers = {"Authorization": f"Bearer {token}"}


async def client():
    server_url = "wss://prototype.ngrok.dev/audio"
    sentence_queue = asyncio.Queue()  # Stores each audio response from server
    hearing_audio = asyncio.Event()  # Tracks whether user hears audio or not


    audio_during_response = bytearray()  # Stores user audio while A.I. is responding
    interrupted_speech = threading.Event()  # Stops current audio response if user interrupts
    audio_stopped  = threading.Event()  # Tracks if audio is stopped during mid-speech interruption
    client_id = ""  # Saved client ID for the duration of current session


    async with connect(server_url, additional_headers=headers) as ws:
        print(f"Connected to {server_url}")
        client_id = await handle_id(ws)  # Get client ID
        recorder = AudioRecorder()  # Used to read and return user audio

        # Non-interruptible task responsible for sending continuous audio to server
        send_task = asyncio.create_task(send_audio(ws, recorder.get_audio_chunks(), audio_during_response, hearing_audio, interrupted_speech)) # Sends continuous audio to server


        with recorder.start_stream():
            print("Recording... Press Ctrl+C to stop.")

            try:
                while True:
                    print("New cycle started!")
                    # Start all interruptible tasks
                    interruption_task = asyncio.create_task(handle_interruptions(hearing_audio, interrupted_speech, audio_during_response))
                    start_conversation_task = asyncio.create_task(start_conversation_reader(ws, sentence_queue, hearing_audio))
                    monitor_task = asyncio.create_task(monitor_conversation(hearing_audio, client_id))
                    playback_task = asyncio.create_task(playback_loop(sentence_queue, hearing_audio, interrupted_speech, audio_stopped))

                    await asyncio.to_thread(interrupted_speech.wait)  # Pause here until each mid-speech interruption

                    # Kill all coroutines during mid-speech interruption
                    await nuke_all(start_conversation_task, monitor_task, playback_task)

                    # Clear all events, buffers, and everything after each interruption
                    await clean_up(interrupted_speech, audio_stopped, hearing_audio, audio_during_response, sentence_queue)

            except KeyboardInterrupt:
                print("Streaming stopped by user.")



if __name__ == "__main__":
    asyncio.run(client())
