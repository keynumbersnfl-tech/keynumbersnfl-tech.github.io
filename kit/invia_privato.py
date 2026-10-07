"""Manda un file di testo nella chat privata, una parte per messaggio.
Le parti sono separate da una riga che contiene solo @@@
Uso: python kit/invia_privato.py file.txt"""
import percorsi
import json
import os
import sys
import requests

LIMITE = 3900

def credenziali():
    if os.environ.get("TELEGRAM_TOKEN") and os.environ.get("TELEGRAM_PRIVATA"):
        return os.environ["TELEGRAM_TOKEN"], os.environ["TELEGRAM_PRIVATA"]
    for p in (".secrets/telegram.json",
              os.path.expanduser("~/Desktop/Bolle test/files/nflkit/.secrets/telegram.json")):
        if os.path.exists(p):
            c = json.load(open(p))
            if "privata" not in c:
                raise SystemExit(f"manca la chat privata in {p}")
            return c["token"], c["privata"]
    raise SystemExit("credenziali Telegram non trovate")

token, chat = credenziali()
testo = open(sys.argv[1], encoding="utf-8").read()
parti = [p.strip() for p in testo.split("\n@@@\n") if p.strip()]

inviate = 0
for p in parti:
    for i in range(0, len(p), LIMITE):
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20,
                          json={"chat_id": chat, "text": p[i:i + LIMITE],
                                "disable_web_page_preview": True}).json()
        if not r.get("ok"):
            print("Errore:", r); sys.exit(1)
        inviate += 1
print(f"Inviati {inviate} messaggi nella chat privata.")
