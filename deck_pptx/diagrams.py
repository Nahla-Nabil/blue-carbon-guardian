"""The two README diagrams (workflow flowchart + 'how a user receives it' sequence) rendered with Mermaid in the deck's calm palette,
transparent background, 3x resolution -> deck_pptx/build/assets/diagram_workflow.png, diagram_sequence.png.
Same content as README.md section 4. Run from the repository root: python deck_pptx/diagrams.py  (needs playwright + internet for the Mermaid CDN)
"""
import pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent / "build" / "assets"; OUT.mkdir(parents=True, exist_ok=True)

THEME = """%%{init: {"theme":"base","themeVariables":{"fontFamily":"Segoe UI, Arial","fontSize":"20px","background":"transparent",
"primaryColor":"#EEF4FB","primaryTextColor":"#1B2B40","primaryBorderColor":"#7F9FC6","lineColor":"#6E8FB5","secondaryColor":"#E3EDF8","tertiaryColor":"#F5F8FC",
"actorBkg":"#E3EDF8","actorBorder":"#6E95C2","actorTextColor":"#1B2B40","actorLineColor":"#9AB3CF","signalColor":"#4F7BAA","signalTextColor":"#1B2B40",
"labelBoxBkgColor":"#D6E4F4","labelBoxBorderColor":"#6E95C2","labelTextColor":"#1B2B40","loopTextColor":"#3A4D63","noteBkgColor":"#F5ECD9","noteTextColor":"#1B2B40",
"activationBkgColor":"#D6E4F4","activationBorderColor":"#6E95C2","sequenceNumberColor":"#FFFFFF","edgeLabelBackground":"#FFFFFF"}}}%%"""

WORKFLOW = THEME + """
flowchart LR
    A["<b>Stands & 200 m cells</b><br/>WorldCover 2021, ≥ 3 ha<br/>interior pixels only"] --> B["<b>Sentinel-2 L2A</b><br/>778 dates 2020–26<br/>cloud mask"]
    B --> C["<b>Indices per stand & cell</b><br/>NDVI · red edge · moisture<br/>wetness"]
    C --> D["<b>Tide-aware robust model</b><br/>trend + season + tide<br/>refitted monthly"]
    D --> E{"<b>Alert</b><br/>stand ≤ −1.5σ<br/>OR any cell ≤ −3.5σ"}
    D --> F["<b>Condition</b><br/>last 12 months<br/>vs 2020–21"]
    E --> G["<b>Decision layer</b><br/>cell map · carbon at stake<br/>dashboard · site reports"]
    F --> G
    H["<b>Field carbon</b><br/>108 t C/ha"] --> G
    I["<b>Independent checks</b><br/>EnMAP · sub-metre captures"] -.-> G
    classDef step fill:#EEF4FB,stroke:#7F9FC6,color:#1B2B40,stroke-width:1.5px
    classDef core fill:#D6E6F7,stroke:#4F7BAA,color:#1B2B40,stroke-width:2px
    classDef alert fill:#F8E4E7,stroke:#C0606E,color:#5A2630,stroke-width:1.5px
    classDef out fill:#F5ECD9,stroke:#B08A3E,color:#4A3A16,stroke-width:2px
    classDef side fill:#F7F9FC,stroke:#9AAFC6,color:#3A4D63,stroke-width:1px
    class A,B,C,F step
    class D core
    class E alert
    class G out
    class H,I side
"""

SEQUENCE = THEME + """
sequenceDiagram
    participant S as Sentinel-2
    participant P as Blue Carbon Guardian
    participant A as Agency / developer
    participant I as Inspector
    S->>P: new scene every ~5 days
    P->>P: tide-aware model, stand + cells
    alt alert fires
        P->>P: check cells on sub-metre imagery
        P->>A: alert + cell map + carbon at stake
        A->>I: visit only flagged cells
    else no alert
        P->>A: monthly site report
    end
"""

PAGE = """<!doctype html><meta charset="utf-8"><body style="margin:0;background:transparent">
<div id="d" class="mermaid">{src}</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, securityLevel:"loose", flowchart:{{curve:"basis", padding:18, nodeSpacing:38, rankSpacing:52}},
sequence:{{actorMargin:60, messageMargin:58, width:180, height:70, messageFontSize:24, actorFontSize:24, noteFontSize:22, boxMargin:12, noteMargin:12, mirrorActors:false, useMaxWidth:false}}}});</script></body>"""

with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 2200, "height": 1400}, device_scale_factor=3)
    for name, src in (("diagram_workflow", WORKFLOW), ("diagram_sequence", SEQUENCE)):
        pg.set_content(PAGE.format(src=src)); pg.wait_for_selector("#d svg", timeout=30000); pg.wait_for_timeout(800)
        pg.locator("#d svg").screenshot(path=str(OUT / f"{name}.png"), omit_background=True)
        bb = pg.locator("#d svg").bounding_box(); print(name, round(bb["width"]), "x", round(bb["height"]))
    b.close()
