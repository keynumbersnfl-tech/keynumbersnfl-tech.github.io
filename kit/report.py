"""Weekly report. Part 1 observed data (grey), Part 2 estimates from the line (blue),
Part 3 historical check (orange). Runs on the latest snapshot from settimana.py."""
import glob
import html
import math
import os
import sys
import numpy as np
import pandas as pd
import polars as pl
import nflreadpy as nfl
from motore import K, FRANCHIGIE, dec_am, devig_power, tabella_margine, pmf_casa, pmf_favorito

STAGIONE = 2026
ANNI_SIMILI = (2011, 2025)
ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Report Football")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ANT = pd.read_csv("data/anticipo_meteo.csv") if os.path.exists("data/anticipo_meteo.csv") else None
RAT = pd.read_parquet("data/rating_corretto.parquet") if os.path.exists("data/rating_corretto.parquet") else None
e = html.escape

# ------------------------------------------------------------ data
foto = sorted(glob.glob(f"data/snapshot/{STAGIONE}_w*.parquet"))
if not foto:
    print("No snapshot found: run settimana.py first"); sys.exit(1)
w = pd.read_parquet(foto[-1])
week = int(w.week.iloc[0])
quando = pd.Timestamp(w.fotografia.iloc[0]).tz_localize("Europe/Rome").tz_convert("America/New_York")
w["kick"] = pd.to_datetime(w.kick_et).dt.tz_localize("America/New_York")
w = w.sort_values("kick_et").reset_index(drop=True)

st = pd.read_parquet("data/schedules.parquet")
tutte = pd.concat([st[st.season < STAGIONE], nfl.load_schedules([STAGIONE]).to_pandas()], ignore_index=True)
for c in ["home_team", "away_team"]:
    tutte[c] = tutte[c].replace(FRANCHIGIE)
giocate = tutte[tutte.result.notna()].copy()
sim_sp = giocate[(giocate.game_type == "REG") & giocate.season.between(*ANNI_SIMILI) & giocate.spread_line.notna()]
sim_tot = giocate[(giocate.game_type == "REG") & giocate.season.between(*ANNI_SIMILI) & giocate.total_line.notna()]
vento_mis = giocate[(giocate.game_type == "REG") & (giocate.season < STAGIONE) & giocate.roof.isin(["outdoors", "open"])
                    & giocate.wind.notna() & giocate.total_line.notna()]
vento_prev = pd.read_parquet("data/vento_previsto.parquet")
B, sigma = tabella_margine(giocate[giocate.season < STAGIONE], STAGIONE)

try:
    nomi = nfl.load_teams().to_pandas().set_index("team_abbr")["team_name"].to_dict()
except Exception:
    nomi = {}

def tab_stagione(df):
    ok = (pl.col("play_type").is_in(["pass", "run"]) & pl.col("epa").is_not_null()
          & (pl.col("two_point_attempt").fill_null(0) == 0))
    d = df.filter(ok)
    off = d.group_by("posteam").agg(epa=pl.col("epa").mean(), n=pl.len(),
                                    part=pl.col("game_id").n_unique(),
                                    pas=(pl.col("play_type") == "pass").sum()).to_pandas().set_index("posteam")
    dif = d.group_by("defteam").agg(epa=pl.col("epa").mean(), n=pl.len()).to_pandas().set_index("defteam")
    off["azioni_pg"] = off.n / off.part
    off["partite"] = off.part
    off["pass_pct"] = off.pas / off.n
    if "fixed_drive_result" in df.columns:
        dr = (df.filter(pl.col("posteam").is_not_null() & pl.col("fixed_drive").is_not_null()
                        & pl.col("fixed_drive_result").is_not_null())
                .group_by(["game_id", "posteam", "fixed_drive"])
                .agg(res=pl.col("fixed_drive_result").first()).to_pandas())
        dr["td"] = dr.res.eq("Touchdown").astype(int)
        dr["fg"] = dr.res.eq("Field goal").astype(int)
        a = dr.groupby("posteam").agg(poss=("res", "size"), td=("td", "sum"), fg=("fg", "sum"))
        off = off.join(a)
        off["poss_pg"] = off.poss / off.part
        punti = 7 * off.td + 3 * off.fg
        off["ppp"] = punti / off.poss
        off["quota_td"] = (7 * off.td) / punti.replace(0, np.nan)
    return off, dif

def carica(anno):
    f_off, f_dif = f"data/stagione_{anno}_off.parquet", f"data/stagione_{anno}_dif.parquet"
    if anno < STAGIONE and os.path.exists(f_off):
        return pd.read_parquet(f_off), pd.read_parquet(f_dif)
    o, dd = tab_stagione(nfl.load_pbp([anno]))
    if anno < STAGIONE:
        o.to_parquet(f_off); dd.to_parquet(f_dif)
    return o, dd

off26 = def26 = o25 = d25 = None
for anno, etichetta in [(STAGIONE, "26"), (STAGIONE - 1, "25")]:
    try:
        a, b = carica(anno)
        if etichetta == "26":
            off26, def26 = a, b
        else:
            o25, d25 = a, b
    except Exception as ex:
        print(f"Play-by-play {anno} unavailable:", ex)

# ------------------------------------------------------------ helpers
def nome(t): return f"{nomi.get(t, t)} ({t})"
def pct(p): return "n/a" if p is None or pd.isna(p) else f"{p * 100:.1f}%"
def quota(x): return "n/a" if pd.isna(x) else f"{x:.2f}"
def conta(x, n): return f"{x} of {n} ({x / n * 100:.0f}%)" if n else "none"
def linea(x): return "pk" if x == 0 else f"{x:+g}"
def data_us(d): return f"{int(d[5:7])}/{int(d[8:10])}/{d[2:4]}"

def tabella(intest, righe):
    h = "<div class='wrap'><table>"
    if intest:
        h += "<tr>" + "".join(f"<th>{e(str(x))}</th>" for x in intest) + "</tr>"
    for r in righe:
        h += "<tr>" + "".join(f"<td>{e(str(x))}</td>" for x in r) + "</tr>"
    return h + "</table></div>"

def blocco(classe, titolo, corpo):
    return f"<div class='{classe}'><h3>{e(titolo)}</h3>{corpo}</div>"

def epa_txt(tab, team, crescente):
    if tab is None or team not in tab.index:
        return "n/a"
    pos = int(tab.epa.rank(ascending=crescente, method="min")[team])
    return f"{tab.epa[team]:+.3f} ({pos})"

def vista(x, team):
    casa = (x.home_team == team).to_numpy()
    hs, as_ = x.home_score.to_numpy(float), x.away_score.to_numpy(float)
    pf, pa = np.where(casa, hs, as_), np.where(casa, as_, hs)
    sp = x.spread_line.to_numpy(float)
    return pd.DataFrame({"data": x.gameday.to_numpy(), "season": x.season.to_numpy(),
                         "tipo": x.game_type.to_numpy(), "casa": casa,
                         "avv": np.where(casa, x.away_team, x.home_team), "pf": pf, "pa": pa,
                         "ats": np.sign(pf - pa - np.where(casa, sp, -sp)),
                         "ou": np.sign(x.total.to_numpy(float) - x.total_line.to_numpy(float))})

def storia(team, prima):
    x = giocate[((giocate.home_team == team) | (giocate.away_team == team)) & (giocate.gameday < prima)]
    return vista(x.sort_values("gameday", ascending=False), team)

ESITO_ATS = {1.0: "covered", 0.0: "push", -1.0: "no cover"}
ESITO_OU = {1.0: "over", 0.0: "push", -1.0: "under"}

medie = {c: (o25[c].mean() if o25 is not None and c in o25.columns else float("nan"))
         for c in ["poss_pg", "azioni_pg", "ppp", "pass_pct"]}

def val(tab, team, col, fmt=".1f", perc=False):
    if tab is None or team not in tab.index or col not in tab.columns or pd.isna(tab[col][team]):
        return "n/a"
    x = tab[col][team]
    return f"{x * 100:.0f}%" if perc else format(x, fmt)

# ------------------------------------------------------------ Part 1
def parte1_squadra(team, prima, ruolo):
    v = storia(team, prima)
    s = v[(v.season == STAGIONE) & (v.tipo == "REG")]
    n = len(s)
    W, L = int((s.pf > s.pa).sum()), int((s.pf < s.pa).sum())
    base = [["Record", f"{W}-{L}" + (f"-{n - W - L}" if n - W - L else "")]]
    if n:
        base.append(["Points scored / allowed per game", f"{s.pf.mean():.1f} / {s.pa.mean():.1f}"])
    np26 = int(off26.partite[team]) if (off26 is not None and team in off26.index) else 0
    np25 = int(o25.partite[team]) if (o25 is not None and team in o25.index) else 0
    conf = [["Offensive plays per game", val(off26, team, "azioni_pg", ".0f"), val(o25, team, "azioni_pg", ".0f")],
            ["Drives per game", val(off26, team, "poss_pg", ".1f"), val(o25, team, "poss_pg", ".1f")],
            ["Share of plays that are passes", val(off26, team, "pass_pct", perc=True),
             val(o25, team, "pass_pct", perc=True)],
            ["EPA per play, offense", epa_txt(off26, team, False), epa_txt(o25, team, False)],
            ["EPA per play allowed, defense", epa_txt(def26, team, True), epa_txt(d25, team, True)],
            ["Points per drive", val(off26, team, "ppp", ".2f"), val(o25, team, "ppp", ".2f")],
            ["Share of points from touchdowns", val(off26, team, "quota_td", perc=True),
             val(o25, team, "quota_td", perc=True)]]
    def rat(col, rank):
        if RAT is None or team not in RAT.index:
            return "n/a"
        return f"{RAT[col][team]:+.3f} ({int(RAT[rank][team])})"
    corr = [["Offense, adjusted", rat("off", "off_rank")],
            ["Defense, adjusted", rat("dif", "dif_rank")]]
    ult = [[data_us(r.data), ("vs " if r.casa else "at ") + r.avv,
            f"{'W' if r.pf > r.pa else ('L' if r.pf < r.pa else 'T')} {int(r.pf)}-{int(r.pa)}",
            ESITO_ATS.get(r.ats, "n/a"), ESITO_OU.get(r.ou, "n/a")] for r in v.head(5).itertuples()]
    h = (f"<h4>{e(nome(team))} &middot; {ruolo}</h4>" + tabella(None, base)
         + tabella(["How they play", f"{STAGIONE} ({np26} games)", f"{STAGIONE - 1} ({np25} games)"], conf)
         + tabella(["Adjusted for opponents faced", ""], corr)
         + "<p class='nota'>Deviation from league average in EPA per play, computed over the last four "
           "seasons, weighting recent games more heavily and accounting for who each team has faced. "
           "For defense, negative is good. Where this differs from the raw EPA above, the gap is "
           "schedule.</p>"
         + "<p class='nota'>Rank out of 32 in parentheses. Points per drive counts offensive touchdowns "
           f"and field goals only. League average: {medie['poss_pg']:.1f} drives and "
           f"{medie['azioni_pg']:.0f} plays per game, {medie['ppp']:.2f} points per drive, "
           f"{medie['pass_pct'] * 100:.0f}% passes. The current-season column rests on few games, so it "
           "swings a lot.</p>"
         + "<p class='nota'>Last 5 games</p>"
         + tabella(["Date", "Opponent", "Result", "Spread", "Total"], ult))
    if n:
        h += tabella([f"Against the market, {STAGIONE}", ""],
                     [["Covered the spread", conta(int((s.ats > 0).sum()), int(s.ats.notna().sum()))],
                      ["Over in their games", conta(int((s.ou > 0).sum()), int(s.ou.notna().sum()))]])
        h += ("<p class='nota'>Over this few games these two numbers are close to pure noise: "
              "historically they say nothing about how the next ones will go.</p>")
    return h

def mercato(r):
    righe = []
    def coppia(nome_m, la, da, lb, db):
        if pd.isna(da) or pd.isna(db):
            righe.append([nome_m, f"{la} / {lb}", "n/a", "", "", ""]); return
        pa, pb = devig_power(da, db)
        marg = 1 / da + 1 / db - 1
        righe.append([nome_m, la, quota(da), pct(1 / da), pct(pa), pct(marg)])
        righe.append(["", lb, quota(db), pct(1 / db), pct(pb), ""])
    s = r.spread_line
    if pd.notna(s):
        coppia("Spread", f"{r.away_team} {linea(s)}", dec_am(r.away_spread_odds),
               f"{r.home_team} {linea(-s)}", dec_am(r.home_spread_odds))
    if pd.notna(r.total_line):
        coppia("Total", f"Over {r.total_line:g}", dec_am(r.over_odds), f"Under {r.total_line:g}", dec_am(r.under_odds))
    coppia("Moneyline", r.away_team, dec_am(r.away_moneyline), r.home_team, dec_am(r.home_moneyline))
    return tabella(["Market", "Side", "Odds", "Implied", "No-vig", "Hold"], righe)

def precedenti(a, b, prima):
    x = giocate[(((giocate.home_team == a) & (giocate.away_team == b)) | ((giocate.home_team == b) & (giocate.away_team == a)))
                & (giocate.gameday < prima) & (giocate.season >= 2016)].sort_values("gameday", ascending=False).head(5)
    if x.empty:
        return "<p>No meetings since 2016.</p>"
    return tabella(["Date", "Game", "Result"],
                   [[data_us(r.gameday), f"{r.away_team} at {r.home_team}", f"{int(r.away_score)}-{int(r.home_score)}"]
                    for r in x.itertuples()])

def ore_prima(r):
    return (pd.Timestamp(r.kick_et).tz_localize("America/New_York") - quando).total_seconds() / 3600

def incertezza(ore):
    if ANT is None or ore <= 0:
        return None
    riga = ANT.iloc[(ANT.giorni - ore / 24).abs().argmin()]
    return float(riga.errore_tipico)

def meteo_txt(r):
    if r.location == "Neutral":
        return f"Neutral site: {e(str(r.stadium))}."
    if r.roof in ("dome", "closed"):
        return f"{e(str(r.stadium))}: indoors, weather does not apply."
    if pd.isna(r.vento_prev):
        return f"{e(str(r.stadium))}: forecast unavailable."
    ore = ore_prima(r)
    inc = incertezza(ore)
    t = f"{e(str(r.stadium))}: wind forecast <b>{r.vento_prev:.1f} mph</b>"
    if inc:
        t += (f", so realistically between {max(r.vento_prev - inc, 0):.0f} and {r.vento_prev + inc:.0f} mph "
              f"(forecast made {ore / 24:.1f} days out, typical error &plusmn;{inc:.1f})")
    t += (f". Temperature {r.temp_prev:.0f}&deg;F, chance of rain {r.pioggia_prob:.0f}%.")
    if r.roof == "open" or pd.isna(r.roof):
        t += " Retractable roof: the call is made on game day."
    return t

# ------------------------------------------------------------ Part 2
def parte2(r):
    s = r.spread_line
    if pd.isna(s):
        return "<p>Spread not posted yet.</p>"
    ph = pmf_casa(B, s)
    p_c, p_n, p_t = ph[K > 0].sum(), ph[K == 0].sum(), ph[K < 0].sum()
    dm_c, dm_t = dec_am(r.home_moneyline), dec_am(r.away_moneyline)
    ml_t, ml_c = devig_power(dm_t, dm_c) if pd.notna(dm_c) and pd.notna(dm_t) else (np.nan, np.nan)
    righe = [[f"{r.away_team} win", pct(p_t / (1 - p_n)), pct(ml_t)],
             [f"{r.home_team} win", pct(p_c / (1 - p_n)), pct(ml_c)],
             ["Tie", pct(p_n), "(moneyline refunded)"]]
    h = tabella(["Outcome", "From the spread", "From the moneyline"], righe)
    h += "<p class='nota'>Win probabilities exclude ties, the same way the moneyline does.</p>"
    righe = [[f"{r.away_team} {linea(s)} covers", pct(ph[K < s].sum())],
             [f"{r.home_team} {linea(-s)} covers", pct(ph[K > s].sum())],
             ["Push", pct(ph[K == s].sum())]]
    h += tabella(["Spread at the current line", "Probability"], righe)
    L = abs(s)
    if L > 0:
        fav = r.home_team if s > 0 else r.away_team
        pf = pmf_favorito(B, s)
        numeri = sorted({math.floor(L), math.ceil(L)} - {0})
        h += tabella([f"{fav} wins by exactly", "Probability"],
                     [[f"{n} points", pct(pf[K == n].sum())] for n in numeri])
        h += "<p class='nota'>The margins sitting either side of the line &mdash; this is what that half point is worth.</p>"
    h += ("<p class='nota'>Probabilities derived from the market line using the historical distribution of "
          f"final margins, which puts the real weight on 3 and 7 instead of assuming a smooth curve "
          f"(validated on 2016&ndash;2025; spread used {sigma:.1f} points).</p>")
    return h

# ------------------------------------------------------------ Part 3
def parte3(r):
    h = ""
    s = r.spread_line
    if pd.notna(s):
        L = abs(s)
        x = sim_sp[(sim_sp.spread_line.abs() - L).abs() <= 0.5]
        def riga(nome_g, y):
            fm = np.where(y.spread_line > 0, y.result, -y.result)
            n = len(y)
            return [nome_g, n, conta(int((fm > 0).sum()), n), conta(int((fm > L).sum()), n), conta(int((fm == L).sum()), n)]
        righe = [riga("All", x)]
        if s != 0:
            stesso = x[x.spread_line > 0] if s > 0 else x[x.spread_line < 0]
            righe.append(riga("Favorite at home" if s > 0 else "Favorite on the road", stesso))
        h += (f"<p>Games from {ANNI_SIMILI[0]}&ndash;{ANNI_SIMILI[1]} with the favorite laying "
              f"{max(L - 0.5, 0):g} to {L + 0.5:g} points:</p>")
        h += tabella(["Group", "Games", "Favorite won", f"Won by more than {L:g}", f"Won by exactly {L:g}"], righe)
    T = r.total_line
    if pd.notna(T):
        y = sim_tot[(sim_tot.total_line - T).abs() <= 1]
        o, u, p = int((y.total > y.total_line).sum()), int((y.total < y.total_line).sum()), int((y.total == y.total_line).sum())
        h += (f"<p>Games from {ANNI_SIMILI[0]}&ndash;{ANNI_SIMILI[1]} with a total between {T - 1:g} and "
              f"{T + 1:g}, measured against their own line:</p>")
        h += tabella(["Games", "Over", "Under", "Push", "Points (median)"],
                     [[len(y), conta(o, len(y)), conta(u, len(y)), conta(p, len(y)), f"{y.total.median():.0f}"]])
    if pd.notna(r.vento_prev) and r.location != "Neutral":
        v = r.vento_prev
        a = vento_prev[((vento_prev.v_prev - v).abs() <= 3) & (vento_prev.res != 0)]
        b = vento_mis[((vento_mis.wind - v).abs() <= 3) & (vento_mis.total != vento_mis.total_line)]
        h += f"<p>Outdoor games with similar wind ({max(v - 3, 0):.0f}&ndash;{v + 3:.0f} mph):</p>"
        h += tabella(["Sample", "Over (pushes excluded)"],
                     [["Forecast wind, 2021&ndash;2025", conta(int((a.res > 0).sum()), len(a))],
                      ["Measured wind, 1999&ndash;2025", conta(int((b.total > b.total_line).sum()), len(b))]])
    return h or "<p>No data.</p>"

# ------------------------------------------------------------ page
CSS = """
body{font-family:-apple-system,Helvetica,Arial,sans-serif;background:#fff;color:#111;margin:0;padding:12px 16px;font-size:15px;line-height:1.35}
h1{font-size:20px;margin:6px 0} h3{font-size:15px;margin:4px 0 6px} h4{font-size:14px;margin:10px 0 4px}
summary{font-weight:600;padding:12px 2px;cursor:pointer} details{border-bottom:1px solid #ddd}
.oss{background:#f1f1f1;border-left:4px solid #888;padding:8px 10px;margin:8px 0;border-radius:4px}
.mod{background:#e8f0fe;border-left:4px solid #1a73e8;padding:8px 10px;margin:8px 0;border-radius:4px}
.ctl{background:#fff3e0;border-left:4px solid #f57c00;padding:8px 10px;margin:8px 0;border-radius:4px}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 8px}
td,th{border-bottom:1px solid #d6d6d6;padding:4px 5px;text-align:left;vertical-align:top} th{font-weight:600}
.nota{font-size:12px;color:#555} .vent{color:#0f6e56;font-weight:400} .fin{color:#555;font-weight:400}
"""
sezioni = []
for i, r in w.iterrows():
    k = r.kick
    quando_txt = f"{DAYS[k.weekday()]} {k.month}/{k.day} {k.strftime('%I:%M %p').lstrip('0')} ET"
    s = r.spread_line
    linea_txt = "" if pd.isna(s) else (f"{r.home_team} {linea(-s)}" if s > 0 else f"{r.away_team} {linea(s)}" if s < 0 else "pick'em")
    tot_txt = "" if pd.isna(r.total_line) else f"O/U {r.total_line:g}"
    fine = f" <span class='fin'>&middot; final {int(r.away_score)}-{int(r.home_score)}</span>" if pd.notna(r.result) else ""
    flag = " <span class='vent'>&middot; windy</span>" if r.regola_vento or getattr(r, "regola_cond", False) else ""
    p1 = (f"<p>{meteo_txt(r)}</p>"
          f"<p>Rest: {r.away_team} {r.away_rest:.0f} days, {r.home_team} {r.home_rest:.0f} days.</p>"
          + parte1_squadra(r.away_team, r.gameday, "away")
          + parte1_squadra(r.home_team, r.gameday, "home")
          + "<h4>Head to head since 2016</h4>" + precedenti(r.away_team, r.home_team, r.gameday)
          + "<h4>Odds</h4>" + mercato(r))
    sezioni.append(
        f"<details><summary>{e(quando_txt)} &middot; {e(r.away_team)} at {e(r.home_team)} &middot; {e(linea_txt)} &middot; {e(tot_txt)}{fine}{flag}</summary>"
        + blocco("oss", "1 · Observed data", p1)
        + blocco("mod", "2 · Estimates", parte2(r))
        + blocco("ctl", "3 · Historical check", parte3(r))
        + "</details>")

pagina = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>NFL {STAGIONE} Week {week}</title>
<style>{CSS}</style></head><body>
<h1>NFL {STAGIONE} &middot; Week {week}</h1>
<p class="nota">Data as of {quando:%b %d, %I:%M %p} ET. All times Eastern. Lines and weather keep moving until
kickoff &mdash; the game day update carries the final numbers.</p>
<p class="nota"><b>Grey</b> = observed data, counted and nothing else. <b>Blue</b> = estimates derived from the
market line. <b>Orange</b> = similar games from past seasons, and how often each result actually came up.</p>
{''.join(sezioni)}
<p class="nota" style="margin-top:18px">New to these numbers?
<a href="../GUIDA.html">How to read the report</a></p>
</body></html>"""

cartella = os.path.join(ICLOUD, f"{STAGIONE}_W{week:02d}")
os.makedirs(cartella, exist_ok=True)
os.makedirs("report", exist_ok=True)
nome_file = f"NFL_{STAGIONE}_W{week:02d}.html"
for dest in [os.path.join(cartella, nome_file), os.path.join("report", nome_file)]:
    with open(dest, "w", encoding="utf-8") as f:
        f.write(pagina)
print(f"Report week {week}: {len(sezioni)} games")
print("Saved to:", os.path.join(cartella, nome_file))
print("Local copy: report/" + nome_file)
