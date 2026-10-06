"""Registro della regola vento -> under. Verifica in avanti, stagione 2026.
Regola fissata in NOTE_DATI.md il 22/09/2026: partita all'aperto, non su campo neutro,
vento medio previsto nelle 3 ore dal kickoff >= 11 mph -> UNDER sul totale di chiusura.
Il file e' a sola aggiunta: la previsione e' congelata alla prima scrittura,
una riga di partita conclusa non viene piu' modificata."""
import percorsi  # ancora i percorsi alla radice del progetto
import glob
import math
import os
from datetime import datetime
import numpy as np
import pandas as pd
import requests
import nflreadpy as nfl
from stadi import COORD

STAGIONE = 2026
SOGLIA = 11.0            # NON MODIFICARE: la soglia fa parte della regola
ORE_CONGELA = 36.0       # la previsione si congela solo entro 36 ore dal kickoff
PUNTATA = 1.0            # puntata fissa
REGISTRO = "data/registro_vento.csv"
ARCHIVIO = "https://historical-forecast-api.open-meteo.com/v1/forecast"
LIVE = "https://api.open-meteo.com/v1/forecast"
COLONNE = ["game_id", "season", "week", "gameday", "kickoff_et", "away", "home", "stadium",
           "roof", "neutral", "vento_prev", "origine_prev", "ore_prima", "total_line", "under_dec",
           "punti_reali", "esito", "profitto", "regola", "stato", "nota", "scritta_il"]

def titolo(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)

def dec_am(ml):
    if pd.isna(ml):
        return np.nan
    return 1 + ml / 100 if ml > 0 else 1 + 100 / abs(ml)

adesso = pd.Timestamp.now()
adesso_et = pd.Timestamp.now(tz='Europe/Rome').tz_convert('America/New_York').tz_localize(None)
os.makedirs("data/meteo", exist_ok=True)

vecchio = pd.read_csv(REGISTRO) if os.path.exists(REGISTRO) else pd.DataFrame(columns=COLONNE)
if len(vecchio):
    vecchio['kickoff_et'] = pd.to_datetime(vecchio['kickoff_et'])
chiuse = set(vecchio.loc[vecchio.stato == "conclusa", "game_id"]) if len(vecchio) else set()
print(f"Registro esistente: {len(vecchio)} righe, di cui {len(chiuse)} gia' chiuse e intoccabili.")

# ------------------------------------------------------------ partite candidate
sch = nfl.load_schedules([STAGIONE]).to_pandas()
g = sch[sch.game_type == "REG"].copy()
g["kick_et"] = pd.to_datetime(g.gameday + " " + g.gametime)
g = g[~g.roof.isin(["dome", "closed"])]          # cupole fisse: fuori per costruzione
g = g.sort_values("kick_et").reset_index(drop=True)
print(f"Partite candidate (regular season, non in cupola fissa): {len(g)}")

# ------------------------------------------------------------ previsioni
cache = {}
def serie_archivio(team):
    """Previsione com'era allora: archivio Open-Meteo, una chiamata per stadio."""
    f = f"data/meteo/arch_{team}_{STAGIONE}.parquet"
    if os.path.exists(f):
        h = pd.read_parquet(f)
        if h.index.max() >= adesso.floor("D") - pd.Timedelta(days=1):
            return h
    lat, lon = COORD[team]
    par = {"latitude": lat, "longitude": lon, "start_date": f"{STAGIONE}-09-01",
           "end_date": adesso.strftime("%Y-%m-%d"), "hourly": "wind_speed_10m",
           "wind_speed_unit": "mph", "timezone": "America/New_York"}
    r = requests.get(ARCHIVIO, params=par, timeout=120)
    r.raise_for_status()
    h = pd.DataFrame(r.json()["hourly"])
    h["time"] = pd.to_datetime(h["time"])
    h = h.set_index("time")
    h.to_parquet(f)
    return h

def serie_live(team):
    lat, lon = COORD[team]
    par = {"latitude": lat, "longitude": lon, "forecast_days": 16, "hourly": "wind_speed_10m",
           "wind_speed_unit": "mph", "timezone": "America/New_York"}
    r = requests.get(LIVE, params=par, timeout=60)
    r.raise_for_status()
    h = pd.DataFrame(r.json()["hourly"])
    h["time"] = pd.to_datetime(h["time"])
    return h.set_index("time")

def vento(team, kick, passata):
    chiave = (team, passata)
    if chiave not in cache:
        cache[chiave] = serie_archivio(team) if passata else serie_live(team)
    h = cache[chiave]
    t0 = kick.floor("h")
    b = h.loc[t0:t0 + pd.Timedelta(hours=2), "wind_speed_10m"]
    return float(b.mean()) if len(b) and b.notna().any() else np.nan

# ------------------------------------------------------------ fotografie gia' scattate
foto = {}
for f in sorted(glob.glob(f"data/snapshot/{STAGIONE}_w*.parquet")):
    d = pd.read_parquet(f)
    for _, r in d.iterrows():
        if pd.notna(r.get("vento_prev")):
            foto.setdefault(r.game_id, []).append((pd.Timestamp(r.fotografia), r.vento_prev))

# ------------------------------------------------------------ costruzione righe
righe, nuove, aggiornate = [], 0, 0
for _, r in g.iterrows():
    if r.game_id in chiuse:
        righe.append(vecchio[vecchio.game_id == r.game_id].iloc[0].to_dict())
        continue
    prec = vecchio[vecchio.game_id == r.game_id]
    prec = prec.iloc[0] if len(prec) else None
    giocata = pd.notna(r.result)
    neutro = r.location == "Neutral"

    # previsione: si aggiorna finche' il kickoff e' lontano, si congela entro ORE_CONGELA
    ore_mancanti = (r.kick_et - adesso_et).total_seconds() / 3600
    iniziata = giocata or ore_mancanti <= 0
    gia = (prec is not None and pd.notna(prec.vento_prev)
           and pd.notna(prec.get("ore_prima", np.nan))
           and float(prec.get("ore_prima")) <= ORE_CONGELA)
    if gia:
        v, orig, op = float(prec.vento_prev), prec.origine_prev, float(prec.ore_prima)
    elif neutro or r.home_team not in COORD:
        v, orig, op = np.nan, "n.d.", np.nan
    else:
        scatti = [(t, x) for t, x in foto.get(r.game_id, []) if t <= r.kick_et]
        if scatti:
            t_s, x_s = max(scatti)
            v, orig = float(x_s), "fotografia"
            op = (r.kick_et - t_s).total_seconds() / 3600
        else:
            try:
                v = vento(r.home_team, r.kick_et, iniziata)
                orig = "archivio" if iniziata else "live"
                op = -1.0 if iniziata else ore_mancanti
            except Exception as ex:
                print(f"  meteo non disponibile {r.game_id}: {ex!r}")
                v, orig, op = np.nan, "n.d.", np.nan

    ud = dec_am(r.under_odds)
    regola = bool(pd.notna(v) and v >= SOGLIA and not neutro and r.roof in ("outdoors", "open"))
    if neutro:
        stato, nota = ("conclusa" if giocata else "in attesa"), "campo neutro: fuori dal conteggio"
    elif pd.isna(v):
        stato, nota = ("conclusa" if giocata else "in attesa"), "previsione mancante: non valutabile"
    elif not giocata:
        stato = "in attesa"
        nota = "tetto da confermare" if pd.isna(r.roof) else ""
    else:
        stato = "conclusa"
        nota = "tetto chiuso: fuori dal conteggio" if r.roof not in ("outdoors", "open") else ""

    if giocata and pd.notna(r.total_line):
        esito = "over" if r.total > r.total_line else ("under" if r.total < r.total_line else "push")
        prof = 0.0 if esito == "push" else (PUNTATA * (ud - 1) if esito == "under" else -PUNTATA)
        prof = prof if (regola and pd.notna(ud)) else np.nan
    else:
        esito, prof = "", np.nan

    righe.append({"game_id": r.game_id, "season": r.season, "week": r.week, "gameday": r.gameday,
                  "kickoff_et": r.kick_et, "away": r.away_team, "home": r.home_team,
                  "stadium": r.stadium, "roof": r.roof, "neutral": neutro,
                  "vento_prev": None if pd.isna(v) else round(v, 1), "origine_prev": orig,
                  "ore_prima": None if pd.isna(op) else round(op, 1),
                  "total_line": r.total_line, "under_dec": None if pd.isna(ud) else round(ud, 3),
                  "punti_reali": r.total if giocata else None, "esito": esito,
                  "profitto": None if pd.isna(prof) else round(prof, 3), "regola": regola,
                  "stato": stato, "nota": nota,
                  "scritta_il": prec.scritta_il if prec is not None else adesso.strftime("%Y-%m-%d %H:%M")})
    nuove += prec is None
    aggiornate += prec is not None

reg = pd.DataFrame(righe)[COLONNE]
reg["kickoff_et"] = pd.to_datetime(reg["kickoff_et"])
reg = reg.sort_values("kickoff_et")
reg.to_csv(REGISTRO, index=False)
print(f"Righe nuove: {nuove}   aggiornate: {aggiornate}   intoccate: {len(chiuse)}")

# ------------------------------------------------------------ riepilogo
titolo("RIGHE PER STATO")
print(reg.groupby(["stato", "regola"]).size().to_string())
print("\nOrigine della previsione:", reg.origine_prev.value_counts().to_dict())

titolo("CONTEGGIO UFFICIALE (regola = vero, partite concluse)")
u = reg[(reg.regola) & (reg.stato == "conclusa") & reg.profitto.notna()]
if len(u):
    print(u[["week", "away", "home", "vento_prev", "origine_prev", "total_line",
             "under_dec", "punti_reali", "esito", "profitto"]].to_string(index=False))
    o, un, p = (u.esito == "over").sum(), (u.esito == "under").sum(), (u.esito == "push").sum()
    tot = u.profitto.sum()
    roi = u.profitto.mean()
    se = u.profitto.std(ddof=1) / math.sqrt(len(u)) if len(u) > 1 else float("nan")
    print(f"\nScommesse: {len(u)}   under {un}, over {o}, push {p}")
    print(f"Profitto: {tot:+.2f} unita'   ROI {roi * 100:+.1f}%" +
          (f" +- {se * 100:.1f}" if len(u) > 1 else ""))
    print(f"Atteso dal backtest: under circa il 59% delle volte. Qui: {un}/{un + o}."
          if un + o else "")
else:
    print("Nessuna partita conclusa che soddisfi la regola.")

titolo("IN ARRIVO CHE SODDISFANO LA REGOLA")
a = reg[(reg.regola) & (reg.stato == "in attesa")]
print(a[["week", "away", "home", "vento_prev", "ore_prima", "total_line", "under_dec", "nota"]].to_string(index=False)
      if len(a) else "Nessuna.")
print("\nPrevisione congelata (entro 36 ore):", int(a.ore_prima.between(0, ORE_CONGELA).sum()),
      "   ancora da aggiornare:", int((a.ore_prima > ORE_CONGELA).sum()))
print("ore_prima = -1 significa ricostruita dall'archivio, non osservata in diretta.")

print(f"\nRegistro: {REGISTRO}")
print("Il bilancio si legge a fine stagione, non ogni domenica: con circa 30 casi l'anno")
print("l'incertezza su una singola stagione e' di circa +-17 punti di ROI.")
