import os
import wave
import json
from vosk import Model, KaldiRecognizer
import pyaudio

# Load the model
model = Model("vosk-model-en-us-0.42-gigaspeech")
rec = KaldiRecognizer(model, 16000)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the microphone stream
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening...")

while True:
    data = stream.read(4000)
    out = None
    if rec.AcceptWaveform(data):
        out = json.loads(rec.Result())['text']
    else:
        out = json.loads(rec.PartialResult())['partial']

    if out == "follow":
        print("match1")
    elif out == "stop":
        print("match2")