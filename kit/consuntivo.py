"""Consuntivo del martedi': come sono andati i numeri pubblicati. Scrive docs/wNN/recap.html
Uso: python kit/consuntivo.py [week]    (senza week = ultima week finita con fotografia)"""
import percorsi
import glob
import html
import os
import sys
import pandas as pd
import nflreadpy as nfl

STAGIONE = 2026
SOGLIA_VENTO = 11.0          # regola fissata in NOTE_DATI.md: non toccare
LEDGER = os.path.join(percorsi.DATI, "consuntivo.csv")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
e = html.escape

def prima_foto(week):
    f = sorted(glob.glob(os.path.join(percorsi.DATI, "snapshot",
                                      f"{STAGIONE}_w{week:02d}_*.parquet")))
    return f[0] if f else None

def su(n, d):
    return f"{int(n)} of {int(d)}" if d else "none"

def tabella(testate, righe):
    h = '<div class="wrap"><table><tr>' + "".join(f"<th>{t}</th>" for t in testate) + "</tr>"
    for r in righe:
        h += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return h + "</table></div>"

sch = nfl.load_schedules([STAGIONE]).to_pandas()
reg = sch[sch.game_type == "REG"].copy()

if len(sys.argv) > 1:
    week = int(sys.argv[1])
else:
    fatte = [int(w) for w, g in reg.groupby("week") if g.result.notna().all()]
    con_foto = [w for w in sorted(fatte, reverse=True) if prima_foto(w)]
    if not con_foto:
        print("No completed week with a published snapshot yet."); sys.exit(0)
    week = con_foto[0]

foto = prima_foto(week)
if foto is None:
    print(f"No snapshot for week {week}."); sys.exit(0)
fin = reg[reg.week == week].copy()
if fin.result.isna().any():
    print(f"Week {week} is not finished yet "
          f"({int(fin.result.notna().sum())}/{len(fin)} final)."); sys.exit(0)

gia = os.path.join(percorsi.DOCS, f"w{week:02d}", "recap.html")
if os.path.exists(gia) and "--forza" not in sys.argv:
    print(f"Recap for week {week} already published. Nothing to do.")
    sys.exit(0)

pub = pd.read_parquet(foto)[["game_id", "spread_line", "total_line", "vento_prev"]]
d = (fin[["game_id", "week", "gameday", "home_team", "away_team",
          "home_score", "away_score", "roof", "location"]]
     .merge(pub, on="game_id", how="left")
     .sort_values("gameday").reset_index(drop=True))
d["margine"] = d.home_score - d.away_score
d["punti"] = d.home_score + d.away_score

def ats(r):
    if pd.isna(r.spread_line):
        return ""
    if r.margine == r.spread_line:
        return "push"
    if r.spread_line == 0:
        return "pick"
    vinto = (r.margine > r.spread_line) if r.spread_line > 0 else (r.margine < r.spread_line)
    return "fav" if vinto else "dog"

def ou(r):
    if pd.isna(r.total_line):
        return ""
    if r.punti == r.total_line:
        return "push"
    return "over" if r.punti > r.total_line else "under"

d["ats"] = d.apply(ats, axis=1)
d["ou"] = d.apply(ou, axis=1)
d["vento_reg"] = (d.roof.isin(["outdoors", "open"]) & (d.location != "Neutral")
                  & (d.vento_prev >= SOGLIA_VENTO))

COLONNE = ["game_id", "week", "gameday", "away_team", "home_team", "away_score", "home_score",
           "margine", "punti", "spread_line", "total_line", "vento_prev", "vento_reg", "ats", "ou"]
nuove = d[COLONNE].assign(season=STAGIONE)
nuove["vento_reg"] = nuove.vento_reg.astype(int)
if os.path.exists(LEDGER):
    vecchio = pd.read_csv(LEDGER)
    storico = pd.concat([vecchio[~vecchio.game_id.isin(nuove.game_id)], nuove], ignore_index=True)
else:
    storico = nuove.copy()
storico = storico.sort_values(["season", "week", "gameday"]).reset_index(drop=True)
storico.to_csv(LEDGER, index=False)
print(f"Registro: {len(storico)} partite ({LEDGER})")

def conteggi(x):
    a = x.ats[x.ats.isin(["fav", "dog"])]
    o = x.ou[x.ou.isin(["over", "under"])]
    v = x[x.vento_reg == 1]
    vo = v.ou[v.ou.isin(["over", "under"])]
    return {"fav": su((a == "fav").sum(), len(a)),
            "casa": su((x.margine > 0).sum(), len(x)),
            "over": su((o == "over").sum(), len(o)),
            "stretto": su((x.margine.abs() <= 3).sum(), len(x)),
            "tre": su((x.margine.abs() == 3).sum(), len(x)),
            "sette": su((x.margine.abs() == 7).sum(), len(x)),
            "vento": su((vo == "under").sum(), len(vo)),
            "vento_n": len(vo)}

c = conteggi(d)
st = conteggi(storico)

E_ATS = {"fav": "favorite", "dog": "underdog", "push": "push", "pick": "pick'em", "": "&mdash;"}
E_OU = {"over": "over", "under": "under", "push": "push", "": "&mdash;"}

def linea_txt(r):
    s = r.spread_line
    if pd.isna(s):
        return "&mdash;"
    if s > 0:
        return f"{e(r.home_team)} -{s:g}"
    if s < 0:
        return f"{e(r.away_team)} -{-s:g}"
    return "pick'em"

righe = []
for r in d.itertuples():
    g = pd.Timestamp(r.gameday)
    soffio = f" <span class='vent'>&middot; {r.vento_prev:.0f} mph</span>" if r.vento_reg else ""
    righe.append([f"{DAYS[g.weekday()]} {g.month}/{g.day}",
                  f"{e(r.away_team)} {int(r.away_score)} @ {e(r.home_team)} {int(r.home_score)}{soffio}",
                  f"{linea_txt(r)} &rarr; {E_ATS.get(r.ats, '&mdash;')}",
                  (f"{r.total_line:g} &rarr; {int(r.punti)} {E_OU.get(r.ou, '')}"
                   if pd.notna(r.total_line) else f"&mdash; &rarr; {int(r.punti)}")])

p1 = tabella(["Date", "Final", "Spread", "Total"], righe)

p2 = tabella(["", f"Week {week}", "Season to date"],
             [["Favorite covered the spread", c["fav"], st["fav"]],
              ["Home team won", c["casa"], st["casa"]],
              ["Total went over", c["over"], st["over"]],
              ["Decided by 3 points or fewer", c["stretto"], st["stretto"]],
              ["Margin landed exactly on 3", c["tre"], st["tre"]],
              ["Margin landed exactly on 7", c["sette"], st["sette"]]])

if c["vento_n"]:
    p3 = (f"<p>Games flagged windy before kickoff (forecast {SOGLIA_VENTO:g} mph or more, roof open) "
          f"that finished under the published total: <b>{c['vento']}</b> this week, "
          f"<b>{st['vento']}</b> since the registry started.</p>")
    vv = d[d.vento_reg]
    p3 += tabella(["Game", "Forecast wind", "O/U", "Points", "Result"],
                  [[f"{e(r.away_team)} at {e(r.home_team)}", f"{r.vento_prev:.0f} mph",
                    f"{r.total_line:g}" if pd.notna(r.total_line) else "&mdash;",
                    int(r.punti), E_OU.get(r.ou, "&mdash;")] for r in vv.itertuples()])
else:
    p3 = (f"<p>No game was flagged windy this week. Since the registry started, flagged games that "
          f"finished under the published total: <b>{st['vento']}</b>.</p>")
p3 += ('<p class="nota">The threshold and the direction of this rule were written down before the season '
       'started and have not been changed. Pushes are excluded from every count on this page.</p>')

CSS = """
body{font-family:-apple-system,Helvetica,Arial,sans-serif;background:#fff;color:#111;margin:0;padding:12px 16px;font-size:15px;line-height:1.35}
h1{font-size:20px;margin:6px 0} h3{font-size:15px;margin:4px 0 6px}
.oss{background:#f1f1f1;border-left:4px solid #888;padding:8px 10px;margin:8px 0;border-radius:4px}
.mod{background:#e8f0fe;border-left:4px solid #1a73e8;padding:8px 10px;margin:8px 0;border-radius:4px}
.ctl{background:#fff3e0;border-left:4px solid #f57c00;padding:8px 10px;margin:8px 0;border-radius:4px}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 8px}
td,th{border-bottom:1px solid #d6d6d6;padding:4px 5px;text-align:left;vertical-align:top} th{font-weight:600}
.nota{font-size:12px;color:#555} .vent{color:#0f6e56}
"""

def blocco(cl, tit, corpo):
    return f'<div class="{cl}"><h3>{tit}</h3>{corpo}</div>'

pagina = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NFL {STAGIONE} Week {week} recap</title>
<style>{CSS}</style></head><body>
<h1>NFL {STAGIONE} &middot; Week {week} &middot; How it went</h1>
<p class="nota">Spreads and totals below are the ones published before the games, not the closing numbers.
Final scores from nflverse.</p>
<p class="nota"><b>Grey</b> = what happened. <b>Blue</b> = the week in counts, next to the season so far.
<b>Orange</b> = the check that was written down in advance.</p>
{blocco("oss", "1 &middot; Results", p1)}
{blocco("mod", "2 &middot; The week in counts", p2)}
{blocco("ctl", "3 &middot; The wind registry", p3)}
<p class="nota" style="margin-top:18px">New to these numbers?
<a href="/guide.html">How to read the report</a></p>
</body></html>"""

dest = os.path.join(percorsi.settimana_dir(week), "recap.html")
with open(dest, "w", encoding="utf-8") as f:
    f.write(pagina)
print(f"Recap week {week}: {len(d)} games")
print(f"  favorite covered: {c['fav']}   over: {c['over']}   home won: {c['casa']}")
print(f"  windy games under: {c['vento']}")
print("Saved to:", dest)

# ------------------------------------------------ testo pronto per Instagram
def grezzi(x):
    a = x.ats[x.ats.isin(["fav", "dog"])]
    o = x.ou[x.ou.isin(["over", "under"])]
    v = x[x.vento_reg == 1]
    vo = v.ou[v.ou.isin(["over", "under"])]
    return dict(fav=int((a == "fav").sum()), fav_n=len(a),
                over=int((o == "over").sum()), over_n=len(o),
                casa=int((x.margine > 0).sum()), casa_n=len(x),
                tre=int((x.margine.abs() == 3).sum()),
                vento=int((vo == "under").sum()), vento_n=len(vo))

g, gs = grezzi(d), grezzi(storico)

testa = (f"POST DEL MARTEDI' — WEEK {week}\n\n"
         f"Messaggio 2 = prompt per ChatGPT.  Messaggio 3 = didascalia per Instagram.\n\n"
         f"CONTROLLO: sull'immagine deve esserci scritto esattamente\n"
         f"  WEEK {week}\n  HOW IT WENT\n  @keynumbersnfl")

prompt = f"""Generate an image. Size 1080x1350, vertical.

A dark, cinematic NFL stadium at dusk under floodlights, heavily darkened and desaturated so it works as a textured background rather than a photograph. Deep charcoal blacks, one warm amber light source low in the frame. No logos, no team names, no recognizable faces, no jersey numbers, no brands.

Centred, in very large bold condensed white sans-serif filling about half the image width:

WEEK {week}

Directly beneath it, small, uppercase, grey, widely letter-spaced:

HOW IT WENT

At the bottom centre, small but clearly readable:

@keynumbersnfl

Generous empty space around the text. Nothing else anywhere on the image. Render the text exactly as written, character for character."""

if g["vento_n"]:
    riga_vento = (f"Wind rule: {g['vento']} of {g['vento_n']} this week, "
                  f"{gs['vento']} of {gs['vento_n']} since we wrote it down.")
else:
    riga_vento = (f"Wind rule: no game qualified this week. "
                  f"{gs['vento']} of {gs['vento_n']} since we wrote it down.")

didascalia = f"""Week {week}, counted.

Favorites covered: {g['fav']} of {g['fav_n']}.
Totals went over: {g['over']} of {g['over_n']}.
Margins that landed exactly on 3: {g['tre']}.
Home teams won: {g['casa']} of {g['casa_n']}.

{riga_vento}

Season to date in the full recap. Link in bio."""

dest_post = os.path.join(percorsi.DATI, "post_recap.txt")
with open(dest_post, "w", encoding="utf-8") as f:
    f.write(f"{testa}\n@@@\n{prompt}\n@@@\n{didascalia}\n")
print("Testo del post salvato:", dest_post)
