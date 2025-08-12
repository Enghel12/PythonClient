import asyncio
import json
from asyncio import QueueEmpty


# Handle incoming JSON from the server
def handle_json(current_json):
    try:
        return json.loads(current_json)  # Parse and return the JSON as dictionary
    except json.JSONDecodeError:
        print("Invalid JSON format")
        return None


# Clears previous audio from server in case the user talks before hearing a response
async def clear_previous_audio(audio_queue: asyncio.Queue):
    while True:
        try:
            audio_garbage = audio_queue.get_nowait()  # Try to get an item
        except QueueEmpty:
            break

