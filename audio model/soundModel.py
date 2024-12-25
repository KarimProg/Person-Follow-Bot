import os
import wave
import json
from vosk import Model, KaldiRecognizer
import pyaudio

# Load the model
model = Model("./audio model/vosk-model-en-us-0.22-lgraph")
rec = KaldiRecognizer(model, 16000)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the microphone stream
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening...")

last = None
while True:
    data = stream.read(4000)
    out = None
    if rec.AcceptWaveform(data):
        out = json.loads(rec.Result())['text']
    else:
        out = json.loads(rec.PartialResult())['partial']

    sentence = out.split()
    words = ["follow", "stop"]
    for word in sentence:
        if word in words:
            out = word
            break
    if out == "follow" and last != "follow":
        print("Follow")
        with open("command.txt", "w") as f:
            f.write("follow")
        last = "follow"

    elif out == "stop" and last != "stop":
        print("Stop")
        with open("command.txt", "w") as f:
            f.write("stop")
        last = "stop"