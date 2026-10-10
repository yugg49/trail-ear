import sys
from datetime import datetime

import ollama

from trailear.identify import identify, summarize

MODEL = "qwen2.5:3b"


def build_prompt(species, place, when):
    lines = [
        f"- {s['common_name']} ({s['scientific_name']}): "
        f"heard {s['count']} times, best confidence {s['best_confidence']:.0%}"
        for s in species
    ]
    return (
        "You are a field naturalist writing in a personal birding journal.\n"
        f"Place: {place}\nDate: {when}\n"
        "Detections from today's recording:\n" + "\n".join(lines) + "\n\n"
        "Write EXACTLY 4 sentences about these detections. Sentence 1: where "
        "and when. Sentence 2: which bird dominated and how often. Sentence 3: "
        "how confident the identification is. Sentence 4: a short reflective "
        "closing line.\n"
        "Then on a new line write 'Listen for next:' followed by ONE common "
        "bird name likely near this place in this season. Use the common name "
        "only. Never write scientific names for that suggestion.\n"
        "Rules: in the 4 sentences mention ONLY the species listed above. "
        "Do not invent sightings or weather. If confidence is under 50%, say "
        "the identification is uncertain."
    )


def write_entry(species, place="Pune", model=MODEL):
    when = datetime.now().strftime("%d %B %Y, %I:%M %p")
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": build_prompt(species, place, when)}],
        options={"temperature": 0.4},
    )
    return resp["message"]["content"].strip()


if __name__ == "__main__":
    path = sys.argv[1]
    place = sys.argv[2] if len(sys.argv) > 2 else "Pune"
    species = summarize(identify(path))
    if not species:
        print("No birds detected, nothing to journal.")
    else:
        print(write_entry(species, place))
