"""Funzioni condivise, tutte gia' validate negli script di backtest (prob_linea.py, bias_moneyline.py)."""
import math
import numpy as np

K = np.arange(-80, 81)              # margini possibili
LINEE = np.arange(0, 30.5, 0.5)     # linee dal punto di vista del favorito
BW, EMIVITA_STAG, ALFA = 1.0, 10, 0.10
FRANCHIGIE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}
_verf = np.vectorize(math.erf)

def _Phi(x):
    return 0.5 * (1 + _verf(np.asarray(x) / math.sqrt(2)))

def dec_am(ml):
    """Quota americana -> decimale. Scalare o array; NaN resta NaN."""
    a = np.asarray(ml, dtype=float)
    out = np.where(a > 0, 1 + a / 100, 1 + 100 / np.abs(a))
    return float(out) if out.ndim == 0 else out

def devig_power(d1, d2):
    """Probabilita' senza margine, metodo power: q1^k + q2^k = 1."""
    scalare = np.ndim(d1) == 0
    q1 = 1 / np.atleast_1d(np.asarray(d1, float))
    q2 = 1 / np.atleast_1d(np.asarray(d2, float))
    lo, hi = np.full(q1.shape, 0.3), np.full(q1.shape, 3.0)
    for _ in range(60):
        mid = (lo + hi) / 2
        troppo = q1 ** mid + q2 ** mid > 1
        lo, hi = np.where(troppo, mid, lo), np.where(troppo, hi, mid)
    k = (lo + hi) / 2
    p1, p2 = q1 ** k, q2 ** k
    return (float(p1[0]), float(p2[0])) if scalare else (p1, p2)

def tabella_margine(storico, stagione):
    """Metodo B: distribuzione del margine del favorito per ogni linea, dalle stagioni precedenti."""
    g = storico[(storico.game_type == "REG") & storico.result.notna()
                & storico.spread_line.notna() & (storico.season < stagione)]
    s, m, se = g.spread_line.to_numpy(float), g.result.to_numpy(float), g.season.to_numpy()
    pos, neg, zer = s > 0, s < 0, s == 0
    fs = np.concatenate([s[pos], -s[neg], np.zeros(zer.sum()), np.zeros(zer.sum())])
    fm = np.concatenate([m[pos], -m[neg], m[zer], -m[zer]])
    ss = np.concatenate([se[pos], se[neg], se[zer], se[zer]])
    w0 = np.concatenate([np.ones(pos.sum()), np.ones(neg.sum()),
                         np.full(zer.sum(), 0.5), np.full(zer.sum(), 0.5)])
    fm = np.clip(fm, K[0], K[-1]).astype(int)
    wt = w0 * 0.5 ** ((stagione - ss) / EMIVITA_STAG)
    sigma = math.sqrt(np.sum(wt * (fm - fs) ** 2) / np.sum(wt))
    B = np.empty((len(LINEE), len(K)))
    for j, L in enumerate(LINEE):
        a = _Phi((K + 0.5 - L) / sigma) - _Phi((K - 0.5 - L) / sigma)
        a = a / a.sum()
        kw = wt * np.exp(-(fs - L) ** 2 / (2 * BW ** 2))
        emp = np.bincount(fm - K[0], weights=kw, minlength=len(K)).astype(float)
        B[j] = (1 - ALFA) * emp / emp.sum() + ALFA * a
    return B, sigma

def pmf_favorito(B, spread):
    return B[min(int(round(abs(spread) * 2)), len(LINEE) - 1)]

def pmf_casa(B, spread):
    """Distribuzione del margine della squadra di casa (spread_line nflverse: positivo = casa favorita)."""
    pf = pmf_favorito(B, spread)
    return pf[::-1] if spread < 0 else pf
