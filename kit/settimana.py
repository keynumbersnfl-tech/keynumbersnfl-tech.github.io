"""Fotografia della week in corso: linee di quel momento + meteo previsto. Salvata con data e ora.
Da lanciare piu' volte in settimana (es. mercoledi', sabato, domenica mattina)."""
import sys
from datetime import datetime
import numpy as np
import pandas as pd
import requests
import nflreadpy as nfl
from stadi import COORD

SOGLIA_VENTO = 11.0          # regola fissata in NOTE_DATI.md: non toccare
RETRATTILI = {"ARI", "ATL", "DAL", "HOU", "IND"}   # nflverse lascia roof vuoto per le partite future
FORECAST = "https://api.open-meteo.com/v1/forecast"
STAGIONE = 2026

def dec_am(ml):
    if pd.isna(ml):
        return np.nan
    return 1 + ml / 100 if ml > 0 else 1 + 100 / abs(ml)

adesso = datetime.now()
sch = nfl.load_schedules([STAGIONE]).to_pandas()
reg = sch[sch.game_type == "REG"].copy()
reg["kick"] = pd.to_datetime(reg.gameday + " " + reg.gametime)
ora_et = pd.Timestamp.now(tz="Europe/Rome").tz_convert("America/New_York").tz_localize(None)
quota = reg.assign(futura=reg.kick > ora_et).groupby("week").futura.mean()
restanti = quota[quota >= 0.5]
if restanti.empty:
    print("Nessuna week con la maggioranza delle partite ancora da giocare."); sys.exit(0)
week = int(restanti.index.min())
w = sch[(sch.week == week) & (sch.game_type == "REG")].copy()
w["kick_et"] = pd.to_datetime(w.gameday + " " + w.gametime)
w["kick_it"] = w.kick_et.dt.tz_localize("America/New_York")
w = w.sort_values("kick_et").reset_index(drop=True)

# ------------------------------------------------ meteo previsto
cache = {}
def previsione(team, kick_et):
    if team not in cache:
        lat, lon = COORD[team]
        par = {"latitude": lat, "longitude": lon, "forecast_days": 16,
               "hourly": "wind_speed_10m,wind_gusts_10m,temperature_2m,precipitation_probability",
               "wind_speed_unit": "mph", "temperature_unit": "fahrenheit",
               "timezone": "America/New_York"}
        r = requests.get(FORECAST, params=par, timeout=60)
        r.raise_for_status()
        h = pd.DataFrame(r.json()["hourly"])
        h["time"] = pd.to_datetime(h["time"])
        cache[team] = h.set_index("time")
    h = cache[team]
    t0 = kick_et.floor("h")
    b = h.loc[t0:t0 + pd.Timedelta(hours=2)]
    if b.empty:
        return np.nan, np.nan, np.nan, np.nan
    return (b.wind_speed_10m.mean(), b.wind_gusts_10m.max(),
            b.temperature_2m.mean(), b.precipitation_probability.max())

meteo = []
for _, r in w.iterrows():
    aperto = (r.roof in ("outdoors", "open") or (pd.isna(r.roof) and r.home_team in RETRATTILI)) and r.location != "Neutral"
    if aperto and r.home_team in COORD and pd.isna(r.result):
        try:
            meteo.append(previsione(r.home_team, r.kick_et))
        except Exception as e:
            print(f"  meteo non disponibile per {r.home_team}: {e!r}")
            meteo.append((np.nan,) * 4)
    else:
        meteo.append((np.nan,) * 4)
w[["vento_prev", "raffica_prev", "temp_prev", "pioggia_prob"]] = pd.DataFrame(meteo)

w["regola_vento"] = (w.roof.isin(["outdoors", "open"]) & (w.location != "Neutral")
                     & (w.vento_prev >= SOGLIA_VENTO))
w["regola_cond"] = (w.roof.isna() & w.home_team.isin(RETRATTILI) & (w.location != "Neutral")
                    & (w.vento_prev >= SOGLIA_VENTO))

# ------------------------------------------------ stampa
print(f"\nWEEK {week} {STAGIONE}   fotografia del {adesso:%d/%m/%Y %H:%M} (ora italiana)   orari partite in ET")
print(f"Partite: {len(w)}   con spread: {int(w.spread_line.notna().sum())}   "
      f"con totale: {int(w.total_line.notna().sum())}\n")
for _, r in w.iterrows():
    s = r.spread_line
    if pd.isna(s):
        linea = "spread n.d."
    elif s > 0:
        linea = f"{r.home_team} -{s:g}"
    elif s < 0:
        linea = f"{r.away_team} -{-s:g}"
    else:
        linea = "pick'em"
    tot = f"O/U {r.total_line:g}" if pd.notna(r.total_line) else "O/U n.d."
    ml = f"ML {dec_am(r.away_moneyline):.2f} / {dec_am(r.home_moneyline):.2f}" if pd.notna(r.home_moneyline) else "ML n.d."
    stato = f"FINITA {int(r.away_score)}-{int(r.home_score)}" if pd.notna(r.result) else ""
    print(f"{r.kick_it:%a %m/%d %I:%M%p} ET  {r.away_team:>3} @ {r.home_team:<3}  {linea:<12} {tot:<10} {ml:<20} {stato}")
    if r.location == "Neutral":
        meteo_txt = f"campo neutro ({r.stadium}): regola non applicabile"
    elif r.roof in ("dome", "closed"):
        meteo_txt = f"stadio coperto ({r.roof})"
    elif pd.isna(r.vento_prev):
        meteo_txt = "meteo non disponibile"
    else:
        meteo_txt = (f"vento {r.vento_prev:.1f} mph (raffiche {r.raffica_prev:.0f}), "
                     f"{r.temp_prev:.0f}F, pioggia {r.pioggia_prob:.0f}%")
        if r.roof == "open" or pd.isna(r.roof):
            meteo_txt += "  [tetto retrattile: si decide il giorno della partita, la regola vale solo se aperto]"
    if r.regola_vento:
        flag = "   >>> REGOLA VENTO: UNDER"
    elif r.regola_cond:
        flag = "   >>> REGOLA VENTO: UNDER solo se tetto aperto"
    else:
        flag = ""
    print(f"{'':>17}{meteo_txt}{flag}")

nome = f"data/snapshot/{STAGIONE}_w{week:02d}_{adesso:%Y%m%d_%H%M}.parquet"
w.assign(fotografia=adesso).drop(columns=["kick_it"]).to_parquet(nome)
print(f"\nFotografia salvata: {nome}")
