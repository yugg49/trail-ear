import argparse
import csv
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

REC_DIR = Path.home() / ".trailear" / "recordings"
SAMPLE_RATE = 48000  # BirdNET's native rate


def record_audio(minutes):
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    REC_DIR.mkdir(parents=True, exist_ok=True)
    path = REC_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.wav"
    total = int(minutes * 60)
    chunks = []
    print(f"Recording for {minutes} min. Press Ctrl+C to stop early.")
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32") as stream:
            for sec in range(total):
                data, _ = stream.read(SAMPLE_RATE)
                chunks.append(data)
                print(f"\r  {sec + 1}/{total}s", end="", flush=True)
    except KeyboardInterrupt:
        pass
    print()
    if not chunks:
        return None
    sf.write(path, np.concatenate(chunks), SAMPLE_RATE)
    print(f"Saved {path}")
    return path


def process(path, place):
    from trailear.identify import identify, summarize
    from trailear.journal import write_entry
    from trailear.db import save_session

    print("Identifying birds...")
    species = summarize(identify(str(path)))
    if not species:
        print("No birds detected. Try a longer or clearer recording.")
        return
    print("Writing journal entry...")
    entry = write_entry(species, place)
    sid = save_session(place, species, entry)
    print(f"\n--- Session {sid}: {place} ---")
    for s in species:
        print(f"  {s['common_name']}: {s['count']}x, best {s['best_confidence']:.0%}")
    print(f"\n{entry}\n")


def show_journal(n):
    from trailear.db import connect

    conn = connect()
    rows = conn.execute(
        "SELECT id, date, place, journal_text FROM sessions "
        "ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    conn.close()
    if not rows:
        print("No sessions yet. Try: trailear record --minutes 2")
    for sid, date, place, text in rows:
        print(f"--- #{sid} | {date.replace('T', ' ')} | {place} ---\n{text}\n")


def show_lifelist(csv_path, min_conf):
    from trailear.db import life_list

    rows = life_list(min_conf)
    if not rows:
        print("Life list is empty.")
        return
    print(f"Life list: {len(rows)} species (confidence {min_conf:.0%}+)")
    for name, sci, first, total, best in rows:
        print(f"  {name} ({sci}) - first {first[:10]}, "
              f"{total} detections, best {best:.0%}")
    if csv_path:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["species", "scientific_name", "first_seen",
                        "detections", "best_confidence"])
            w.writerows(rows)
        print(f"Exported to {csv_path}")


def main():
    p = argparse.ArgumentParser(prog="trailear",
                                description="Offline birding companion")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="record from the mic and journal it")
    r.add_argument("--minutes", type=float, default=5)
    r.add_argument("--place", default="Pune")

    a = sub.add_parser("analyze", help="journal an existing audio file")
    a.add_argument("file")
    a.add_argument("--place", default="Pune")

    j = sub.add_parser("journal", help="show recent journal entries")
    j.add_argument("-n", type=int, default=3)

    l = sub.add_parser("lifelist", help="show every species you've recorded")
    l.add_argument("--csv", help="export to a CSV file")
    l.add_argument("--min-conf", type=float, default=0.5)

    args = p.parse_args()
    if args.cmd == "record":
        path = record_audio(args.minutes)
        if path:
            process(path, args.place)
    elif args.cmd == "analyze":
        process(args.file, args.place)
    elif args.cmd == "journal":
        show_journal(args.n)
    elif args.cmd == "lifelist":
        show_lifelist(args.csv, args.min_conf)
