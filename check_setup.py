from datetime import datetime
import ollama
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

# Approximate Pune coordinates; the date filters to species likely this week
LAT, LON = 18.52, 73.86

print("Loading BirdNET...")
analyzer = Analyzer()
rec = Recording(analyzer, "test.mp3", lat=LAT, lon=LON,
                date=datetime.now(), min_conf=0.25)
rec.analyze()
for d in rec.detections:
    print(f'{d["start_time"]:>5.1f}s  {d["common_name"]}  {d["confidence"]:.2f}')

print("\nTesting Ollama...")
r = ollama.chat(model="qwen2.5:3b",
                messages=[{"role": "user", "content": "Reply with the word OK."}])
print(r["message"]["content"])
