"""Le due immagini del post del consuntivo: copertina e conteggi.
Uso: python kit/grafici_consuntivo.py [week]"""
import percorsi
import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

SFONDO = os.path.join(percorsi.RADICE, "post", "sfondo.png")
W, H = 1080, 1350
VELO = 0.46
AMBRA, GRIGIO, BIANCO, FIOCO, TRACCIA = "#F5A623", "#9A9A9A", "#F5F5F5", "#7A7A7A", "#3A3A3A"

if not os.path.exists(SFONDO):
    raise SystemExit(f"manca lo sfondo: {SFONDO}")
FONDO = Image.blend(Image.open(SFONDO).convert("RGB").resize((W, H)),
                    Image.new("RGB", (W, H), (0, 0, 0)), VELO)

def tavola():
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_alpha(0)
    fig.text(0.5, 0.055, "@keynumbersnfl", color=GRIGIO, fontsize=22, ha="center")
    return fig

def salva(fig, nome):
    t = os.path.join(percorsi.DATI, "_strato.png")
    fig.savefig(t, transparent=True)
    plt.close(fig)
    base = FONDO.convert("RGBA")
    base.alpha_composite(Image.open(t).convert("RGBA"))
    p = os.path.join(percorsi.DATI, nome)
    base.convert("RGB").save(p, quality=95)
    os.remove(t)
    print("  ", nome)
    return p

L = pd.read_csv(os.path.join(percorsi.DATI, "consuntivo.csv"))
week = int(sys.argv[1]) if len(sys.argv) > 1 else int(L.week.max())
x = L[L.week == week]
if x.empty:
    raise SystemExit(f"week {week} non presente nel registro")

def conte(df):
    a = df.ats[df.ats.isin(["fav", "dog"])]
    o = df.ou[df.ou.isin(["over", "under"])]
    v = df[df.vento_reg == 1]
    vo = v.ou[v.ou.isin(["over", "under"])]
    return {"fav": (int((a == "fav").sum()), len(a)),
            "over": (int((o == "over").sum()), len(o)),
            "casa": (int((df.margine > 0).sum()), len(df)),
            "tre": (int((df.margine.abs() == 3).sum()), len(df)),
            "vento": (int((vo == "under").sum()), len(vo))}

c, st = conte(x), conte(L)

# ---------------------------------------------------------------- SLIDE 1: copertina
BASE = {"fav": 0.491, "over": 0.496, "casa": 0.561}
TITOLI = {"fav": "Favorites covered the spread",
          "over": "Totals went over",
          "casa": "Home teams won"}
gancio, scarto = "casa", -1.0
for k, b in BASE.items():
    n, d = c[k]
    if d >= 5 and abs(n / d - b) > scarto:
        gancio, scarto = k, abs(n / d - b)
gn, gd = c[gancio]

fig = tavola()
fig.text(0.5, 0.62, f"WEEK {week}", color=BIANCO, fontsize=150,
         fontweight="bold", ha="center", va="center")
fig.text(0.5, 0.515, "H O W   I T   W E N T", color=FIOCO, fontsize=27,
         ha="center", va="center")
fig.text(0.5, 0.345, f"{TITOLI[gancio]}:", color=GRIGIO, fontsize=26, ha="center")
fig.text(0.5, 0.265, f"{gn} of {gd}", color=AMBRA, fontsize=76,
         fontweight="bold", ha="center")
salva(fig, "post_recap_1.png")

# ---------------------------------------------------------------- SLIDE 2: i conteggi
RIGHE = [("fav", "Favorites covered the spread"),
         ("over", "Totals went over"),
         ("casa", "Home teams won"),
         ("tre", "Margins landed exactly on 3"),
         ("vento", "Wind rule: finished under")]

fig = tavola()
fig.text(0.085, 0.915, f"WEEK {week}, COUNTED", color=BIANCO, fontsize=46,
         fontweight="bold", va="top")
fig.text(0.085, 0.858, f"{len(x)} GAMES", color=FIOCO, fontsize=18, va="top")

ax = fig.add_axes([0.085, 0.27, 0.86, 0.44])
ax.patch.set_alpha(0)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
ax.set_xlim(0, 1); ax.set_ylim(-0.55, len(RIGHE) - 0.35)

for i, (k, etichetta) in enumerate(RIGHE):
    yy = len(RIGHE) - 1 - i
    n, d = c[k]
    ax.text(0, yy + 0.26, etichetta, color=BIANCO, fontsize=23, va="bottom")
    if d == 0:
        ax.text(1, yy + 0.26, "no game qualified", color=GRIGIO, fontsize=21,
                va="bottom", ha="right")
        continue
    ax.text(1, yy + 0.24, f"{n} of {d}", color=AMBRA, fontsize=26,
            fontweight="bold", va="bottom", ha="right")
    ax.barh([yy], [1.0], height=0.17, color=TRACCIA, zorder=2)
    ax.barh([yy], [n / d], height=0.17, color=AMBRA, zorder=3)

sf, sd = st["fav"]; so, sod = st["over"]; sv, svd = st["vento"]
fig.text(0.085, 0.185,
         f"Season to date   -   favorites {sf} of {sd}   -   overs {so} of {sod}   -   "
         f"wind rule {sv} of {svd}",
         color=GRIGIO, fontsize=19, va="top")
salva(fig, "post_recap_2.png")
print("fatto.")

# ---------------------------------------------------------------- testo del post
vn, vd = c["vento"]
if vd:
    riga_vento = (f"Wind rule: {vn} of {vd} went under this week, {sv} of {svd} since we "
                  f"wrote the rule down. We publish that one whichever way it goes.")
else:
    riga_vento = (f"No game qualified for the wind rule this week. {sv} of {svd} since we "
                  f"wrote it down.")

testa = (f"POST DEL MARTEDI' — WEEK {week}\n\n"
         f"Carosello di due immagini, allegate qui sotto.\n"
         f"Poi la didascalia, da copiare e incollare.\n\n"
         f"Le cifre vengono dai dati: non serve ricontrollarle.")

didascalia = (f"Week {week}, counted. These are the lines we published before the games, "
              f"scored afterwards.\n\n"
              f"{TITOLI[gancio]} {gn} of {gd} this week.\n\n"
              f"{riga_vento}\n\n"
              f"Game by game in the full recap. Link in bio.")

dest = os.path.join(percorsi.DATI, "post_recap.txt")
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(f"{testa}\n@@@\n@@IMG:data/post_recap_1.png\n@@@\n"
             f"@@IMG:data/post_recap_2.png\n@@@\n{didascalia}\n")
print("Testo del post salvato:", dest)
