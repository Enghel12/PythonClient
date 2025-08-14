import torch
import numpy as np


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



                