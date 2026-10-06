"""Conteggi per i post Instagram. Nessun numero a memoria: tutto da data/schedules.parquet."""
import pandas as pd

d = pd.read_parquet("data/schedules.parquet")
r = d[(d.game_type == "REG") & d.result.notna() & (d.season >= 2002)].copy()
r["marg"] = r.result.abs()
n = len(r)
print(f"CAMPIONE: {n} partite di regular season, {int(r.season.min())}-{int(r.season.max())}\n")

print("--- MARGINI PIU' FREQUENTI ---")
c = r.marg.value_counts().sort_values(ascending=False).head(12)
for m, k in c.items():
    print(f"  margine {int(m):>2}: {k:>5} partite   ({k/n*100:4.1f}%)   ~{round(k/n*100)} ogni 100")

print("\n--- IL BUCO DEL 9 ---")
for m in (8, 9, 10, 11):
    k = int((r.marg == m).sum())
    print(f"  margine {m:>2}: {k:>5} partite ({k/n*100:4.1f}%)")
nove, dieci = int((r.marg == 9).sum()), int((r.marg == 10).sum())
print(f"  il 10 e' {dieci/nove:.1f} volte piu' frequente del 9")

print("\n--- CAMPO DI CASA ---")
for lo, hi in [(2002, 2025), (2002, 2010), (2011, 2019), (2020, 2025)]:
    x = r[(r.season >= lo) & (r.season <= hi)]
    v = int((x.result > 0).sum()); t = int((x.result != 0).sum())
    print(f"  {lo}-{hi}: casa vince {v} su {t}  ({v/t*100:.1f}%)")

print("\n--- FAVORITO CONTRO LO SPREAD ---")
s = r[r.spread_line.notna()].copy()
s = s[s.spread_line != 0]
s["push"] = s.result == s.spread_line
v = s[~s.push]
cop = ((v.result > v.spread_line) & (v.spread_line > 0)) | ((v.result < v.spread_line) & (v.spread_line < 0))
print(f"  campione {len(s)} partite ({int(s.season.min())}-{int(s.season.max())})")
print(f"  favorito copre: {int(cop.sum())} su {len(v)}  ({cop.mean()*100:.1f}%)   push esclusi: {int(s.push.sum())}")

print("\n--- QUANDO LA LINEA E' ESATTAMENTE 3 ---")
t3 = r[r.spread_line.abs() == 3]
p3 = int((t3.result.abs() == 3).sum())
print(f"  linea 3: {len(t3)} partite, finite esattamente sul 3: {p3}  ({p3/len(t3)*100:.1f}%)  ~{round(p3/len(t3)*100)} ogni 100")
t35 = r[r.spread_line.abs() == 3.5]
print(f"  linea 3.5: {len(t35)} partite, push impossibili per costruzione")

print("\n--- TOTALI ---")
o = r[r.total_line.notna() & r.total.notna()]
ov = int((o.total > o.total_line).sum()); un = int((o.total < o.total_line).sum())
print(f"  campione {len(o)} partite ({int(o.season.min())}-{int(o.season.max())})")
print(f"  over: {ov} su {ov+un}  ({ov/(ov+un)*100:.1f}%)   push: {int((o.total == o.total_line).sum())}")

print("\n--- PARTITE DECISE DA POCO ---")
for soglia in (3, 7):
    k = int((r.marg <= soglia).sum())
    print(f"  decise da {soglia} punti o meno: {k} su {n}  ({k/n*100:.1f}%)  ~{round(k/n*100)} ogni 100")
