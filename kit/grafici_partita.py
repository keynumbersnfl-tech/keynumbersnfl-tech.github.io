"""Le due immagini del post della partita della settimana.
Legge data/post_partita.json, scritto da report.py.
Uso: python kit/grafici_partita.py"""
import percorsi
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

SFONDO = os.path.join(percorsi.RADICE, "post", "sfondo.png")
DATI = os.path.join(percorsi.DATI, "post_partita.json")
W, H = 1080, 1350
VELO = 0.46
AMBRA, GRIGIO, BIANCO, FIOCO, TRACCIA = "#F5A623", "#9A9A9A", "#F5F5F5", "#7A7A7A", "#3A3A3A"

if not os.path.exists(DATI):
    raise SystemExit("manca post_partita.json: lancia prima report.py")
if not os.path.exists(SFONDO):
    raise SystemExit(f"manca lo sfondo: {SFONDO}")

d = json.load(open(DATI, encoding="utf-8"))
FONDO = Image.blend(Image.open(SFONDO).convert("RGB").resize((W, H)),
                    Image.new("RGB", (W, H), (0, 0, 0)), VELO)

def tavola():
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_alpha(0)
    fig.text(0.5, 0.055, "@keynumbersnfl", color=GRIGIO, fontsize=22, ha="center")
    return fig

def adatta(fig, testo, x, y, colore, dim, larghezza, **kw):
    t = fig.text(x, y, testo, color=colore, fontsize=dim, fontweight="bold", **kw)
    fig.canvas.draw()
    while dim > 24 and t.get_window_extent(fig.canvas.get_renderer()).width / W > larghezza:
        dim -= 3
        t.set_fontsize(dim)
        fig.canvas.draw()
    return t

def salva(fig, nome):
    t = os.path.join(percorsi.DATI, "_strato.png")
    fig.savefig(t, transparent=True)
    plt.close(fig)
    base = FONDO.convert("RGBA")
    base.alpha_composite(Image.open(t).convert("RGBA"))
    base.convert("RGB").save(os.path.join(percorsi.DATI, nome), quality=95)
    os.remove(t)
    print("  ", nome)

# ---------------------------------------------------------------- SLIDE 1: copertina
fig = tavola()
adatta(fig, d["titolo"], 0.5, 0.78, BIANCO, 86, 0.84, ha="center", va="center")
fig.text(0.5, 0.705, f'WEEK {d["week"]}   ·   {d["orario"].upper()}', color=FIOCO,
         fontsize=22, ha="center", va="center")
adatta(fig, d["cop_num"], 0.5, 0.46, AMBRA, 130, 0.86, ha="center", va="center")
fig.text(0.5, 0.345, d["cop_lab"], color=GRIGIO, fontsize=23, ha="center", va="center")
salva(fig, "post_partita_1.png")

# ---------------------------------------------------------------- SLIDE 2: i conteggi
righe = d["righe"]
fig = tavola()
fig.text(0.085, 0.915, "WHAT THE COUNT SAYS", color=BIANCO, fontsize=46,
         fontweight="bold", va="top")
fig.text(0.085, 0.858, f'{d["titolo"].upper()}   ·   WEEK {d["week"]}', color=FIOCO,
         fontsize=18, va="top")

alt = 0.16 * len(righe)
ax = fig.add_axes([0.085, 0.72 - alt, 0.86, alt])
ax.patch.set_alpha(0)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
ax.set_xlim(0, 1); ax.set_ylim(-0.55, len(righe) - 0.35)

for i, voce in enumerate(righe):
    etichetta, valore, frazione = voce[0], voce[1], voce[2]
    yy = len(righe) - 1 - i
    ax.text(0, yy + 0.26, etichetta, color=BIANCO, fontsize=23, va="bottom")
    ax.text(1, yy + 0.24, valore, color=AMBRA, fontsize=26, fontweight="bold",
            va="bottom", ha="right")
    if frazione is not None:
        ax.barh([yy], [1.0], height=0.17, color=TRACCIA, zorder=2)
        ax.barh([yy], [frazione], height=0.17, color=AMBRA, zorder=3)

fig.text(0.085, 0.235, f'Line: {d["linea"]}      Total: {d["totale"]}',
         color=BIANCO, fontsize=26, va="top")
fig.text(0.085, 0.165, "Published before kickoff. The full report has every game of the week.",
         color=GRIGIO, fontsize=19, va="top")
salva(fig, "post_partita_2.png")

# ---------------------------------------------------------------- testo del post
testa = (f'POST DELLA PARTITA — WEEK {d["week"]}\n\n'
         f'{d["titolo"]}, {d["orario"]}\n\n'
         f"Carosello di due immagini, allegate qui sotto.\n"
         f"Poi la didascalia, da copiare e incollare.\n\n"
         f"Le cifre vengono dai dati: non serve ricontrollarle.")

dest = os.path.join(percorsi.DATI, "post_partita.txt")
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(f"{testa}\n@@@\n@@IMG:data/post_partita_1.png\n@@@\n"
             f'@@IMG:data/post_partita_2.png\n@@@\n{d["didascalia"]}\n')
print("Testo del post salvato:", dest)
