"""Deck v4 for the PoC submission guide: order title -> problem -> use case -> data -> approach (workflow) -> outputs -> validation & limits ->
impact -> next steps. Adds slides 'usecase', 'limits'; rewrites 'solution' as a workflow diagram; adds theme + country to the cover; renumbers."""
import json, os, re
os.chdir(os.path.join(os.path.dirname(__file__), "..", "deck_source"))
INK, MUTED, ACC, DARK = "#12302E", "#4B6461", "#0B7A66", "#0F2B29"


def eyebrow(s):
    return ("<p style=\"font-family:'IBM Plex Mono', 'Courier New', monospace; font-size:24px; font-weight:600; letter-spacing:2px; "
            f"text-transform:uppercase; color:{ACC}\">{s}</p>")


def sec(id_, bg, gap):
    return (f"<section id=\"{id_}\" data-transition=\"fade\" style=\"background:{bg}; color:{INK}; font-family:'IBM Plex Sans', Arial, sans-serif; "
            f"padding:128px 128px 160px; display:flex; flex-direction:column; gap:{gap}px\">")


FOOT = ('  <p style="position:absolute; left:128px; bottom:64px; font-size:24px; color:#4B6461">Blue Carbon Guardian &#183; Team T0006</p>\n'
        '  <p style="position:absolute; right:128px; bottom:64px; font-size:24px; color:#4B6461">00</p>')

# ---- use case -------------------------------------------------------------------------------------------------------------------------------
def ucard(who, decision, today):
    return (f'    <div style="display:flex; flex-direction:column; gap:12px; flex:1; background:#FFFFFF; border:1px solid #D8E3DF; border-radius:16px; padding:28px">\n'
            f'      <h3 style="font-size:30px; font-weight:700; color:{INK}; line-height:1.25">{who}</h3>\n'
            f'      <p style="font-size:22px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:{ACC}">Decision</p>\n'
            f'      <p style="font-size:25px; color:{INK}; line-height:1.4">{decision}</p>\n'
            f'      <p style="font-size:22px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:{ACC}">Today, without us</p>\n'
            f'      <p style="font-size:25px; color:{MUTED}; line-height:1.4">{today}</p>\n    </div>')


open("slides/usecase.html", "w", encoding="utf-8").write(f"""{sec("usecase", "#FBFBF8", 30)}
  <div style="display:flex; flex-direction:column; gap:14px">
    {eyebrow("Business use case")}
    <h2 style="font-size:58px; font-weight:700; line-height:1.12; color:{INK}">Who uses it, and for which decision</h2>
  </div>
  <div style="display:flex; flex-direction:row; gap:28px">
{ucard("Environment agencies", "Which stands to inspect this month? Is a protected stand intact?", "Periodic field surveys and one-off studies")}
{ucard("Planting &amp; carbon-project developers", "Is the carbon stock we report still there? Evidence for verification.", "Field plots and drone surveys, campaign by campaign")}
{ucard("Coastal developers &amp; regulators", "Did construction stay outside the mangrove line?", "Comparing two dated images by eye")}
  </div>
  <div style="background:{DARK}; border-radius:14px; padding:24px 32px">
    <p style="font-size:27px; color:#EAF3F0; line-height:1.45"><b>What they get:</b> a monthly alert per stand <i>and</i> per 200&#160;m cell, a map of where to look, the carbon at stake, and a site report &#8212; at about one false alarm per stand per year.</p>
  </div>
{FOOT}
  <aside>The product is decision support: it tells an inspector where to go first and gives a project developer independent evidence. It does not replace field verification; it decides where field verification is worth the cost.</aside>
</section>
""")

# ---- approach as a workflow diagram ---------------------------------------------------------------------------------------------------------
def step(n, title, body, dark=False):
    bg, tc, bc = (DARK, "#EAF3F0", "#9FC1BB") if dark else ("#FFFFFF", INK, MUTED)
    border = "" if dark else " border:1px solid #D8E3DF;"
    return (f'    <div style="display:flex; flex-direction:column; gap:10px; flex:1; background:{bg};{border} border-radius:14px; padding:22px 20px">\n'
            f"      <p style=\"font-family:'IBM Plex Mono', 'Courier New', monospace; font-size:22px; font-weight:600; color:{'#3FC0A4' if dark else ACC}\">{n}</p>\n"
            f'      <h3 style="font-size:26px; font-weight:700; color:{tc}; line-height:1.25">{title}</h3>\n'
            f'      <p style="font-size:21px; color:{bc}; line-height:1.4">{body}</p>\n    </div>')


ARROW = f'    <p style="font-size:36px; color:{ACC}; font-weight:700">&#8594;</p>'
open("slides/solution.html", "w", encoding="utf-8").write(f"""{sec("solution", "#FBFBF8", 28)}
  <div style="display:flex; flex-direction:column; gap:14px">
    {eyebrow("Approach")}
    <h2 style="font-size:58px; font-weight:700; line-height:1.12; color:{INK}">From satellite pixels to an inspection decision</h2>
  </div>
  <div style="display:flex; flex-direction:row; gap:12px; align-items:center">
{step("01", "Stands &amp; 200 m cells", "WorldCover 2021 mangrove patches &#8805; 3&#160;ha; interior pixels only")}
{ARROW}
{step("02", "Sentinel-2 series", "778 dates 2020&#8211;26; cloud mask; NDVI, red edge, SWIR moisture, wetness")}
{ARROW}
{step("03", "Tide-aware model", "Robust trend + season + <b>tide</b> terms, refitted monthly")}
{ARROW}
{step("04", "Alert &amp; condition", "Stand <b>OR</b> any cell, &#8776;1 false alarm per stand-year; vs 2020&#8211;21 baseline")}
{ARROW}
{step("05", "Decision layer", "Carbon at stake, cell map, dashboard &amp; site reports", dark=True)}
  </div>
  <div style="display:flex; flex-direction:row; gap:24px">
    <div style="display:flex; flex-direction:column; gap:8px; flex:1; background:#DDF0EA; border-radius:14px; padding:22px 28px">
      <p style="font-size:24px; font-weight:700; color:{INK}">Checks built in</p>
      <p style="font-size:23px; color:{INK}; line-height:1.45">EnMAP hyperspectral on the same dates &#183; dated sub-metre captures &#183; simulated losses against chance &#183; 65 unseen stands</p>
    </div>
    <div style="display:flex; flex-direction:column; gap:8px; flex:1; background:#FFFFFF; border:1px solid #D8E3DF; border-radius:14px; padding:22px 28px">
      <p style="font-size:24px; font-weight:700; color:{INK}">Problem statement</p>
      <p style="font-size:23px; font-style:italic; color:{INK}; line-height:1.45">&#8220;We monitor mangrove condition and carbon stock in Abu Dhabi, 2020&#8211;2026, so authorities and developers can decide where to inspect and verify carbon claims.&#8221;</p>
    </div>
  </div>
{FOOT}
  <aside>Five steps, all running on free data. The only non-standard step is the tide model in step 3 &#8212; that is what makes stand-level monitoring possible on Gulf tidal flats. Steps 1 to 5 are exactly what the notebook in our repository runs.</aside>
</section>
""")

# ---- limitations ----------------------------------------------------------------------------------------------------------------------------
def lim(t, b):
    return (f'    <div style="display:flex; flex-direction:column; gap:6px; background:#FFFFFF; border:1px solid #D8E3DF; border-radius:12px; padding:18px 24px">\n'
            f'      <p style="font-size:25px; font-weight:700; color:{INK}">{t}</p>\n      <p style="font-size:22px; color:{MUTED}; line-height:1.4">{b}</p>\n    </div>')


open("slides/limits.html", "w", encoding="utf-8").write(f"""{sec("limits", "#EEF3F1", 24)}
  <div style="display:flex; flex-direction:column; gap:12px">
    {eyebrow("Limitations")}
    <h2 style="font-size:54px; font-weight:700; line-height:1.12; color:{INK}">Where it breaks &#8212; and what we do not claim</h2>
  </div>
  <div style="display:flex; flex-direction:row; gap:20px">
    <div style="display:flex; flex-direction:column; gap:16px; flex:1">
{lim("Detection, not early warning", "Alerts fire as works happen. We never claim to see stress before it is visible.")}
{lim("10 m pixels", "Patches under ~0.6&#160;ha and young plantings are missed &#8212; Bahrain&#8217;s small stands included.")}
{lim("Imagery, not site visits", "Five conversions confirmed on dated sub-metre captures; not yet on permits or field records.")}
    </div>
    <div style="display:flex; flex-direction:column; gap:16px; flex:1">
{lim("Simulated losses", "Canopy-cover loss, not leaf stress; every detection rate shown next to its chance rate; &#177;7 points.")}
{lim("Hyperspectral", "EnMAP confirms our indices but was not a better classifier (F1 0.74 vs 0.72).")}
{lim("Carbon", "Area &#215; field density from four sites (2013&#8211;14): a stock with a range, never a sequestration rate.")}
    </div>
  </div>
  <p style="font-size:22px; color:{MUTED}">We withdrew our own first backtest figure (58% / 90%) when a null test showed its metric counted alerts already running.</p>
{FOOT}
  <aside>We name the limits before a judge does. Each one has a concrete next step in the roadmap: very-high-resolution or Satellite 813 data for small stands, partner records for confirmation, more EnMAP dates for leaf-level stress.</aside>
</section>
""")

# ---- cover: theme + country -----------------------------------------------------------------------------------------------------------------
p = "slides/cover.html"; t = open(p, encoding="utf-8").read()
a = "Arab Youth Space Hackathon &#183; Challenge 813 &#183; Team T0006</p>"
if a in t:
    t = t.replace(a, "Arab Youth Space Hackathon &#183; Challenge 813 &#183; Team T0006 &#183; Palestine</p>\n  <p style=\"font-size:26px; font-weight:600; color:#9FC1BB\">Theme: Ecosystem Health, Biodiversity &amp; Blue Carbon</p>")
open(p, "w", encoding="utf-8").write(t)

# ---- order, sections, renumber ---------------------------------------------------------------------------------------------------------------
order = ["cover", "problem", "usecase", "data", "solution", "innovation", "cells", "product", "validation-real", "hyperspectral",
         "validation-sim", "limits", "carbon", "business", "roadmap", "team"]
d = json.load(open("deck.json", encoding="utf-8")); d["order"] = order
d["sections"] = {
    "s1": {"description": "Title, the problem and who uses the product for which decision.", "start": "cover"},
    "s2": {"description": "Data (incl. EnMAP hyperspectral) and the approach as a workflow, with its two technical innovations.", "start": "data"},
    "s3": {"description": "Example outputs: the dashboard, five real conversions confirmed at sub-metre, the hyperspectral check.", "start": "product"},
    "s4": {"description": "Validation against chance and out of sample, and the limitations.", "start": "validation-sim"},
    "s5": {"description": "Impact (carbon, business) and next steps for incubation; the team.", "start": "carbon"}}
json.dump(d, open("deck.json", "w", encoding="utf-8"), indent=2)
for n, sid in enumerate(order, start=1):
    p = f"slides/{sid}.html"; t = open(p, encoding="utf-8").read()
    t = re.sub(r'(right:128px; bottom:64px; font-size:24px; color:#4B6461">)\d+(</p>)', rf"\g<1>{n:02d}\g<2>", t)
    open(p, "w", encoding="utf-8").write(t)
print("order:", order)
