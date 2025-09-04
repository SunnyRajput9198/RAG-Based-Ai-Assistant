import whisper
import json
model = whisper.load_model("large-v2")

result=model.transcribe(audio="audios/41_Exercise 6 - Navbar using Flexbox.mp3", language="en", task="translate")
print(result["text"])
with open("result.json", "w") as f:
    json.dump(result, f)