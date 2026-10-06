"""Pubblica nel canale Telegram l'annuncio della week.
Uso:  python annuncia.py report | update | recap
Lanciare dopo pubblica.py."""
import glob
import percorsi
import json
import os
import re
import sys
import requests

BASE = "https://keynumbersnfl-tech.github.io"
ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Report Football")
CONF = ".secrets/telegram.json"

tipo = sys.argv[1] if len(sys.argv) > 1 else "report"
if tipo not in ("report", "update", "recap"):
    print("Uso: python annuncia.py report | update | recap"); sys.exit(1)

MODELLO = {"report": "report.html", "update": "update-*.html", "recap": "recap.html"}
cartelle = [c for c in sorted(glob.glob(os.path.join(percorsi.DOCS, "w[0-9][0-9]")))
            if glob.glob(os.path.join(c, MODELLO[tipo]))]
if not cartelle:
    print(f"Nessuna week con {MODELLO[tipo]}."); sys.exit(1)
wk = int(os.path.basename(cartelle[-1])[1:])
url = f"{BASE}/w{wk:02d}/"

TESTI = {
    "report": (
        f"<b>Week {wk} report is up.</b>\n\n"
        "Every game: how both teams are actually playing once you adjust for the "
        "opponents they've faced, the forecast with its margin of error, and how "
        "similar lines have played out in past seasons.\n\n"
        "Free, no sign-up."),
    "update": (
        f"<b>Week {wk} — game day update.</b>\n\n"
        "Final forecasts, current lines, and who's on the injury report."),
    "recap": (
        f"<b>Week {wk} — how it went.</b>\n\n"
        "What the numbers said, what actually happened, and where they missed."),
}

c = ({"token": os.environ["TELEGRAM_TOKEN"], "canale": os.environ["TELEGRAM_CANALE"]}
     if os.environ.get("TELEGRAM_TOKEN") else json.load(open(CONF)))
api = f"https://api.telegram.org/bot{c['token']}"
r = requests.post(f"{api}/sendMessage", timeout=20, json={
    "chat_id": c["canale"],
    "text": f"{TESTI[tipo]}\n\n{url}",
    "parse_mode": "HTML"}).json()

if not r.get("ok"):
    print("Errore:", r); sys.exit(1)
mid = r["result"]["message_id"]
print(f"Pubblicato nel canale ({tipo}, week {wk}): {url}")

if tipo == "report":
    p = requests.post(f"{api}/pinChatMessage", timeout=20, json={
        "chat_id": c["canale"], "message_id": mid,
        "disable_notification": True}).json()
    print("Fissato in alto." if p.get("ok") else f"Non fissato: {p.get('description')}")
