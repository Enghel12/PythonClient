import asyncio
import queue
import sounddevice as sd

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.02
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)


class AudioRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Sounddevice status: {status}")
        self.audio_queue.put(indata.copy().tobytes())

    def start_stream(self):
        return sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            dtype='int16',
            channels=1,
            callback=self._callback
        )

    async def get_audio_chunks(self):
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, self.audio_queue.get)
            yield chunk
