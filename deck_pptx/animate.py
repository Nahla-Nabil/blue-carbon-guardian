"""Post-process the pptxgenjs deck: add a Morph transition (with a fade fallback for older PowerPoint) to every slide and
automatic, staggered entrance animations to every object named a<order><effect>_..., plus the title and kicker placeholders.
Animations start by themselves after the transition (no clicks needed during an 8-minute pitch).
Also fixes pptxgenjs' duplicate shape id for the slide-number placeholder.
Run from deck_pptx/:  python animate.py  [in.pptx] [out.pptx]
"""
import re, sys, zipfile, pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build" / "blue_carbon_guardian_final.pptx"
DST = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "build" / "animated.pptx"  # media.ps1 then adds the videos -> docs/
BASE, STEP = 250, 220  # ms: first delay after the transition, gap between animation groups

TRANSITION = ('<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
              '<mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" Requires="p159">'
              '<p:transition spd="slow" p14:dur="1200"><p159:morph option="byObject"/></p:transition></mc:Choice>'
              '<mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')

PRESET = {"fade": (10, 0), "float": (42, 0), "rise": (42, 0), "zoom": (53, 16), "pop": (53, 16), "wipe": (22, 8)}


class Ids:
    def __init__(self, start): self.n = start
    def __call__(self): self.n += 1; return self.n


def tgt(spid): return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'


def anim(nid, spid, attr, frm, to, dur):
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{nid()}" dur="{dur}" fill="hold"/>{tgt(spid)}'
            f'<p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>'
            f'<p:tav tm="0"><p:val><p:strVal val="{frm}"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="{to}"/></p:val></p:tav></p:tavLst></p:anim>')


def looping(nid, spid, fx, delay):
    """Effects that repeat for as long as the slide is shown: 'ping' (ring grows and fades, like a radar echo) and
    'drift' (object glides across the slide along a motion path, e.g. the satellite on the cover)."""
    if fx == "ping":
        cls, pid, dur = "emph", 6, 1600
        beh = (f'<p:animScale><p:cBhvr><p:cTn id="{nid()}" dur="{dur}" fill="hold"/>{tgt(spid)}</p:cBhvr><p:by x="160000" y="160000"/></p:animScale>'
               f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{nid()}" dur="{dur}" fill="hold"/>{tgt(spid)}'
               '<p:attrNameLst><p:attrName>style.opacity</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>'
               '<p:tav tm="0"><p:val><p:fltVal val="1"/></p:val></p:tav><p:tav tm="100000"><p:val><p:fltVal val="0"/></p:val></p:tav></p:tavLst></p:anim>')
    else:
        cls, pid, dur = "path", 0, 18000
        beh = (f'<p:animMotion origin="layout" path="M 0 0 L 1.12 -0.03 E" pathEditMode="relative" ptsTypes=""><p:cBhvr><p:cTn id="{nid()}" dur="{dur}" fill="hold"/>{tgt(spid)}'
               '<p:attrNameLst><p:attrName>ppt_x</p:attrName><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr></p:animMotion>')
    return (f'<p:par><p:cTn id="{nid()}" presetID="{pid}" presetClass="{cls}" presetSubtype="0" repeatCount="indefinite" fill="hold" grpId="0" nodeType="withEffect">'
            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>{beh}</p:childTnLst></p:cTn></p:par>')


def effect(nid, spid, fx, delay, graphic=False):
    if fx in ("ping", "drift"):
        return looping(nid, spid, fx, delay)
    pid, sub = PRESET[fx]
    dur = {"fade": 600, "float": 700, "rise": 1400, "zoom": 800, "pop": 450, "wipe": 900}[fx]
    beh = (f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>{tgt(spid)}'
           f'<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>')
    if fx == "wipe":
        beh += f'<p:animEffect transition="in" filter="wipe(left)"><p:cBhvr><p:cTn id="{nid()}" dur="{dur}"/>{tgt(spid)}</p:cBhvr></p:animEffect>'
    else:
        beh += f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="{min(dur, 700)}"/>{tgt(spid)}</p:cBhvr></p:animEffect>'
    if fx in ("float", "rise"):
        beh += anim(nid, spid, "ppt_y", "#ppt_y+" + ("0.03" if fx == "float" else "0.10"), "#ppt_y", dur)
    elif fx in ("zoom", "pop"):
        k = "0.85" if fx == "zoom" else "0.2"
        beh += anim(nid, spid, "ppt_w", f"#ppt_w*{k}", "#ppt_w", dur) + anim(nid, spid, "ppt_h", f"#ppt_h*{k}", "#ppt_h", dur)
    ease = ' decel="100000"' if fx != "wipe" else ""
    return (f'<p:par><p:cTn id="{nid()}" presetID="{pid}" presetClass="entr" presetSubtype="{sub}" fill="hold"{ease} grpId="0" nodeType="withEffect">'
            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>{beh}</p:childTnLst></p:cTn></p:par>')


def timing(items):
    """items: list of (delay_ms, spid, fx, is_graphic). One automatic group that starts when the slide starts."""
    nid = Ids(4)
    effects = "".join(effect(nid, spid, fx, d, g) for d, spid, fx, g in items)
    bld = "".join(f'<p:bldP spid="{spid}" grpId="0"/>' if not g else f'<p:bldGraphic spid="{spid}" grpId="0"><p:bldAsOne/></p:bldGraphic>'
                  for spid, g in dict(((s, g) for _, s, _, g in items)).items())
    return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            '<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{effects}</p:childTnLst></p:cTn></p:par>'
            '</p:childTnLst></p:cTn></p:par>'
            '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            f'</p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>{bld}</p:bldLst></p:timing>')


def process(xml):
    # 1) unique shape ids
    seen, mx = set(), max(int(i) for i in re.findall(r'<p:cNvPr id="(\d+)"', xml))
    def fix(m):
        nonlocal mx
        i = int(m.group(1))
        if i in seen:
            mx += 1; i = mx
        seen.add(i)
        return f'<p:cNvPr id="{i}"'
    xml = re.sub(r'<p:cNvPr id="(\d+)"', fix, xml)
    # 2) collect animated objects
    items = []
    for blk in re.findall(r"<p:sp>.*?</p:sp>", xml, re.S):
        m = re.search(r'<p:cNvPr id="(\d+)"', blk)
        if re.search(r'<p:ph[^>]*type="title"', blk): items.append((0, int(m.group(1)), "float", False))
        elif re.search(r'<p:ph[^>]*type="body"', blk) and "<a:t>" in blk: items.append((0, int(m.group(1)), "fade", False))
    for spid, name in re.findall(r'<p:cNvPr id="(\d+)" name="([az]\d+[a-z]+_[^"]*)"', xml):
        o, fx = re.match(r"[az](\d+)([a-z]+)_", name).groups()
        graphic = bool(re.search(rf'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{spid}"', xml))
        items.append((int(o), int(spid), fx, graphic))
    items = [(BASE + o * STEP, s, fx, g) for o, s, fx, g in sorted(items)]
    # 3) transition + timing after clrMapOvr
    add = TRANSITION + (timing(items) if items else "")
    xml = xml.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + add, 1)
    return xml, len(items)


zin = zipfile.ZipFile(SRC)
DST.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
    for it in zin.infolist():
        data = zin.read(it.filename)
        if re.fullmatch(r"ppt/slides/slide\d+\.xml", it.filename):
            xml, n = process(data.decode("utf-8"))
            data = xml.encode("utf-8")
            print(f"{it.filename}: {n} animated objects")
        zout.writestr(it, data)
print("wrote", DST)
