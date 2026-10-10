import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

# Approximate Pune coordinates
LAT, LON = 18.52, 73.86

_analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = Analyzer()
    return _analyzer


def identify(path, lat=LAT, lon=LON, date=None, min_conf=0.25):
    """Run BirdNET on an audio file and return raw detections."""
    rec = Recording(get_analyzer(), path, lat=lat, lon=lon,
                    date=date or datetime.now(), min_conf=min_conf)
    rec.analyze()
    return rec.detections


def summarize(detections):
    """Collapse repeated detections into one row per species."""
    species = {}
    for d in detections:
        s = species.setdefault(d["common_name"], {
            "common_name": d["common_name"],
            "scientific_name": d["scientific_name"],
            "count": 0,
            "best_confidence": 0.0,
            "first_seen_s": d["start_time"],
        })
        s["count"] += 1
        s["best_confidence"] = max(s["best_confidence"], d["confidence"])
        s["first_seen_s"] = min(s["first_seen_s"], d["start_time"])
    return sorted(species.values(), key=lambda x: -x["best_confidence"])


if __name__ == "__main__":
    path = sys.argv[1]
    results = summarize(identify(path))
    if not results:
        print("No birds detected. Try a clearer clip or a lower min_conf.")
    for r in results:
        print(f'{r["common_name"]} ({r["scientific_name"]}): '
              f'{r["count"]} detections, best {r["best_confidence"]:.2f}, '
              f'first at {r["first_seen_s"]:.0f}s')
