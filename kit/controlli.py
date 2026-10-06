"""Safety checks before anything gets published. Exits non-zero if the data looks wrong."""
import glob
import os
import sys
import percorsi
import pandas as pd

errori = []

foto = sorted(glob.glob(os.path.join(percorsi.DATI, "snapshot", "*.parquet")))
if not foto:
    errori.append("no snapshot found")
else:
    w = pd.read_parquet(foto[-1])
    if len(w) < 10:
        errori.append(f"only {len(w)} games in the snapshot")
    if w.spread_line.notna().mean() < 0.8:
        errori.append(f"spread missing on {(1 - w.spread_line.notna().mean()) * 100:.0f}% of games")
    if w.total_line.notna().mean() < 0.8:
        errori.append(f"total missing on {(1 - w.total_line.notna().mean()) * 100:.0f}% of games")

settimane = sorted(glob.glob(os.path.join(percorsi.DOCS, "w[0-9][0-9]")))
if not settimane:
    errori.append("no week folder in docs/")
else:
    rep = os.path.join(settimane[-1], "report.html")
    if not os.path.exists(rep):
        errori.append("report.html missing")
    elif os.path.getsize(rep) < 20000:
        errori.append(f"report.html suspiciously small ({os.path.getsize(rep)} bytes)")

if errori:
    print("CHECKS FAILED:")
    for x in errori:
        print(" -", x)
    sys.exit(1)
print("All checks passed.")
