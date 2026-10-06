"""Rating di attacco e difesa corretti per la forza degli avversari.
Stessi parametri validati in backtest_m2.py: emivita 12 settimane, ridge 300, tutte le azioni,
finestra di 4 stagioni. Il valore e' lo scostamento dalla media di lega, in EPA per azione."""
import percorsi  # ancora i percorsi alla radice del progetto
import numpy as np
import pandas as pd
import polars as pl
import nflreadpy as nfl

STAGIONE, EMIVITA, RIDGE, PAUSA, FINESTRA = 2026, 12, 300, 10, 4
FRANCHIGIE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

ok = (pl.col("play_type").is_in(["pass", "run"]) & pl.col("epa").is_not_null()
      & (pl.col("two_point_attempt").fill_null(0) == 0))
cur = (nfl.load_pbp([STAGIONE]).filter(ok)
       .group_by(["game_id", "posteam", "defteam"])
       .agg(n=pl.len(), epa=pl.col("epa").sum()).to_pandas())
pt = pd.concat([pd.read_parquet("data/pbp_squadre.parquet")[["game_id", "posteam", "defteam", "n", "epa"]],
                cur], ignore_index=True).drop_duplicates(subset=["game_id", "posteam"], keep="last")
for c in ["posteam", "defteam"]:
    pt[c] = pt[c].replace(FRANCHIGIE)
pt = pt[pt.n > 0].copy()

pezzi = pt.game_id.str.split("_", n=2, expand=True)
pt["t"] = pezzi[0].astype(int).sub(1999).mul(22 + PAUSA) + pezzi[1].astype(int)
t_now = pt.t.max() + 1

squadre = sorted(set(pt.posteam) | set(pt.defteam))
T = len(squadre)
pos = {s: i for i, s in enumerate(squadre)}
m = pt.t >= t_now - FINESTRA * (22 + PAUSA)
d = pt[m]
print(f"Squadre {T}   righe usate {len(d)} (dalle ultime {FINESTRA} stagioni)   "
      f"ultima settimana nei dati: {pt.game_id[pt.t.idxmax()]}")

P = 1 + 2 * T
X = np.zeros((len(d), P))
ar = np.arange(len(d))
X[ar, 0] = 1
X[ar, 1 + d.posteam.map(pos).to_numpy()] = 1
X[ar, 1 + T + d.defteam.map(pos).to_numpy()] = 1
y = (d.epa / d.n).to_numpy()
w = d.n.to_numpy() * 0.5 ** ((t_now - d.t.to_numpy()) / EMIVITA)
pen = np.full(P, float(RIDGE)); pen[0] = 0.0
beta = np.linalg.solve(X.T @ (X * w[:, None]) + np.diag(pen), X.T @ (w * y))

r = pd.DataFrame({"team": squadre, "off": beta[1:1 + T], "dif": beta[1 + T:]}).set_index("team")
r["off_rank"] = r.off.rank(ascending=False, method="min").astype(int)
r["dif_rank"] = r.dif.rank(ascending=True, method="min").astype(int)
r.to_parquet("data/rating_corretto.parquet")

print(f"\nMedia di lega (intercetta): {beta[0]:+.3f} EPA per azione")
print("\nMigliori 5 attacchi:")
print(r.sort_values("off", ascending=False).head(5)[["off", "off_rank"]].round(3).to_string())
print("\nMigliori 5 difese (negativo = concede meno):")
print(r.sort_values("dif").head(5)[["dif", "dif_rank"]].round(3).to_string())
print("\nPeggiori 3 difese:")
print(r.sort_values("dif").tail(3)[["dif", "dif_rank"]].round(3).to_string())
print("\nSalvato in data/rating_corretto.parquet")
