"""Game day update: today's games only, in Eastern Time.
Latest forecast, current lines with the move since the report, injury report.
Run on each day games are played: Thursday, Sunday, Monday."""
import percorsi  # ancora i percorsi alla radice del progetto
import glob
import html
import os
import sys
import numpy as np
import pandas as pd
import requests
import nflreadpy as nfl
from motore import dec_am
from stadi import COORD

STAGIONE = 2026
ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Report Football")
FORECAST = "https://api.open-meteo.com/v1/forecast"
RETRATTILI = {"ARI", "ATL", "DAL", "HOU", "IND"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ANT = pd.read_csv("data/anticipo_meteo.csv") if os.path.exists("data/anticipo_meteo.csv") else None
e = html.escape

adesso = pd.Timestamp.now(tz="Europe/Rome").tz_convert("America/New_York")
oggi = adesso.date()

sch = nfl.load_schedules([STAGIONE]).to_pandas()
g = sch[sch.game_type == "REG"].copy()
g["kick"] = pd.to_datetime(g.gameday + " " + g.gametime).dt.tz_localize("America/New_York")
g = g[g.kick.dt.date == oggi].sort_values("kick").reset_index(drop=True)
if g.empty:
    print(f"No games today ({oggi:%b %d}, Eastern Time). Nothing to publish.")
    sys.exit(0)
week = int(g.week.iloc[0])
print(f"{len(g)} game(s) today, week {week}")

foto = sorted(glob.glob(f"data/snapshot/{STAGIONE}_w{week:02d}_*.parquet"))
base = pd.read_parquet(foto[0]).set_index("game_id") if foto else None
_f = pd.Timestamp(base.fotografia.iloc[0]) if base is not None else None
quando_base = (None if _f is None else
               (_f.tz_localize("UTC") if _f.tzinfo is None else _f).tz_convert("America/New_York"))

cache = {}
def meteo(team, kick_naive):
    if team not in cache:
        lat, lon = COORD[team]
        par = {"latitude": lat, "longitude": lon, "forecast_days": 16,
               "hourly": "wind_speed_10m,wind_gusts_10m,temperature_2m,precipitation_probability",
               "wind_speed_unit": "mph", "temperature_unit": "fahrenheit", "timezone": "America/New_York"}
        r = requests.get(FORECAST, params=par, timeout=60)
        r.raise_for_status()
        h = pd.DataFrame(r.json()["hourly"])
        h["time"] = pd.to_datetime(h["time"])
        cache[team] = h.set_index("time")
    h = cache[team]
    t0 = kick_naive.floor("h")
    b = h.loc[t0:t0 + pd.Timedelta(hours=2)]
    if b.empty:
        return (np.nan,) * 4
    return (b.wind_speed_10m.mean(), b.wind_gusts_10m.max(),
            b.temperature_2m.mean(), b.precipitation_probability.max())

def incertezza(ore):
    if ANT is None or ore <= 0:
        return None
    r = ANT.iloc[(ANT.giorni - ore / 24).abs().argmin()]
    return float(r.errore_tipico)

try:
    inj = nfl.load_injuries([STAGIONE]).to_pandas()
    disponibili = sorted(inj.week.unique())
    w_inj = week if week in disponibili else (max(disponibili) if disponibili else None)
    inj = inj[inj.week == w_inj].copy() if w_inj else inj.iloc[0:0]
    for c in ["report_status", "report_primary_injury", "practice_primary_injury",
              "practice_status", "position", "full_name"]:
        if c not in inj.columns:
            inj[c] = None
    nota_inj = ("" if w_inj == week else
                f" Showing week {w_inj}: week {week}'s report is not out yet.")
except Exception as ex:
    print("Injury report unavailable:", ex)
    inj = pd.DataFrame()
    nota_inj = ""

def primo_valido(*valori):
    for x in valori:
        if pd.notna(x) and str(x).strip() not in ('', 'nan', 'None'):
            return str(x).strip()
    return ''

RILEVANTI = {"Out", "Doubtful", "Questionable"}
def infortuni(team):
    if inj.empty:
        return "<p class='nota'>Injury report unavailable.</p>"
    saltato = inj.practice_status.astype(str).str.startswith("Did Not")
    x = inj[(inj.team == team) & (inj.report_status.isin(RILEVANTI) | saltato)]
    if x.empty:
        return f"<p class='nota'>{e(team)}: nobody on the injury report.{nota_inj}</p>"
    x = x.assign(ord=x.position.ne("QB")).sort_values(["ord", "report_status"])
    righe = "".join(
        f"<tr><td>{e(str(r.position))}</td><td>{e(str(r.full_name))}</td>"
        f"<td>{e(str(r.report_status) if pd.notna(r.report_status) else 'did not practice')}</td>"
        f"<td>{e(primo_valido(r.report_primary_injury, r.practice_primary_injury))}</td></tr>"
        for r in x.head(8).itertuples())
    qb = " <b>QB on the report.</b>" if (x.position == "QB").any() else ""
    return (f"<p class='nota'>{e(team)}{qb}{nota_inj}</p><div class='wrap'><table>"
            f"<tr><th>Pos</th><th>Player</th><th>Status</th><th>Injury</th></tr>{righe}</table></div>")

def delta(ora, prima, suffisso=""):
    if base is None or pd.isna(ora) or pd.isna(prima) or ora == prima:
        return ""
    return f" <span class='delta'>({ora - prima:+g}{suffisso})</span>"

sezioni = []
for _, r in g.iterrows():
    ore = (r.kick - adesso).total_seconds() / 3600
    manca = "under way" if ore < 0 else (f"in {ore:.0f} hours" if ore < 36 else f"in {ore / 24:.0f} days")
    b = base.loc[r.game_id] if (base is not None and r.game_id in base.index) else None
    coperto = r.roof in ("dome", "closed")
    neutro = r.location == "Neutral"
    aperto = (r.roof in ("outdoors", "open") or (pd.isna(r.roof) and r.home_team in RETRATTILI)) and not neutro

    if neutro:
        met = f"{e(str(r.stadium))}: neutral site."
    elif coperto:
        met = f"{e(str(r.stadium))}: indoors."
    elif not aperto or r.home_team not in COORD:
        met = f"{e(str(r.stadium))}: forecast unavailable."
    else:
        try:
            v, raf, tmp, pio = meteo(r.home_team, pd.to_datetime(f"{r.gameday} {r.gametime}"))
        except Exception as ex:
            print(f"  weather failed for {r.home_team}: {ex!r}")
            v = np.nan
        if pd.isna(v):
            met = f"{e(str(r.stadium))}: forecast unavailable."
        else:
            inc = incertezza(ore)
            met = f"{e(str(r.stadium))}: wind <b>{v:.1f} mph</b>"
            if inc and ore > 3:
                met += f", between {max(v - inc, 0):.0f} and {v + inc:.0f}"
            met += f" (gusts {raf:.0f}), {tmp:.0f}&deg;F, rain {pio:.0f}%"
            if b is not None and pd.notna(b.get("vento_prev")):
                met += delta(round(v, 1), round(float(b.vento_prev), 1), " mph since the report")
            met += "."
            if r.roof == "open" or pd.isna(r.roof):
                met += " Retractable roof: the call is made on game day."

    s, t = r.spread_line, r.total_line
    if pd.isna(s):
        linea = "Spread not posted."
    else:
        fav = f"{r.home_team} -{s:g}" if s > 0 else (f"{r.away_team} -{-s:g}" if s < 0 else "pick'em")
        linea = f"Spread <b>{fav}</b>" + (delta(s, b.spread_line) if b is not None else "")
    if pd.notna(t):
        linea += f" &nbsp;&middot;&nbsp; Total <b>{t:g}</b>" + (delta(t, b.total_line) if b is not None else "")
    if pd.notna(r.home_moneyline):
        linea += (f" &nbsp;&middot;&nbsp; Moneyline {e(r.away_team)} {dec_am(r.away_moneyline):.2f} / "
                  f"{e(r.home_team)} {dec_am(r.home_moneyline):.2f}")

    ora_txt = r.kick.strftime("%I:%M %p").lstrip("0")
    sezioni.append(
        f"<div class='p'><h3>{ora_txt} ET &middot; {e(r.away_team)} at {e(r.home_team)}"
        f" <span class='nota'>({manca})</span></h3>"
        f"<p>{met}</p><p>{linea}</p>{infortuni(r.away_team)}{infortuni(r.home_team)}</div>")

CSS = """
body{font-family:-apple-system,Helvetica,Arial,sans-serif;background:#fff;color:#111;margin:0;padding:12px 16px;font-size:15px;line-height:1.4}
h1{font-size:20px;margin:6px 0} h3{font-size:16px;margin:0 0 6px}
.p{border-top:1px solid #ddd;padding:12px 0}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 8px}
td,th{border-bottom:1px solid #d6d6d6;padding:4px 5px;text-align:left} th{font-weight:600}
.nota{font-size:12px;color:#555} .delta{color:#b00020;font-size:13px}
"""
cambiato = (f"In red, what moved since the report published {quando_base:%b %d, %I:%M %p} ET."
            if quando_base is not None else "")
pagina = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Game day {oggi:%b %d}</title>
<style>{CSS}</style></head><body>
<h1>Game day &middot; {DAYS[adesso.weekday()]} {oggi:%b %d} &middot; Week {week}</h1>
<p class="nota">Updated {adesso:%I:%M %p} ET. Today's games only. {cambiato}
<a href="/guide.html">How to read this</a></p>
{''.join(sezioni)}
</body></html>"""

dest = os.path.join(percorsi.settimana_dir(week), f"update-{oggi:%Y%m%d}.html")
with open(dest, "w", encoding="utf-8") as f:
    f.write(pagina)
print("Saved to:", dest)
