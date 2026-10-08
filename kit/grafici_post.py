"""Grafici per i post Instagram. 1080x1350, dati veri, sfondo fisso.
Uso: python kit/grafici_post.py
Lo sfondo e le immagini prodotte stanno nella cartella iCloud dei post."""
import percorsi
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

POST = os.path.expanduser("~/Desktop/Bolle test/files/nflkit/post/immagini")
SFONDO = os.path.join(POST, "sfondo.png")
W, H = 1080, 1350
VELO = 0.46          # quanto scurire lo sfondo: 0 = originale, 1 = nero
AMBRA, GRIGIO, BIANCO, FIOCO, ASSE = "#F5A623", "#9A9A9A", "#F5F5F5", "#7A7A7A", "#3A3A3A"

if not os.path.exists(SFONDO):
    raise SystemExit(f"manca lo sfondo: {SFONDO}")
FONDO = Image.blend(Image.open(SFONDO).convert("RGB").resize((W, H)),
                    Image.new("RGB", (W, H), (0, 0, 0)), VELO)

def nuova(titolo, sotto, piede):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_alpha(0)
    dim = 46
    t = fig.text(0.085, 0.925, titolo, color=BIANCO, fontsize=dim, fontweight="bold", va="top")
    fig.canvas.draw()
    while dim > 26 and t.get_window_extent(fig.canvas.get_renderer()).width / W > 0.845:
        dim -= 2
        t.set_fontsize(dim)
        fig.canvas.draw()
    fig.text(0.085, 0.868, sotto, color=FIOCO, fontsize=18, va="top")
    fig.text(0.085, 0.150, piede, color=FIOCO, fontsize=19, va="top")
    fig.text(0.5, 0.055, "@keynumbersnfl", color=GRIGIO, fontsize=22, ha="center")
    return fig

def pulisci(ax, basso=True):
    ax.patch.set_alpha(0)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    if basso:
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(ASSE)
        ax.spines["bottom"].set_linewidth(2)
    ax.tick_params(colors=FIOCO, length=0, pad=12, labelsize=20)
    ax.set_yticks([])

def salva(fig, nome):
    t = os.path.join(POST, "_strato.png")
    fig.savefig(t, transparent=True)
    plt.close(fig)
    base = FONDO.convert("RGBA")
    base.alpha_composite(Image.open(t).convert("RGBA"))
    base.convert("RGB").save(os.path.join(POST, nome), quality=95)
    os.remove(t)
    print("  ", nome)

d = pd.read_parquet("data/schedules.parquet")
r = d[(d.game_type == "REG") & d.result.notna() & (d.season >= 2002)].copy()
r["marg"] = r.result.abs()
N = len(r)
cons = pd.read_csv(os.path.join(percorsi.DATI, "consuntivo.csv"))
print(f"campione: {N} partite")

# ---------------------------------------------------------------- POST 2 - vento
v = cons[cons.vento_reg == 1].copy()
fig = nuova("THE WIND RULE, WEEK 3",
            "FORECAST 11 MPH OR MORE, ROOF OPEN - 3 GAMES",
            "Bar = points actually scored.  Marker = the total the market set.")
ax = fig.add_axes([0.30, 0.30, 0.62, 0.42]); pulisci(ax, basso=False)
y = np.arange(len(v))[::-1]
ax.barh(y, v.punti, height=0.46, color=AMBRA, zorder=3)
for yy, (_, g) in zip(y, v.iterrows()):
    ax.plot([g.total_line, g.total_line], [yy - 0.34, yy + 0.34], color=BIANCO, lw=4, zorder=4)
    ax.text(g.punti + 1.5, yy, f"{int(g.punti)}", va="center", color=AMBRA,
            fontsize=26, fontweight="bold")
    ax.text(g.total_line, yy + 0.46, f"{g.total_line:g}", ha="center", va="bottom",
            color=BIANCO, fontsize=17)
ax.set_yticks(y)
ax.set_yticklabels([f"{a} at {h}" for a, h in zip(v.away_team, v.home_team)])
ax.tick_params(axis="y", colors=BIANCO, length=0, pad=14, labelsize=23)
ax.set_xlim(0, 78); ax.set_xticks([])
fig.text(0.085, 0.215, "All three went over.   0 of 3.", color=BIANCO,
         fontsize=30, fontweight="bold")
salva(fig, "post_02_vento.png")

# ---------------------------------------------------------------- POST 3 - il 3
m = list(range(1, 15)); c = [int((r.marg == x).sum()) for x in m]
fig = nuova("HOW NFL GAMES END",
            f"FINAL MARGIN, {N:,} REGULAR SEASON GAMES, 2002-2026",
            "Points separating the two teams at the final whistle")
ax = fig.add_axes([0.095, 0.225, 0.855, 0.495]); pulisci(ax)
ax.bar(m, c, width=0.70, color=[AMBRA if x in (3, 7) else GRIGIO for x in m], zorder=3)
for x, y2 in zip(m, c):
    if x in (3, 7):
        ax.text(x, y2 + 26, f"{y2:,}", ha="center", va="bottom", color=AMBRA,
                fontsize=27, fontweight="bold")
ax.set_xticks(m); ax.set_xticklabels([str(x) for x in m])
ax.set_ylim(0, max(c) * 1.18); ax.set_xlim(0.3, 14.7)
salva(fig, "post_03_tre.png")

# ---------------------------------------------------------------- POST 4 - il buco del 9
m2 = [8, 9, 10, 11]; c2 = [int((r.marg == x).sum()) for x in m2]
fig = nuova("THE 9 IS RARE",
            f"FINAL MARGINS OF 8 TO 11 POINTS, {N:,} GAMES",
            "A 10 is a touchdown plus a field goal.  A 9 needs an unusual path.")
ax = fig.add_axes([0.14, 0.235, 0.78, 0.47]); pulisci(ax)
ax.bar(m2, c2, width=0.56, color=[AMBRA if x == 9 else GRIGIO for x in m2], zorder=3)
for x, y2 in zip(m2, c2):
    ax.text(x, y2 + 8, f"{y2:,}", ha="center", va="bottom",
            color=AMBRA if x == 9 else BIANCO, fontsize=30, fontweight="bold")
ax.set_xticks(m2); ax.set_xticklabels([str(x) for x in m2])
ax.tick_params(axis="x", labelsize=26)
ax.set_ylim(0, max(c2) * 1.20); ax.set_xlim(7.4, 11.6)
salva(fig, "post_04_nove.png")

# ---------------------------------------------------------------- POST 5 - il favorito
s = r[r.spread_line.notna() & (r.spread_line != 0)].copy()
vv = s[s.result != s.spread_line]
cop = int((((vv.result > vv.spread_line) & (vv.spread_line > 0)) |
           ((vv.result < vv.spread_line) & (vv.spread_line < 0))).sum())
tot = len(vv); non = tot - cop
fig = nuova("A COIN FLIP, FOR 24 SEASONS",
            "FAVORITES AGAINST THE SPREAD, 2002-2026",
            f"Pushes excluded.  {tot:,} games.")
ax = fig.add_axes([0.085, 0.42, 0.855, 0.14]); pulisci(ax, basso=False)
ax.barh([0], [cop], color=AMBRA, height=1.0, zorder=3)
ax.barh([0], [non], left=[cop], color="#4A4A4A", height=1.0, zorder=3)
ax.axvline(tot / 2, color=BIANCO, lw=3, ls=(0, (6, 5)), zorder=5)
ax.set_xlim(0, tot); ax.set_ylim(-0.5, 0.5); ax.set_xticks([])
fig.text(0.085, 0.60, f"{cop / tot * 100:.1f}%", color=AMBRA, fontsize=96,
         fontweight="bold", va="bottom")
fig.text(0.085, 0.385, f"Covered  {cop:,}", color=AMBRA, fontsize=24, va="top")
fig.text(0.94, 0.385, f"Did not  {non:,}", color=GRIGIO, fontsize=24, va="top", ha="right")
fig.text(0.5, 0.345, "dashed line = exactly half", color=FIOCO, fontsize=18, ha="center")
salva(fig, "post_05_favorito.png")

# ---------------------------------------------------------------- POST 6 - mezzo punto
t3 = r[r.spread_line.abs() == 3]; p3 = int((t3.marg == 3).sum())
t35 = r[r.spread_line.abs() == 3.5]
fig = nuova("WHAT HALF A POINT BUYS",
            "HOW OFTEN THE GAME LANDS EXACTLY ON THE LINE",
            "On 3 the game can land there.  On 3.5 it never can.")
ax = fig.add_axes([0.20, 0.25, 0.66, 0.44]); pulisci(ax)
alt = p3 / len(t3) * 100
ax.bar([0], [alt], width=0.46, color=AMBRA, zorder=3)
ax.bar([1], [0.35], width=0.46, color="#4A4A4A", zorder=3)
ax.text(0, alt + 0.7, f"{p3} of {len(t3):,}", ha="center", va="bottom", color=AMBRA,
        fontsize=28, fontweight="bold")
ax.text(1, 1.1, f"0 of {len(t35):,}", ha="center", va="bottom", color=GRIGIO,
        fontsize=28, fontweight="bold")
ax.set_xticks([0, 1]); ax.set_xticklabels(["LINE  3", "LINE  3.5"])
ax.tick_params(axis="x", labelsize=26, colors=BIANCO)
ax.set_ylim(0, alt * 1.35); ax.set_xlim(-0.6, 1.6)
salva(fig, "post_06_mezzopunto.png")

# ---------------------------------------------------------------- POST 7 - campo di casa
nt = r[r.result != 0].copy()
nt["casa_vince"] = (nt.result > 0).astype(float)
per_stag = nt.groupby("season").casa_vince.mean() * 100
per_stag = per_stag[per_stag.index <= 2025]
EPOCHE = [(2002, 2010), (2011, 2019), (2020, 2025)]
fig = nuova("HOME FIELD IS SHRINKING",
            "SHARE OF GAMES WON BY THE HOME TEAM",
            "Small dots are single seasons.  Large dot is the era average.  Ties excluded.")
ax = fig.add_axes([0.085, 0.265, 0.875, 0.42]); pulisci(ax)
for i, (a, b) in enumerate(EPOCHE):
    yy = len(EPOCHE) - 1 - i
    stag = per_stag[(per_stag.index >= a) & (per_stag.index <= b)]
    ax.plot(stag.values, [yy] * len(stag), "o", ms=11, color="#5A5A5A", zorder=3)
    med = nt[nt.season.between(a, b)].casa_vince.mean() * 100
    ax.plot([med], [yy], "o", ms=30, color=AMBRA, zorder=5)
    ax.text(med, yy + 0.33, f"{med:.1f}%", ha="center", va="bottom", color=AMBRA,
            fontsize=30, fontweight="bold")
    ax.text(44.6, yy, f"{a}-{b}", ha="left", va="center", color=BIANCO, fontsize=22)
ax.set_ylim(-0.7, len(EPOCHE) - 0.25)
ax.set_xlim(44.3, 66); ax.set_xticks([50, 55, 60, 65])
ax.set_xticklabels(["50%", "55%", "60%", "65%"])
ax.axvline(50, color=ASSE, lw=2, ls=(0, (5, 5)), zorder=1)
salva(fig, "post_07_casa.png")

# ---------------------------------------------------------------- POST 8 - partite strette
soglie = list(range(1, 22))
cum = [(r.marg <= x).mean() * 100 for x in soglie]
fig = nuova("HALF THE SEASON IS ONE SCORE",
            f"SHARE OF GAMES DECIDED BY N POINTS OR FEWER, {N:,} GAMES",
            "Read it as: out of every 100 games, how many were this close.")
ax = fig.add_axes([0.115, 0.235, 0.835, 0.48]); pulisci(ax)
ax.plot(soglie, cum, color=GRIGIO, lw=4, zorder=3)
for x in (3, 7):
    y2 = cum[x - 1]
    ax.plot([x], [y2], "o", ms=16, color=AMBRA, zorder=5)
    ax.plot([x, x], [0, y2], color=AMBRA, lw=2, ls=(0, (4, 4)), zorder=2)
    if x == 3:
        ax.text(x - 0.45, y2 + 2.5, f"{y2:.0f} in 100", color=AMBRA, fontsize=27,
                fontweight="bold", va="bottom", ha="left")
    else:
        ax.text(x + 0.6, y2 - 1.0, f"{y2:.0f} in 100", color=AMBRA, fontsize=27,
                fontweight="bold", va="top", ha="left")
ax.set_xticks([1, 3, 7, 10, 14, 21]); ax.set_xticklabels(["1", "3", "7", "10", "14", "21"])
ax.set_ylim(0, max(cum) * 1.08); ax.set_xlim(0.5, 21.5)
salva(fig, "post_08_strette.png")

print("fatto.")
