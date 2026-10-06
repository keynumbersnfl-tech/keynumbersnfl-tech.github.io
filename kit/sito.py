"""Rebuilds the site index pages from whatever is in docs/."""
import glob
import html
import os
import re
import percorsi
from datetime import datetime

BASE = "https://keynumbersnfl-tech.github.io"
MESI = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
e = html.escape

CSS = """
body{font-family:-apple-system,Helvetica,Arial,sans-serif;background:#0E0E0E;color:#F5F5F5;
margin:0;padding:44px 20px;font-size:16px;line-height:1.5;display:flex;justify-content:center}
main{max-width:34em;width:100%}
h1{font-size:24px;margin:0 0 4px;font-weight:500}
h2{font-size:13px;letter-spacing:1.5px;text-transform:uppercase;color:#6A6A6A;
margin:34px 0 10px;font-weight:500}
p{color:#A0A0A0;margin:8px 0}
a{color:#F5F5F5;text-decoration:none}
ul{list-style:none;padding:0;margin:0}
li a{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
border-top:1px solid #262626;padding:15px 0}
li a:hover{color:#F5A623}
.quando{font-size:13px;color:#6A6A6A;white-space:nowrap}
.primo a{border-top:2px solid #F5A623;padding-top:17px}
.primo .tit{font-size:18px}
.nota{font-size:13px;color:#6A6A6A;margin-top:36px}
.back{font-size:13px;color:#6A6A6A;display:inline-block;margin-bottom:18px}
"""

def pagina(titolo, corpo):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(titolo)}</title><style>{CSS}</style></head>'
            f'<body><main>{corpo}</main></body></html>')

def data_breve(s):
    d = datetime.strptime(s, "%Y%m%d")
    return f"{MESI[d.month - 1]} {d.day}"

settimane = []
for cart in sorted(glob.glob(os.path.join(percorsi.DOCS, "w[0-9][0-9]"))):
    wk = int(os.path.basename(cart)[1:])
    voci = []
    if os.path.exists(os.path.join(cart, "report.html")):
        voci.append(("report.html", "Full week report", "all games", True))
    for p in sorted(glob.glob(os.path.join(cart, "update-*.html"))):
        g = re.search(r"update-(\d{8})", p).group(1)
        voci.append((os.path.basename(p), "Game day update", data_breve(g), False))
    if os.path.exists(os.path.join(cart, "recap.html")):
        voci.append(("recap.html", "How it went", "recap", False))
    if not voci:
        continue
    righe = ""
    for href, tit, quando, primo in voci:
        cl = ' class="primo"' if primo else ""
        tc = ' class="tit"' if primo else ""
        righe += (f'<li{cl}><a href="{href}"><span{tc}>{e(tit)}</span>'
                  f'<span class="quando">{e(quando)}</span></a></li>')
    corpo = (f'<a class="back" href="/">&larr; Key Numbers</a>'
             f'<h1>Week {wk}</h1><p>2026 season</p>'
             f'<h2>This week</h2><ul>{righe}</ul>'
             f'<h2>Start here</h2><ul>'
             f'<li><a href="/guide.html"><span>How to read the report</span>'
             f'<span class="quando">guide</span></a></li></ul>')
    with open(os.path.join(cart, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina(f"Week {wk} · Key Numbers", corpo))
    settimane.append((wk, len(voci)))
    print(f"week {wk}: {len(voci)} document(s)")

righe = ""
for wk, n in sorted(settimane, reverse=True):
    righe += (f'<li><a href="/w{wk:02d}/"><span>Week {wk}</span>'
              f'<span class="quando">{n} document{"s" if n > 1 else ""}</span></a></li>')
corpo = ('<h1>Key Numbers</h1><p>NFL matchup data, week by week.</p>'
         f'<h2>Reports</h2><ul>{righe or "<li><a>Coming soon</a></li>"}</ul>'
         '<h2>Start here</h2><ul>'
         '<li><a href="/guide.html"><span>How to read the report</span>'
         '<span class="quando">guide</span></a></li></ul>'
         '<p class="nota">Not betting advice. Just counts.</p>')
with open(os.path.join(percorsi.DOCS, "index.html"), "w", encoding="utf-8") as f:
    f.write(pagina("Key Numbers · NFL", corpo))
print("Index pages rebuilt.")
