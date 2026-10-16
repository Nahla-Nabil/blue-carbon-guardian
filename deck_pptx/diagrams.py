"""The two README diagrams (workflow flowchart + 'how a user receives it' sequence) rendered with Mermaid in the deck's calm palette,
transparent background, 3x resolution -> deck_pptx/build/assets/diagram_workflow.png, diagram_sequence.png.
Same content as README.md section 4. Run from the repository root: python deck_pptx/diagrams.py  (needs playwright + internet for the Mermaid CDN)
"""
import pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent / "build" / "assets"; OUT.mkdir(parents=True, exist_ok=True)

THEME = """%%{init: {"theme":"base","themeVariables":{"fontFamily":"Segoe UI, Arial","fontSize":"20px","background":"transparent",
"primaryColor":"#17304F","primaryTextColor":"#E8EEF6","primaryBorderColor":"#7F9FC6","lineColor":"#93AFCF","secondaryColor":"#1D3A5E","tertiaryColor":"#132A46",
"actorBkg":"#17304F","actorBorder":"#7F9FC6","actorTextColor":"#E8EEF6","actorLineColor":"#5E7DA3","signalColor":"#A9C1DD","signalTextColor":"#E1E9F3",
"labelBoxBkgColor":"#22406A","labelBoxBorderColor":"#7F9FC6","labelTextColor":"#E8EEF6","loopTextColor":"#E1E9F3","noteBkgColor":"#22406A","noteTextColor":"#E8EEF6",
"activationBkgColor":"#22406A","activationBorderColor":"#7F9FC6","sequenceNumberColor":"#0B1B30","edgeLabelBackground":"#0F2440"}}}%%"""

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
    classDef step fill:#17304F,stroke:#7F9FC6,color:#E8EEF6,stroke-width:1.5px
    classDef core fill:#2B4F7E,stroke:#A9C1DD,color:#FFFFFF,stroke-width:2px
    classDef alert fill:#4A3240,stroke:#D9A0A8,color:#FBECEE,stroke-width:1.5px
    classDef out fill:#3B3A2C,stroke:#D8BE84,color:#F6EED9,stroke-width:2px
    classDef side fill:#132A46,stroke:#5E7DA3,color:#C9D6E6,stroke-width:1px
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
