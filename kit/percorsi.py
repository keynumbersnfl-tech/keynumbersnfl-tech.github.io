"""Anchors every script to the repository root, wherever it is launched from."""
import os
import sys

KIT = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(KIT)
if KIT not in sys.path:
    sys.path.insert(0, KIT)
os.chdir(RADICE)

DOCS = os.path.join(RADICE, "docs")
DATI = os.path.join(RADICE, "data")
os.makedirs(DOCS, exist_ok=True)
os.makedirs(os.path.join(DATI, "snapshot"), exist_ok=True)

def settimana_dir(week):
    d = os.path.join(DOCS, f"w{week:02d}")
    os.makedirs(d, exist_ok=True)
    return d
