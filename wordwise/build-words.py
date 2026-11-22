#!/usr/bin/env python3
"""Convert words.csv to words.json. Run from anywhere: python3 wordwise/build-words.py

Schema per card: { id, word, category, level (1-3), associations: [5 strings] }
After changing words.json, bump CACHE in sw.js so installed apps refresh.
"""
import csv
import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
cards = []
seen = set()
with open(here / "words.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cid = row["id"].strip()
        if cid in seen:
            raise SystemExit("duplicate id: " + cid)
        seen.add(cid)
        level = int(row["level"])
        if level not in (1, 2, 3):
            raise SystemExit("bad level for " + cid)
        cards.append({
            "id": cid,
            "word": row["word"],
            "category": row["category"],
            "level": level,
            "associations": [row["clue%d" % i] for i in range(1, 6)],
        })

with open(here / "words.json", "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("wrote %d cards" % len(cards))
