"""Reader's guide. Written once; re-run only if the text changes."""
import os

ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Report Football")
CSS = """
body{font-family:-apple-system,Helvetica,Arial,sans-serif;background:#fff;color:#111;margin:0;padding:12px 18px;font-size:16px;line-height:1.5;max-width:46em}
h1{font-size:22px;margin:10px 0 4px} h2{font-size:18px;margin:26px 0 6px;padding-top:10px;border-top:1px solid #ddd}
p{margin:8px 0}
.oss{border-left:4px solid #888;background:#f1f1f1;padding:8px 12px;border-radius:4px;margin:8px 0}
.mod{border-left:4px solid #1a73e8;background:#e8f0fe;padding:8px 12px;border-radius:4px;margin:8px 0}
.ctl{border-left:4px solid #f57c00;background:#fff3e0;padding:8px 12px;border-radius:4px;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:15px;margin:10px 0}
td,th{border-bottom:1px solid #d6d6d6;padding:7px 8px;text-align:left;vertical-align:top}
th{font-weight:600;font-size:14px} td:first-child{font-weight:600;width:34%}
.nota{font-size:13px;color:#555}
"""

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>How to read the report</title>
<style>{CSS}</style></head><body>

<h1>How to read the report</h1>

<h2>The structure</h2>
<p>Every game has three blocks, told apart by colour. The split keeps raw data separate from anything
done to it.</p>
<div class="oss"><b>Grey &middot; Observed data.</b> Counted and nothing else: record, points, play
statistics, head to head, odds, forecast.</div>
<div class="mod"><b>Blue &middot; Estimates.</b> Probabilities worked out from the market line. There is
arithmetic here, and it should be read as an estimate.</div>
<div class="ctl"><b>Orange &middot; Historical check.</b> Games from past seasons in similar spots, and how
often each result actually came up.</div>

<h2>Team statistics</h2>
<p>Each row has two columns, the current season and the one before, with the number of games behind
each. Early in the year the left column swings hard: read it next to the right one and next to the
league averages printed under the table.</p>
<table>
<tr><th>Stat</th><th>What it tells you</th></tr>
<tr><td>Record, points per game</td><td>Wins and losses, points scored and allowed. Points cover every
game played, including ones whose play-by-play has not posted yet, so the game count can differ by one
from the rows below.</td></tr>
<tr><td>Offensive plays per game</td><td>Runs and passes. League average around 60. This is tempo, not
quality: more plays tends to mean more scoring.</td></tr>
<tr><td>Drives per game</td><td>How many possessions the offense gets. League average around 11. Drives
alternate, so the two teams in a game end up close. A low number means long drives &mdash; theirs or the
opponent's.</td></tr>
<tr><td>Share of plays that are passes</td><td>League average around 57%. Shows how much of a team's
offense travels through the air, which matters for how conditions affect them.</td></tr>
<tr><td>EPA per play, offense</td><td>How much each play improves the team's expected points, given the
situation: 3 yards on third-and-2 is worth far more than 3 yards on third-and-10. Positive is
good.</td></tr>
<tr><td>EPA per play allowed, defense</td><td>The same from the other side. Here <b>negative is
good</b>: the defense is giving up fewer expected points than an average one would.</td></tr>
<tr><td>Points per drive</td><td>League average around 2.1. Counts offensive touchdowns and field goals
only. Read it with drives per game: a team can score heavily per drive and get few of them, or the
reverse.</td></tr>
<tr><td>Share of points from touchdowns</td><td>How much of the scoring comes from touchdowns rather
than field goals.</td></tr>
<tr><td>Offense and defense, adjusted</td><td>See below.</td></tr>
<tr><td>Covered the spread / Over in their games</td><td>How often this season. They sit at the bottom
on purpose: over this few games they are close to pure noise, and historically they say nothing about
how the next ones will go.</td></tr>
</table>
<p class="nota">The number in brackets next to EPA and the adjusted figures is the rank out of 32.</p>

<h2>Adjusted for opponents faced</h2>
<p>Raw EPA says how well a team has played, not who against. Four or five games in, that gap is wide:
an offense that has drawn four weak defenses looks far better than it is.</p>
<p>This row corrects for it. It is an estimate of real offensive and defensive strength, produced by
rating every team together across the last four seasons: each one is weighed for how strong its
opponents were, recent games count more than old ones, and teams with little evidence are pulled
toward the average rather than taken at face value.</p>
<p>The figure is the deviation from league average in EPA per play, so zero means an average team, and
again, for defense negative is good. The values are much tighter than raw EPA, and that is deliberate:
they reflect how little is really known a few weeks into a season. <b>When this number and the raw EPA
tell different stories, the gap is schedule.</b></p>
<p class="nota">How fast recent games are weighted is not a guess: several decay rates were tested
against twenty years of games, and the one that predicted future results best was kept. It came out
slower than instinct suggests.</p>

<h2>The odds</h2>
<table>
<tr><th>Column</th><th>What it tells you</th></tr>
<tr><td>Odds</td><td>In decimal format. Total return per unit staked, stake included.</td></tr>
<tr><td>Implied</td><td>One divided by the odds. The probability those odds appear to express &mdash;
but inflated: the two sides add up to more than 100%.</td></tr>
<tr><td>No-vig</td><td>The same figure with the book's cut stripped out. This is the estimate the market
is actually making, and the one to compare your own view against.</td></tr>
<tr><td>Hold</td><td>How far past 100% the two sides add up. In the NFL it usually runs 2% to 5%: the
lower it is, the sharper the price.</td></tr>
</table>

<h2>The estimates (blue block)</h2>
<p>The win, cover and push probabilities do not come from a model of ours. They are derived from the
market line, by taking every past game with a line close to today's and looking at how they finished,
rather than assuming a smooth curve.</p>
<p>That distinction is not cosmetic. Points arrive almost entirely in blocks of 3 and 7, so final
margins pile up on those numbers: across regular season games from 1999 to 2025 the margin was exactly
3 in <b>1,049 of 6,999 games</b> and exactly 7 in 637, against 288 for a margin of 2 and 265 for a
margin of 8. At a line of 3 a push lands roughly once in ten games; at 3.5 it cannot happen at all.
That is why the report also prints the chance the favorite wins by <i>exactly</i> the margins sitting
either side of the line: it shows what that half point is worth.</p>
<p>Next to the win probability from the spread sits the one from the moneyline. They normally land
within a point or two of each other. When they drift apart, the two markets are not saying the same
thing.</p>

<h2>The forecast</h2>
<p>The report carries wind, temperature and chance of rain at kickoff for outdoor stadiums. Venues with
a retractable roof still get a forecast, but whether the roof is open is decided on game day.</p>
<p>Wind comes with a range: <i>14 mph, so realistically between 11 and 17 (forecast made 3 days out,
typical error &plusmn;3.2)</i>. That range is measured, not decorative. Across NFL stadiums we checked
how much a wind forecast shifts as kickoff approaches: three days out the typical swing is about 3 mph,
one day out it drops to 2.4, seven days out it climbs to 4.4. The wider the range, the less the number
can carry.</p>
<p class="nota">That range measures how much the weather model changes its mind on the way to kickoff,
not how far it lands from what actually blows. The true uncertainty is somewhat larger.</p>
<p>The game day update carries the final forecasts, and it matters: three days out, barely more than
half the games that look windy still are at kickoff.</p>

<h2>The historical check (orange block)</h2>
<p>Frequencies are always written as <b>"X of N"</b>, not just as a percentage. That is deliberate: "6
of 10" and "600 of 1,000" are the same percentage but not the same information. The first can flip with
one more game; the second cannot.</p>
<p>Where the report says <i>games with a similar line</i>, it means past games where the market set a
number close to today's, counted by how they finished. It is the most direct answer to the question:
when the market said this, what actually happened?</p>

<p class="nota">Sources: nflverse for results, play statistics and odds; Open-Meteo for forecasts.
All times Eastern.</p>

</body></html>"""

os.makedirs(ICLOUD, exist_ok=True)
os.makedirs("report", exist_ok=True)
for d in [os.path.join(ICLOUD, "GUIDA.html"), "report/GUIDA.html"]:
    with open(d, "w", encoding="utf-8") as f:
        f.write(HTML)
print("Guide saved:", os.path.join(ICLOUD, "GUIDA.html"))
