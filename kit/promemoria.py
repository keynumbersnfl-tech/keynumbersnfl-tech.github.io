"""Promemoria Instagram nella chat privata.
Lunedi': riepilogo della settimana.  Ogni giorno: il post di oggi, con immagine e didascalia.
Uso: python kit/promemoria.py [AAAA-MM-GG]   (la data serve solo per le prove)"""
import percorsi
import csv
import glob
import json
import os
import sys
from datetime import date, timedelta
import requests

CAL = os.path.join(percorsi.RADICE, "post", "calendario.csv")
POST = os.path.join(percorsi.RADICE, "post")
GIORNI = ["Lunedi", "Martedi", "Mercoledi", "Giovedi", "Venerdi", "Sabato", "Domenica"]

def credenziali():
    if os.environ.get("TELEGRAM_TOKEN") and os.environ.get("TELEGRAM_PRIVATA"):
        return os.environ["TELEGRAM_TOKEN"], os.environ["TELEGRAM_PRIVATA"]
    for p in (".secrets/telegram.json",
              os.path.expanduser("~/Desktop/Bolle test/files/nflkit/.secrets/telegram.json")):
        if os.path.exists(p):
            c = json.load(open(p))
            return c["token"], c["privata"]
    raise SystemExit("credenziali Telegram non trovate")

TOKEN, CHAT = credenziali()
API = f"https://api.telegram.org/bot{TOKEN}"

def manda(testo):
    r = requests.post(f"{API}/sendMessage", timeout=25,
                      json={"chat_id": CHAT, "text": testo,
                            "disable_web_page_preview": True}).json()
    if not r.get("ok"):
        print("errore testo:", r)
    return r.get("ok", False)

def manda_file(percorso):
    with open(percorso, "rb") as f:
        r = requests.post(f"{API}/sendDocument", timeout=90,
                          data={"chat_id": CHAT},
                          files={"document": (os.path.basename(percorso), f)}).json()
    if not r.get("ok"):
        print("errore file:", r)
    return r.get("ok", False)

def blocco(numero, titolo_blocco):
    """Estrae un blocco numerato dal file del post."""
    f = os.path.join(POST, f"post_{numero}.txt")
    if not os.path.exists(f):
        return None
    testo = open(f, encoding="utf-8").read()
    chiave = f"## {titolo_blocco}"
    if chiave not in testo:
        return None
    dopo = testo.split(chiave, 1)[1]
    return dopo.split("\n## ", 1)[0].strip()

oggi = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
righe = list(csv.DictReader(open(CAL, encoding="utf-8")))
oggi_s = oggi.isoformat()
inviati = 0

# ------------------------------------------------ lunedi: riepilogo della settimana
if oggi.weekday() == 0:
    fine = (oggi + timedelta(days=6)).isoformat()
    sett = [x for x in righe if oggi_s <= x["data"] <= fine]
    t = ["La settimana su Instagram:", "",
         "Martedi 17:00   consuntivo della week - arriva da solo",
         "Mercoledi 16:00   partita della settimana - arriva da sola"]
    for x in sett:
        g = date.fromisoformat(x["data"])
        t.append(f"{GIORNI[g.weekday()]} {g.strftime('%d/%m')}   post {x['post']}: {x['titolo']}")
    if not sett:
        t += ["", "Nessun post sui dati in calendario questa settimana."]
    t += ["", "Te li ricordo la mattina stessa, con immagine e didascalia."]
    manda("\n".join(t)); inviati += 1

# ------------------------------------------------ il post di oggi
oggi_r = [x for x in righe if x["data"] == oggi_s]
for x in oggi_r:
    n = x["post"]
    manda(f"Oggi si pubblica: post {n} - {x['titolo']}.\nQui sotto immagine e didascalia.")
    inviati += 1
    img = sorted(glob.glob(os.path.join(POST, f"post_{n}_*.png")))
    if img:
        manda_file(img[0]); inviati += 1
    else:
        p = blocco(n, "1. PROMPT PER CHATGPT")
        if p:
            manda("Immagine da generare in ChatGPT con questo prompt:"); inviati += 1
            manda(p); inviati += 1
    d = blocco(n, "2. DIDASCALIA")
    if d:
        manda(d); inviati += 1

# ------------------------------------------------ i due post automatici
if not oggi_r:
    if oggi.weekday() == 1:
        manda("Oggi alle 17:00 arriva il post del consuntivo."); inviati += 1
    elif oggi.weekday() == 2:
        manda("Oggi alle 16:00 arriva il post della partita della settimana."); inviati += 1

print(f"messaggi inviati: {inviati}")
