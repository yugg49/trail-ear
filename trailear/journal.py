import sys
from datetime import datetime

import ollama

from trailear.identify import identify, summarize

MODEL = "qwen2.5:3b"

LOCAL_BIRDS = [
    "Oriental Magpie-Robin", "Common Tailorbird", "Purple Sunbird",
    "Red-vented Bulbul", "Indian Pond Heron", "Rose-ringed Parakeet",
    "White-throated Kingfisher", "Greater Coucal", "Indian Robin",
    "Spotted Dove", "Common Myna", "Black Kite", "Little Cormorant",
    "Asian Koel",
]


def build_prompt(species, place, when):
    detected = {s["common_name"] for s in species}
    candidates = [b for b in LOCAL_BIRDS if b not in detected]
    lines = [
        f"- {s['common_name']}: heard {s['count']} times, "
        f"best confidence {s['best_confidence']:.0%}"
        for s in species
    ]
    return (
        "You are a field naturalist writing in a personal birding journal.\n"
        f"Place: {place}\nDate and time: {when}\n"
        "Detections from today's recording:\n" + "\n".join(lines) + "\n\n"
        "Write one paragraph of exactly 4 sentences in plain prose. No "
        "labels, no headings, no bullet points. Cover: where and when, which "
        "bird was most frequent and how often, how confident the "
        "identification is, and a short reflective closing thought.\n"
        "Do not mention weather, sunshine, temperature, or anything that is "
        "not in the data above. Mention only the detected species. If "
        "confidence is under 50%, say the identification is uncertain.\n"
        "Then on a new line write 'Listen for next:' followed by exactly one "
        "bird from this list: " + ", ".join(candidates) + "."
    )


def write_entry(species, place="Pune", model=MODEL):
    when = datetime.now().strftime("%d %B %Y, %I:%M %p")
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": build_prompt(species, place, when)}],
        options={"temperature": 0.3},
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
