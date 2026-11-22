#!/usr/bin/env python3
"""Quality checks for words.csv. Run: python3 -I wordwise/validate-words.py

Checks every row for: 5 non-empty clues, level 1-3, unique id, unique word
(case-insensitive), no clue equal to / containing the target word, no clue
contained in the target (clues of 3 characters or fewer are exempt from that
last test), no duplicate clues within a card. Also parses the file with the
csv module and checks that a write/read round trip is identical.
Exits non-zero if anything fails.
"""
import csv
import io
import pathlib
import re
import sys
import unicodedata

here = pathlib.Path(__file__).resolve().parent
COLS = ["id", "word", "category", "level", "clue1", "clue2", "clue3", "clue4", "clue5", "tags"]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def squash(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())


text = (here / "words.csv").read_text(encoding="utf-8")
rows = list(csv.reader(io.StringIO(text, newline="")))
header, body = rows[0], rows[1:]
problems = []

if header != COLS:
    problems.append("header is %r, expected %r" % (header, COLS))

ids, words = {}, {}
for n, r in enumerate(body, start=2):
    if len(r) != len(COLS):
        problems.append("line %d: %d fields, expected %d" % (n, len(r), len(COLS)))
        continue
    cid, word, cat, level = r[0], r[1], r[2], r[3]
    clues, tags = r[4:9], r[9]
    where = "%s (line %d)" % (cid, n)
    if cid in ids:
        problems.append("%s: duplicate id" % where)
    ids[cid] = n
    if cid != slug(word) + "_" + slug(cat):
        problems.append("%s: id is not slug(word_category) = %s" % (where, slug(word) + "_" + slug(cat)))
    k = word.strip().lower()
    if not k:
        problems.append("%s: empty word" % where)
    if k in words:
        problems.append("%s: word %r already used on line %d" % (where, word, words[k]))
    words[k] = n
    if not cat.strip():
        problems.append("%s: empty category" % where)
    if level not in ("1", "2", "3"):
        problems.append("%s: bad level %r" % (where, level))
    if any(not c.strip() for c in clues):
        problems.append("%s: empty clue" % where)
    seen = set()
    sw = squash(word)
    for c in clues:
        cl = c.strip().lower()
        if cl in seen:
            problems.append("%s: duplicate clue %r" % (where, c))
        seen.add(cl)
        if len(c.split()) > 2:
            problems.append("%s: clue %r is more than two words" % (where, c))
        sc = squash(c)
        if not sc:
            continue
        if cl == k or k in cl or sw in sc:
            problems.append("%s: clue %r equals or contains the word %r" % (where, c, word))
        elif len(sc) > 3 and (sc in sw or cl in k):
            problems.append("%s: clue %r is contained in the word %r" % (where, c, word))
    for t in filter(None, tags.split(";")):
        if t != t.strip() or t != t.lower() or " " in t:
            problems.append("%s: odd tag %r" % (where, t))

# Round trip through the csv module: write what we parsed, compare to the file.
out = io.StringIO()
csv.writer(out, lineterminator="\n").writerows(rows)
if out.getvalue() != text:
    problems.append("csv module rewrite differs from the file (quoting or line endings)")

cats = {}
for r in body:
    if len(r) == len(COLS):
        cats[r[2]] = cats.get(r[2], 0) + 1
print("%d cards, %d categories" % (len(body), len(cats)))
for c in sorted(cats):
    print("  %-18s %d" % (c, cats[c]))
tagged = sum(1 for r in body if len(r) == len(COLS) and "codenames" in r[9].split(";"))
multi = sum(1 for r in body if len(r) == len(COLS) and "multi_meaning" in r[9].split(";"))
print("codenames-tagged: %d (multi_meaning: %d)" % (tagged, multi))
if problems:
    print("\nFAILED, %d problem(s):" % len(problems))
    for p in problems:
        print("  - " + p)
    sys.exit(1)
print("\nAll checks passed.")
