// Final-judging deck as PowerPoint: light calm content slides, soft-blue cover and close, glass cards, Morph transitions and entrance animations.
// Content and numbers = docs/final_deck.pdf (scripts/deck_final.py); speaker notes = docs/pitch_script.md.
// Pipeline (run from deck_pptx/):  python assets.py  ->  node build.js  ->  python animate.py
// Objects whose name starts with a<order><effect>_ (e.g. "a2float_card") get an entrance animation in animate.py;
// objects named "!!glow*" are matched between slides by Morph, so the soft light drifts as the slides change.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const lu = require("react-icons/lu");

const ROOT = path.resolve(__dirname, "..");
const A = (f) => path.join(__dirname, "build", "assets", f);
const IMG = (f) => path.join(ROOT, "deck_source", "images", f);
const OUT = path.join(__dirname, "build", "blue_carbon_guardian_final.pptx");

// ---- palettes: LIGHT for content slides, HERO (soft medium blue) for the cover and the closing slide ----
// TEAL = accent blue, TEAL_L = strong accent (names kept from v1); GOLD = key numbers; CORAL = loss.
const LIGHT_P = { PANEL: "FFFFFF", LINE: "D3E0EE", TXT: "1B2B40", MUTED: "5F738A", TEAL: "3F6E9E", TEAL_L: "2F5D8F", GOLD: "A9813A", CORAL: "BE5F6D", BLUE: "5C8DB8", SH: 0.12 };
const HERO_P = { PANEL: "1E3D63", LINE: "7FA2CA", TXT: "FFFFFF", MUTED: "D5E2F0", TEAL: "BCD3EC", TEAL_L: "E3EDF8", GOLD: "F1D9A0", CORAL: "F4BCC4", BLUE: "C7DCF0", SH: 0.25 };
let PANEL, LINE, TXT, MUTED, TEAL, TEAL_L, GOLD, CORAL, BLUE, SH;
const usePalette = (q) => ({ PANEL, LINE, TXT, MUTED, TEAL, TEAL_L, GOLD, CORAL, BLUE, SH } = q);
usePalette(LIGHT_P);
const HEAD = "Segoe UI Semibold", BODY = "Segoe UI", LIGHT = "Segoe UI Light";
const NOTES = JSON.parse(fs.readFileSync(path.join(__dirname, "notes.json"), "utf8"));

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Nahla Nabil";
pres.title = "Blue Carbon Guardian - final judging";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

// ---- layouts: three backgrounds share one frame (title, kicker, footer, slide number) ----
const frame = (bg) => ({
  background: { path: A(bg) },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.42, w: 12.1, h: 0.36, fontFace: HEAD, fontSize: 12, color: TEAL, charSpacing: 3, margin: 0, align: "left" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.78, w: 12.1, h: 0.85, fontFace: HEAD, fontSize: 34, color: TXT, margin: 0, valign: "top", align: "left" }, text: "" } },
    { text: { text: "Blue Carbon Guardian   ·   Team Blue Athar", options: { x: 0.6, y: 7.02, w: 6, h: 0.3, fontFace: BODY, fontSize: 10, color: "8A9BB0", margin: 0 } } },
  ],
  slideNumber: { x: 12.23, y: 7.02, w: 0.5, h: 0.3, fontFace: HEAD, fontSize: 10, color: TEAL, align: "right" },
});
pres.defineSlideMaster({ title: "OCEAN_A", ...frame("bg_light_a.png") });
pres.defineSlideMaster({ title: "OCEAN_B", ...frame("bg_light_b.png") });
pres.defineSlideMaster({ title: "OCEAN_C", ...frame("bg_light_c.png") });
pres.defineSlideMaster({ title: "HERO", background: { path: A("bg_hero.png") }, objects: [] });

// ---- helpers ----
const iconCache = {};
async function iconPng(name, color = TEAL_L) {
  const key = name + color;
  if (!iconCache[key]) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(lu[name], { size: 256, color: "#" + color, strokeWidth: 1.6 }));
    iconCache[key] = "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
  }
  return iconCache[key];
}
const shadow = () => ({ type: "outer", color: "1B2B40", blur: 12, offset: 3, angle: 90, opacity: SH });
function card(s, name, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    objectName: name, x, y, w, h, rectRadius: o.r ?? 0.14,
    fill: { color: o.fill ?? PANEL, transparency: o.tr ?? 18 }, line: { color: o.line ?? LINE, width: o.lw ?? 0.75 }, shadow: o.noShadow ? undefined : shadow(),
  });
}
async function iconCircle(s, name, icon, x, y, d = 0.56, col = TEAL) {
  s.addShape(pres.shapes.OVAL, { objectName: name + "_c", x, y, w: d, h: d, fill: { color: col, transparency: 82 }, line: { color: col, width: 1 } });
  s.addImage({ objectName: name + "_i", data: await iconPng(icon, col === TEAL ? TEAL_L : col), x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52 });
}
const T = (s, name, text, x, y, w, h, o = {}) =>
  s.addText(text, { objectName: name, x, y, w, h, isTextBox: true, margin: 0, fontFace: o.face ?? BODY, fontSize: o.size ?? 14, color: o.color ?? TXT,
    bold: o.bold, align: o.align ?? "left", valign: o.valign ?? "top", charSpacing: o.cs, lineSpacingMultiple: o.ls ?? 1.05, italic: o.italic, fit: "none" });
const glows = (s, a, b) => {
  s.addImage({ objectName: "!!glow1", path: A("glow_cyan.png"), x: a[0], y: a[1], w: a[2], h: a[2], transparency: 62 });
  s.addImage({ objectName: "!!glow2", path: A("glow_blue.png"), x: b[0], y: b[1], w: b[2], h: b[2], transparency: 65 });
};
function slide(master, kicker, title, glowA, glowB, key) {
  const s = pres.addSlide({ masterName: master });
  glows(s, glowA, glowB);
  if (kicker) s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
  if (title) s.addText(title, { placeholder: "title" });
  s.addNotes(NOTES[key] ?? "Backup slide: play the demo only if the judges ask for it.");
  return s;
}
const label = (s, name, text, x, y, w, color = TEAL) => T(s, name, text.toUpperCase(), x, y, w, 0.28, { face: HEAD, size: 11, color, cs: 3 });
const pill = (s, name, text, x, y, w, o = {}) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: name + "_bg", x, y, w, h: o.h ?? 0.4, rectRadius: 0.2, fill: { color: o.fill ?? TEAL, transparency: o.tr ?? 85 }, line: { color: o.line ?? TEAL, width: 0.75 } });
  T(s, name, text, x, y, w, o.h ?? 0.4, { size: o.size ?? 12, color: o.color ?? TEAL_L, align: "center", valign: "middle", face: HEAD });
};

(async () => {
  // =============== 1 · COVER ===============
  {
    usePalette(HERO_P);
    const s = pres.addSlide({ masterName: "HERO" });
    glows(s, [7.4, -2.6, 7.5], [-3.2, 3.6, 7]);
    s.addNotes(NOTES.cover);
    const vw = 5.15, vh = vw * 1120 / 1280;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a3zoom_vframe", x: 7.65 - 0.06, y: 1.25 - 0.06, w: vw + 0.12, h: vh + 0.12, rectRadius: 0.1, fill: { color: "0A1E3C" }, line: { color: "8FB4DE", width: 1.25 }, shadow: shadow() });
    s.addImage({ objectName: "vid_cover", path: path.join(__dirname, "build", "media", "cover_scan.png"), x: 7.65, y: 1.25, w: vw, h: vh });
    s.addImage({ objectName: "z0drift_sat", data: await iconPng("LuSatellite", "CFE6FF"), x: -0.7, y: 0.32, w: 0.42, h: 0.42 });
    T(s, "a0fade_kick", "ARAB YOUTH SPACE HACKATHON 2026  ·  CHALLENGE 813  ·  FINAL", 0.7, 1.3, 8.2, 0.32, { face: HEAD, size: 11, color: TEAL, cs: 2 });
    T(s, "a1float_title", "Blue Carbon Guardian", 0.66, 1.72, 8.2, 1.0, { face: HEAD, size: 46 });
    T(s, "a1float_sub", "Tide-aware satellite monitoring for Gulf mangroves —\nfrom alert to evidence.", 0.7, 2.85, 6.6, 0.85, { face: LIGHT, size: 21, color: "D4E2EE" });
    pill(s, "a2fade_team", "Team Blue Athar  ·  الأثر الأزرق", 0.7, 3.95, 3.05);
    pill(s, "a2fade_theme", "Theme: Ecosystem Health, Biodiversity & Blue Carbon", 0.7, 4.47, 4.25, { fill: BLUE, line: BLUE, color: "CFE4FF" });
    const k = [["91", "stands monitored"], ["5", "conversions confirmed"], ["73 %", "partial loss caught (chance 13 %)"], ["≈ 1", "false alarm per stand-year"]];
    for (let i = 0; i < 4; i++) {
      const x = 0.7 + i * 1.66;
      card(s, `a4float_k${i}`, x, 5.12, 1.55, 1.3, { tr: 30 });
      T(s, `a4float_k${i}n`, k[i][0], x + 0.16, 5.22, 1.3, 0.6, { face: LIGHT, size: 32, color: i === 1 ? CORAL : GOLD });
      T(s, `a4float_k${i}t`, k[i][1], x + 0.16, 5.8, 1.3, 0.55, { size: 11, color: MUTED });
    }
    T(s, "a5fade_name", "Nahla Nabil  ·  Bahrain", 0.7, 6.7, 5, 0.35, { face: HEAD, size: 16, color: "D4E2EE" });
    s.addImage({ objectName: "a5fade_fae", path: path.join(__dirname, "flag_ae.png"), x: 7.65, y: 6.1, w: 0.48, h: 0.24 });
    T(s, "a5fade_fael", "Study area: Abu Dhabi, UAE", 8.2, 6.02, 2.6, 0.4, { size: 12, color: "D4E2EE", valign: "middle" });
    s.addImage({ objectName: "a5fade_fbh", path: path.join(__dirname, "flag_bh.png"), x: 10.55, y: 6.1, w: 0.4, h: 0.24 });
    T(s, "a5fade_fbhl", "Built in Bahrain", 11.02, 6.02, 1.8, 0.4, { size: 12, color: "D4E2EE", valign: "middle" });
    usePalette(LIGHT_P);
  }

  // =============== 2 · TEAM (about me, right after the cover) ===============
  {
    const s = slide("OCEAN_B", "The team", "One engineer, every role — delivered in the open", [-2.4, 2.4, 6.5], [9.4, -3, 6], "team");
    card(s, "a1float_panel", 0.6, 1.85, 4.55, 4.9, { fill: "E8F0F9", tr: 8 });
    s.addShape(pres.shapes.OVAL, { objectName: "a1float_avring", x: 0.8, y: 2.02, w: 1.32, h: 1.32, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 2 } });
    s.addImage({ objectName: "a1float_av", path: path.join(__dirname, "nahla.png"), x: 0.85, y: 2.07, w: 1.22, h: 1.22 });
    T(s, "a1float_name", "Nahla Nabil", 2.28, 2.1, 2.8, 0.45, { face: HEAD, size: 22 });
    T(s, "a1float_role", "Team lead · AI engineer · IEEE researcher", 2.28, 2.55, 2.8, 0.5, { size: 11, color: MUTED });
    T(s, "a1float_ctry", "Bahrain", 2.28, 2.84, 2.8, 0.28, { size: 11, color: MUTED });
    label(s, "a2fade_l0", "Education", 0.88, 3.42, 4);
    T(s, "a2fade_edu", [{ text: "BSc Artificial Intelligence", options: { bold: true } }, { text: " · Arab Open University, Bahrain · final semester · First-Class Honours standing" }], 0.88, 3.66, 4.1, 0.5, { size: 11.5 });
    label(s, "a2fade_l1", "Relevant expertise", 0.88, 4.24, 4);
    s.addText(["2 IEEE papers (ICCA 2025, ICAISET 2026): federated learning for industrial IoT; random-forest audit of GCC sustainability",
      "AI & LLM product engineering (Doo Bahrain; FlyRank backend AI)", "Machine learning, computer vision (deepfake detection), Python geospatial stack"].map((t, i, a) =>
      ({ text: t, options: { bullet: { indent: 12 }, breakLine: i < a.length - 1 } })),
      { objectName: "a2fade_skills", x: 0.88, y: 4.5, w: 4.15, h: 1.4, fontFace: BODY, fontSize: 10.5, color: TXT, paraSpaceAfter: 3, margin: 0, valign: "top", isTextBox: true });
    label(s, "a3fade_l2", "Community", 0.88, 6.0, 4);
    T(s, "a3fade_comm", "NASA Space Apps Challenge local lead (Manama): organising and mentoring space-data teams", 0.88, 6.22, 4.15, 0.45, { size: 10 });
    const roles = [["LuTarget", "Project lead & owner", "problem framing, user needs, scope, every claim"],
      ["LuSatellite", "EO data engineer", "778 Sentinel-2 dates, EnMAP reader, sub-metre checks"],
      ["LuLineChart", "Modelling & statistics", "tide-aware model, stand + cell alert, calibration"],
      ["LuShieldCheck", "Validation & integrity", "real events, simulations, unseen stands"],
      ["LuLayers", "Product & delivery", "dashboard, website, site reports, notebook"],
      ["LuDollarSign", "Business & impact", "customers, pricing hypotheses, carbon ranges"]];
    label(s, "a1fade_l4", "Roles & responsibilities in this project", 5.45, 1.85, 7);
    for (let i = 0; i < 6; i++) {
      const x = 5.45 + (i % 2) * 3.7, y = 2.22 + Math.floor(i / 2) * 1.3, o = 2 + Math.floor(i / 2);
      card(s, `a${o}float_r${i}`, x, y, 3.56, 1.15);
      await iconCircle(s, `a${o}float_r${i}ic`, roles[i][0], x + 0.2, y + 0.29, 0.56);
      T(s, `a${o}float_r${i}t`, roles[i][1], x + 0.92, y + 0.18, 2.5, 0.36, { face: HEAD, size: 14 });
      T(s, `a${o}float_r${i}d`, roles[i][2], x + 0.92, y + 0.55, 2.5, 0.5, { size: 12, color: MUTED });
    }
    card(s, "a5float_gap", 5.45, 6.12, 7.26, 0.63, { fill: TEAL, tr: 86, line: TEAL });
    T(s, "a5float_gapt", [{ text: "Incubation gap we will close:  ", options: { bold: true, color: TEAL_L } }, { text: "a mangrove ecologist mentor · a restoration or agency partner · a GIS analyst" }], 5.7, 6.12, 6.9, 0.63, { size: 13, valign: "middle" });
  }

  // =============== 2 · PROBLEM ===============
  {
    const s = slide("OCEAN_A", "The problem", "Restoration is scaling faster than monitoring", [8.8, -2.2, 6], [-2.5, 4.2, 6], "problem");
    const st = [["100 M", "UAE mangrove pledge by 2030", "COP26, 2021 · Abu Dhabi Mangrove Initiative"], ["100 M+", "Saudi mangrove pledge by 2030", "Saudi Green Initiative"], ["Feb 2026", "first GCC mangrove monitoring guide", "EAD + IUCN Mangrove Specialist Group"]];
    for (let i = 0; i < 3; i++) {
      const y = 1.85 + i * 1.22;
      card(s, `a${i + 1}float_s${i}`, 0.6, y, 5.9, 1.08);
      T(s, `a${i + 1}float_s${i}n`, st[i][0], 0.85, y + 0.2, 2.1, 0.7, { face: LIGHT, size: 32, color: GOLD, valign: "middle" });
      T(s, `a${i + 1}float_s${i}t`, st[i][1], 3.0, y + 0.2, 3.35, 0.4, { face: HEAD, size: 14 });
      T(s, `a${i + 1}float_s${i}c`, st[i][2], 3.0, y + 0.62, 3.35, 0.3, { size: 11, color: MUTED });
    }
    card(s, "a4float_today", 0.6, 5.55, 5.9, 1.2, { fill: "E8F0F9", tr: 5 });
    T(s, "a4float_todayt", [{ text: "TODAY  ", options: { bold: true, color: CORAL, fontFace: HEAD } }, { text: "field surveys and one-off studies, no standing alert.", options: { breakLine: true } },
      { text: "WE SOLVE  ", options: { bold: true, color: TEAL_L, fontFace: HEAD } }, { text: "a calibrated alert every ~5 days that says where to inspect and what carbon is at stake." }], 0.85, 5.6, 5.45, 1.1, { size: 13, valign: "middle", ls: 1.15 });
    label(s, "a1fade_l", "This is happening now  ·  stand 5, Abu Dhabi", 6.95, 1.85, 5.8, CORAL);
    const ch = [["s2_stand5_2021-11.png", "Nov 2021 · intact", "3F6E9E"], ["s2_stand5_2022-10.png", "Oct 2022 · works start, alert fires", "B5535F"], ["s2_stand5_2023-06.png", "Jun 2023 · canals cut", "3F6E9E"], ["s2_stand5_2026-05.png", "May 2026 · development", "3F6E9E"]];
    for (let i = 0; i < 4; i++) {
      const x = 6.95 + (i % 2) * 2.93, y = 2.22 + Math.floor(i / 2) * 2.2, o = 2 + i;
      s.addImage({ objectName: `a${o}zoom_c${i}`, path: IMG(ch[i][0]), x, y, w: 2.8, h: 2.05, sizing: { type: "cover", w: 2.8, h: 2.05 }, rounding: false });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a${o}zoom_c${i}lb`, x: x + 0.1, y: y + 0.1, w: i === 1 ? 2.6 : 1.85, h: 0.32, rectRadius: 0.08, fill: { color: ch[i][2], transparency: 5 }, line: { type: "none" } });
      T(s, `a${o}zoom_c${i}lt`, ch[i][1], x + 0.18, y + 0.1, i === 1 ? 2.5 : 1.75, 0.32, { face: HEAD, size: 11, valign: "middle", color: "FFFFFF" });
    }
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a7ping_alert", x: 9.98, y: 2.32, w: 2.6, h: 0.32, rectRadius: 0.08, fill: { type: "none" }, line: { color: CORAL, width: 2 } });
    T(s, "a6fade_cap", "Sentinel-2 true colour (contains modified Copernicus Sentinel data). Our alert began on 25 Oct 2022, during the works.", 6.95, 6.47, 5.8, 0.3, { size: 11, color: MUTED });
  }

  // =============== 3 · PRODUCT ===============
  {
    const s = slide("OCEAN_B", "Example output · the product", "From signal to decision, in one screen", [8.6, -3, 6.5], [-2.8, 3.2, 6], "product");
    const bx = 0.6, by = 1.85, bw = 7.55, bh = bw * 1500 / 2400;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a1zoom_bf", x: bx, y: by, w: bw, h: bh + 0.34, rectRadius: 0.1, fill: { color: "E9EFF6" }, line: { color: LINE, width: 1 }, shadow: shadow() });
    ["FF5F57", "FEBC2E", "28C840"].forEach((c, i) => s.addShape(pres.shapes.OVAL, { objectName: `a1zoom_dot${i}`, x: bx + 0.16 + i * 0.2, y: by + 0.11, w: 0.12, h: 0.12, fill: { color: c }, line: { type: "none" } }));
    T(s, "a1zoom_url", "nahla-nabil.github.io/blue-carbon-guardian", bx + 0.9, by + 0.04, 5, 0.26, { size: 10, color: MUTED, valign: "middle" });
    s.addImage({ objectName: "vid_product", path: path.join(__dirname, "build", "media", "website.png"), x: bx + 0.04, y: by + 0.34, w: bw - 0.08, h: bh - 0.05 });
    const F = [["LuBell", "One alert", "stand OR any 200 m cell, calibrated"], ["LuLayoutGrid", "Where to look", "a 200 m cell map for the inspector"],
      ["LuActivity", "Condition", "last 12 months vs own 2020–21 baseline"], ["LuLeaf", "Carbon at stake", "stock with a range, from field data"], ["LuFileText", "Site report", "one page per stand, every number traced"]];
    for (let i = 0; i < 5; i++) {
      const y = 1.9 + i * 0.84, o = 2 + i;
      await iconCircle(s, `a${o}float_f${i}`, F[i][0], 8.5, y, 0.56);
      T(s, `a${o}float_f${i}t`, F[i][1], 9.25, y - 0.02, 3.4, 0.32, { face: HEAD, size: 15 });
      T(s, `a${o}float_f${i}d`, F[i][2], 9.25, y + 0.3, 3.45, 0.5, { size: 12, color: MUTED });
    }
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a8ping_liver", x: 8.5, y: 6.25, w: 4.2, h: 0.48, rectRadius: 0.24, fill: { type: "none" }, line: { color: CORAL, width: 2 } });
    pill(s, "a7pop_live", "●  LIVE DEMO  ·  open stand 9 on the website", 8.5, 6.25, 4.2, { h: 0.48, size: 13, fill: CORAL, line: CORAL, color: "A04B58", tr: 80 });
  }

  // =============== 4 · USERS ===============
  {
    const s = slide("OCEAN_C", "Business use case & end users", "Who uses it, and for which decision", [3.5, -3.2, 6], [8.5, 3.6, 6.5], "usecase");
    const P = [["LuShieldCheck", "Environment agencies", "EAD, MOCCAE, Saudi NCVC", "Which stands do we inspect this month?", "periodic field surveys", "monthly alert + 200 m cell map: inspect only flagged cells"],
      ["LuSprout", "Planting & carbon developers", "ADNOC, Red Sea Global, carbon projects", "Is the carbon we report still there?", "plots and drone campaigns", "condition + carbon stock with a range, a site report"],
      ["LuBuilding2", "Developers & regulators", "EIA consultants, permit offices", "Did works stay outside the mangrove line?", "comparing two images by eye", "an alert when works enter mangrove cells, dated evidence"]];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.1, o = i + 1;
      card(s, `a${o}float_p${i}`, x, 1.85, 3.93, 3.55);
      await iconCircle(s, `a${o}float_p${i}ic`, P[i][0], x + 0.25, 2.07, 0.62);
      T(s, `a${o}float_p${i}n`, P[i][1], x + 1.02, 2.07, 2.8, 0.34, { face: HEAD, size: 15 });
      T(s, `a${o}float_p${i}w`, P[i][2], x + 1.02, 2.42, 2.8, 0.3, { size: 11, color: MUTED });
      label(s, `a${o}float_p${i}l1`, "Their decision", x + 0.25, 2.95, 3.5);
      T(s, `a${o}float_p${i}d`, P[i][3], x + 0.25, 3.23, 3.45, 0.62, { face: HEAD, size: 15, color: "1B2B40" });
      T(s, `a${o}float_p${i}t`, [{ text: "Today: ", options: { bold: true } }, { text: P[i][4] }], x + 0.25, 3.92, 3.45, 0.32, { size: 12, color: MUTED });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a${o}float_p${i}gb`, x: x + 0.18, y: 4.35, w: 3.57, h: 0.88, rectRadius: 0.1, fill: { color: TEAL, transparency: 86 }, line: { type: "none" } });
      T(s, `a${o}float_p${i}g`, P[i][5], x + 0.33, 4.35, 3.3, 0.88, { size: 13, color: TEAL_L, valign: "middle", face: HEAD });
    }
    const F = [["LuSatellite", "New scene", "every ~5 days"], ["LuBell", "Alert", "~1 false alarm / stand-yr"], ["LuLayoutGrid", "Cell map", "where to look"], ["LuSearch", "Inspection", "only flagged cells"], ["LuFileText", "Site report", "carbon at stake"]];
    card(s, "a4fade_flow", 0.6, 5.6, 12.13, 1.15, { fill: "E8F0F9", tr: 10 });
    for (let i = 0; i < 5; i++) {
      const x = 0.95 + i * 2.42, o = 5 + i;
      await iconCircle(s, `a${o}pop_f${i}`, F[i][0], x, 5.85, 0.62);
      T(s, `a${o}pop_f${i}t`, F[i][1], x + 0.75, 5.85, 1.45, 0.32, { face: HEAD, size: 14 });
      T(s, `a${o}pop_f${i}d`, F[i][2], x + 0.75, 6.17, 1.5, 0.3, { size: 11, color: MUTED });
      if (i < 4) s.addShape(pres.shapes.LINE, { objectName: `a${o}fade_ar${i}`, x: x + 2.12, y: 6.16, w: 0.2, h: 0, line: { color: TEAL, width: 1.5, endArrowType: "triangle" } });
    }
  }

  // =============== 5 · DATA ===============
  {
    const s = slide("OCEAN_B", "Data & study area", "Five independent data sources, six years, 91 stands", [-2.6, -1.4, 6.5], [8.8, 3.8, 6], "data");
    card(s, "a1zoom_mapcard", 0.6, 1.85, 4.75, 4.9, { fill: "F3F7FB", tr: 10 });
    s.addImage({ objectName: "a1zoom_map", path: A("stand_map.png"), x: 0.75, y: 1.95, w: 4.45, h: 4.45 * 1398 / 1680 });
    T(s, "a2fade_mapcap", "Pilot: 25 stands · 2,281 ha (WorldCover 2021 patches ≥ 3 ha). +66 unseen stands in Abu Dhabi N/W and Saudi Tarut Bay test transfer.", 0.85, 5.8, 4.3, 0.85, { size: 12, color: MUTED });
    const src = [["LuSatellite", "Sentinel-2 L2A", "ESA / Copernicus · 10–20 m time series", "778 dates"], ["LuScanLine", "EnMAP hyperspectral", "DLR · 224 bands · independent check", "2 scenes"],
      ["LuLayers", "ESA WorldCover 2021", "10 m land cover · stand outlines", "CC BY 4.0"], ["LuLeaf", "Field carbon plots", "Schile et al. 2016 · carbon density", "24 plots"],
      ["LuSearch", "Sub-metre captures", "WorldView-2/3, Legion-1 · confirm events", "0.3–0.5 m"]];
    for (let i = 0; i < 5; i++) {
      const y = 1.85 + i * 0.99, o = 2 + i;
      card(s, `a${o}float_d${i}`, 5.6, y, 7.13, 0.86);
      await iconCircle(s, `a${o}float_d${i}ic`, src[i][0], 5.8, y + 0.17, 0.52, i === 1 ? "7D6FB0" : TEAL);
      T(s, `a${o}float_d${i}t`, src[i][1], 6.5, y + 0.12, 4, 0.34, { face: HEAD, size: 15 });
      T(s, `a${o}float_d${i}d`, src[i][2], 6.5, y + 0.46, 4.2, 0.3, { size: 12, color: MUTED });
      pill(s, `a${o}float_d${i}p`, src[i][3], 11.18, y + 0.23, 1.35, { h: 0.4, size: 13, fill: i === 1 ? "7D6FB0" : GOLD, line: i === 1 ? "7D6FB0" : GOLD, color: i === 1 ? "5E5296" : "8A6A2A" });
    }
    T(s, "a7fade_cap", "Quality control: cloud masks · interior pixels only · tide model · second-source checks", 5.6, 6.83, 7.1, 0.25, { size: 11, color: MUTED });
  }

  // =============== 6 · HYPERSPECTRAL ===============
  {
    const s = slide("OCEAN_A", "Space data · hyperspectral (EnMAP, 224 bands)", "A second sensor shows what the mangrove became", [9, -2.6, 6], [-2.4, 3.6, 6], "hyperspectral");
    const iw = 11.85, ih = iw * 528 / 1870;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a1zoom_ef", x: 0.6, y: 1.85, w: 12.13, h: ih + 0.28, rectRadius: 0.1, fill: { color: "FFFFFF" }, line: { type: "none" }, shadow: shadow() });
    s.addImage({ objectName: "a1zoom_ei", path: IMG("enmap_stand5_two_epochs.png"), x: 0.74, y: 1.99, w: iw, h: ih });
    const C = [["r = 0.84–0.99", "agreement with our Sentinel-2 indices on the same dates (25 and 14 stands)", "6E60A8"],
      ["62 vs 26 ha", "stand-5 loss: EnMAP pixel count vs our conservative Sentinel-2 flag", GOLD],
      ["Vegetation → mineral", "converted pixels take the spectrum of sand and fill: reclamation, not dieback", CORAL]];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.1, y = 1.85 + ih + 0.42, o = 2 + i;
      card(s, `a${o}float_h${i}`, x, y, 3.93, 1.02);
      T(s, `a${o}float_h${i}n`, C[i][0], x + 0.22, y + 0.06, 3.6, 0.45, { face: LIGHT, size: 22, color: C[i][2] });
      T(s, `a${o}float_h${i}t`, C[i][1], x + 0.22, y + 0.52, 3.55, 0.45, { size: 11, color: MUTED });
    }
    T(s, "a5fade_hc", "Honest limit: as a classifier, the full spectrum is no better than Sentinel-2-like bands (F1 0.74 vs 0.72). Contains modified EnMAP data © DLR 2022, 2025.", 0.6, 6.75, 11.5, 0.22, { size: 10, color: "7A8CA0" });
  }

  // =============== 6b · READY FOR SATELLITE 813 ===============
  {
    const s = slide("OCEAN_C", "Space data · ready for Satellite 813", "Sentinel-2 says when. Satellite 813 says what.", [8.8, -2.8, 6], [-2.4, 3.6, 6], "sat813");
    const head = ["Sensor", "Bands", "Range", "Pixel", "Revisit", "Role in the product"];
    const rows = [["Sentinel-2", "13", "443–2190 nm", "10–20 m", "~5 days", "WHEN: the alert, every pass"],
      ["EnMAP (used)", "224", "420–2450 nm", "30 m", "~27 days", "WHAT: tested on stand 5"],
      ["Satellite 813 (next)", "~205", "~400–1700 nm", "~20 m", "on demand", "WHAT, sharper: tasked on flagged cells"]];
    const cell = (v, i, j) => ({ text: v, options: { bold: j === 0 || i === 2, color: i === 2 ? "FFFFFF" : (j === 0 ? TXT : "3A4D63"),
      fill: { color: i === 2 ? "3F6E9E" : (i % 2 ? "F5F8FC" : "FFFFFF") }, align: j === 0 || j === 5 ? "left" : "center", valign: "middle", fontFace: j === 0 || i === 2 ? HEAD : BODY } });
    const table = [head.map((v, j) => ({ text: v, options: { bold: true, color: TEAL_L, fill: { color: "E3EDF8" }, align: j === 0 || j === 5 ? "left" : "center", valign: "middle", fontFace: HEAD, fontSize: 12 } })),
      ...rows.map((r, i) => r.map((v, j) => cell(v, i, j)))];
    s.addTable(table, { objectName: "a1float_tbl", x: 0.6, y: 1.85, w: 12.13, colW: [2.4, 0.95, 1.75, 1.15, 1.35, 4.53], rowH: 0.52, fontSize: 13, margin: 0.08,
      border: { type: "solid", color: "D3E0EE", pt: 0.75 } });
    const F = [["LuBell", "1 · Sentinel-2 alert", "stand or 200 m cell below its threshold"], ["LuSatellite", "2 · Task Satellite 813", "only over the flagged cells, on demand"], ["LuScanLine", "3 · Spectral diagnosis", "vegetation, or sand and fill: an evidence pack"]];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.12, o = 2 + i;
      card(s, `a${o}float_f${i}`, x, 4.15, 3.75, 1.25);
      await iconCircle(s, `a${o}float_f${i}ic`, F[i][0], x + 0.2, 4.47, 0.6, i === 1 ? GOLD : TEAL);
      T(s, `a${o}float_f${i}t`, F[i][1], x + 0.95, 4.3, 2.7, 0.38, { face: HEAD, size: 15 });
      T(s, `a${o}float_f${i}d`, F[i][2], x + 0.95, 4.68, 2.7, 0.6, { size: 12, color: MUTED });
      if (i < 2) T(s, `a${o}fade_ar${i}`, "→", x + 3.75, 4.5, 0.37, 0.5, { size: 22, color: TEAL, align: "center", valign: "middle" });
    }
    card(s, "a5float_note", 0.6, 5.65, 12.13, 1.1, { fill: "E8F0F9", tr: 5 });
    T(s, "a5float_notet", [{ text: "Every index the monitor uses ", options: { bold: true, color: TEAL_L } }, { text: "(NDVI, red edge, SWIR moisture at 1610 nm, wetness) sits inside 813's ~400–1700 nm range, at 20 m instead of EnMAP's 30 m.  " },
      { text: "Planned, not yet tested: ", options: { bold: true, color: GOLD } }, { text: "813 scenes were not available in the proof of concept." }], 0.85, 5.65, 11.7, 1.1, { size: 14, valign: "middle" });
  }

  // =============== 7 · HOW IT WORKS (README workflow diagram) ===============
  {
    const s = slide("OCEAN_C", "Approach · how it works", "From satellite pixels to a decision", [3.6, -3.4, 6], [-2.6, 3.8, 6], "solution");
    card(s, "a1zoom_wfc", 0.6, 1.85, 12.13, 4.72, { fill: "FFFFFF", tr: 8 });
    const ww = 11.7, wh = ww * 664 / 1737;
    s.addImage({ objectName: "a1zoom_wf", path: A("diagram_workflow.png"), x: 0.6 + (12.13 - ww) / 2, y: 1.85 + (4.72 - wh) / 2, w: ww, h: wh });
    const K = [["Core model", "6E95C2"], ["Alert rule", "C0606E"], ["Output to the user", "B08A3E"], ["Inputs and checks", "9AAFC6"]];
    T(s, "a2fade_wl", "Read left to right:", 0.6, 6.68, 1.9, 0.3, { size: 12, color: MUTED });
    K.forEach(([t, c], i) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a2fade_wk${i}`, x: 2.45 + i * 2.35, y: 6.75, w: 0.26, h: 0.16, rectRadius: 0.04, fill: { color: c, transparency: 30 }, line: { color: c, width: 0.75 } });
      T(s, `a2fade_wkt${i}`, t, 2.8 + i * 2.35, 6.68, 2.0, 0.3, { size: 12, color: "3A4D63" });
    });
  }

  // =============== 8 · HOW A USER RECEIVES IT (README sequence diagram) ===============
  {
    const s = slide("OCEAN_B", "Delivery · how a user receives it", "One alert, one message, one targeted visit", [-2.4, -2.6, 6], [9, 3.6, 6], "sequence");
    card(s, "a1zoom_sqc", 0.6, 1.85, 8.25, 4.9, { fill: "FFFFFF", tr: 8 });
    const SQ = require("fs").readFileSync(A("diagram_sequence.png")); const sw = SQ.readUInt32BE(16), sh = SQ.readUInt32BE(20);
    let qw = 7.95, qh = qw * sh / sw; if (qh > 4.6) { qh = 4.6; qw = qh * sw / sh; }
    s.addImage({ objectName: "a1zoom_sq", path: A("diagram_sequence.png"), x: 0.6 + (8.25 - qw) / 2, y: 1.85 + (4.9 - qh) / 2, w: qw, h: qh });
    const E = [["LuSatellite", "Every ~5 days", "a new Sentinel-2 scene is read in place and run through the tide-aware model, per stand and per 200 m cell", TEAL],
      ["LuBell", "If an alert fires", "we check the flagged cells on sub-metre imagery, then send the alert by email or JSON API with the cell map and the carbon at stake", CORAL],
      ["LuFileText", "If nothing changes", "the user still gets a monthly site report: condition, trend and carbon stock for every stand", GOLD]];
    for (let i = 0; i < 3; i++) {
      const y = 1.85 + i * 1.66, o = 2 + i;
      card(s, `a${o}float_e${i}`, 9.1, y, 3.63, 1.52);
      await iconCircle(s, `a${o}float_e${i}ic`, E[i][0], 9.28, y + 0.16, 0.48, E[i][3]);
      T(s, `a${o}float_e${i}t`, E[i][1], 9.88, y + 0.2, 2.75, 0.34, { face: HEAD, size: 14, color: E[i][3] === TEAL ? TXT : E[i][3] });
      T(s, `a${o}float_e${i}d`, E[i][2], 9.28, y + 0.72, 3.3, 0.78, { size: 11, color: "3A4D63" });
    }
  }

  // =============== 9 · TIDE INNOVATION ===============
  {
    const s = slide("OCEAN_A", "Technical innovation 1", "The tide looks like tree loss — until you correct for it", [9.2, -2.5, 6], [-1.5, 3.8, 5.5], "innovation");
    card(s, "a1float_ill", 0.6, 1.85, 6.0, 3.55);
    label(s, "a1float_illl", "Why naive monitors fail on tidal flats", 0.85, 2.02, 5.5);
    for (let p = 0; p < 2; p++) {
      const x0 = 0.85 + p * 2.85, wl = p === 0 ? 4.45 : 3.65; // water level
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a2fade_pn${p}`, x: x0, y: 2.4, w: 2.65, h: 2.35, rectRadius: 0.1, fill: { color: "F3F7FB", transparency: 0 }, line: { color: LINE, width: 0.75 } });
      T(s, `a2fade_pt${p}`, p === 0 ? "Low tide" : "High tide", x0 + 0.15, 2.48, 2, 0.3, { face: HEAD, size: 14 });
      for (let t = 0; t < 5; t++) {
        s.addShape(pres.shapes.RECTANGLE, { objectName: `a2fade_tr${p}_${t}`, x: x0 + 0.3 + t * 0.47, y: 3.55, w: 0.04, h: 1.1, fill: { color: "6B5B4B" }, line: { type: "none" } });
        s.addShape(pres.shapes.OVAL, { objectName: `a2fade_tc${p}_${t}`, x: x0 + 0.13 + t * 0.47, y: 3.2, w: 0.38, h: 0.38, fill: { color: "5E977A" }, line: { type: "none" } });
      }
      s.addShape(pres.shapes.RECTANGLE, { objectName: `a3rise_w${p}`, x: x0 + 0.02, y: wl, w: 2.61, h: 4.73 - wl, fill: { color: BLUE, transparency: 45 }, line: { type: "none" } });
      T(s, `a4fade_nv${p}`, [{ text: "NDVI ", options: { color: MUTED } }, { text: p === 0 ? "0.30" : "0.18", options: { bold: true, color: p === 0 ? TEAL_L : CORAL } }], x0, 4.82, 2.65, 0.35, { size: 15, align: "center" });
    }
    T(s, "a4fade_illc", "Same trees, same season. Measured on our stands: noise vs wetness r ≈ −0.9.", 0.85, 5.08, 5.6, 0.28, { size: 11, color: MUTED });
    card(s, "a1float_chc", 6.85, 1.85, 5.88, 3.55);
    s.addChart(pres.charts.BAR, [
      { name: "without tide model", labels: ["NDVI", "NDRE (red edge)", "NDMI (moisture)"], values: [0.0436, 0.0283, 0.0433] },
      { name: "with tide model", labels: ["NDVI", "NDRE (red edge)", "NDMI (moisture)"], values: [0.0298, 0.0183, 0.0306] }],
      { objectName: "a3wipe_chart", x: 7.0, y: 2.0, w: 5.6, h: 3.3, barDir: "col", barGapWidthPct: 60, chartColors: ["B9C6D4", TEAL],
        showTitle: true, title: "Date-to-date noise, 25 stands, 2020–2026", titleColor: TXT, titleFontFace: BODY, titleFontSize: 13,
        showLegend: true, legendPos: "b", legendColor: MUTED, legendFontFace: BODY, legendFontSize: 11,
        showValue: true, dataLabelPosition: "outEnd", dataLabelColor: TXT, dataLabelFontSize: 10, dataLabelFormatCode: "0.000", dataLabelFontFace: BODY,
        catAxisLabelColor: MUTED, catAxisLabelFontFace: BODY, catAxisLabelFontSize: 11, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
        catAxisLineColor: LINE });
    card(s, "a5float_st", 0.6, 5.6, 6.0, 1.15, { fill: "E8F0F9", tr: 5 });
    await iconCircle(s, "a5float_stic", "LuWaves", 0.85, 5.88, 0.6);
    T(s, "a5float_stn", "−29 to −35 %", 1.6, 5.6, 2.55, 1.15, { face: LIGHT, size: 28, color: GOLD, valign: "middle" });
    T(s, "a5float_stt", "less noise on every index: we model trend, season and the tide before flagging anything", 4.1, 5.6, 2.4, 1.15, { size: 12, valign: "middle" });
    card(s, "a6float_tb", 6.85, 5.6, 5.88, 1.15, { fill: "E8F0F9", tr: 5 });
    T(s, "a6float_tbn", [{ text: "1.61 → 0.96", options: { color: GOLD } }], 7.05, 5.6, 2.55, 1.15, { face: LIGHT, size: 28, valign: "middle" });
    T(s, "a6float_tbt", "false alarms per stand-year: textbook NDVI-only vs our tide-aware monitor, same alert rule, same 25 stands (40 % fewer)", 9.6, 5.6, 3.0, 1.15, { size: 12, valign: "middle" });
  }

  // =============== 10 · CELLS ===============
  {
    const s = slide("OCEAN_C", "Technical innovation 2", "A stand average hides partial loss. 200 m cells do not.", [-2, -2.8, 6], [9, 3.4, 6.5], "cells");
    s.addImage({ objectName: "vid_cells", path: path.join(__dirname, "build", "media", "alert_story.png"), x: 0.6, y: 1.85, w: 7.7, h: 7.7 * 520 / 1100 });
    T(s, "a2fade_storyc", "Real stand-5 data, 2022 → 2026: cells turn red while the stand average barely moves.", 0.6, 5.55, 7.7, 0.3, { size: 11, color: MUTED });
    const bars = [[73, "stand + cells", TEAL], [25, "stand alone", BLUE], [13, "by chance", "B9C6D4"]];
    T(s, "a5fade_bl", "Partial loss caught within 60 days (simulated)", 0.6, 5.98, 3.1, 0.6, { face: HEAD, size: 13 });
    for (let i = 0; i < 3; i++) {
      const x = 3.9 + i * 1.5;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a${6 + i}wipe_b${i}`, x, y: 6.0, w: 1.35 * bars[i][0] / 73, h: 0.2, rectRadius: 0.1, fill: { color: bars[i][2] }, line: { type: "none" } });
      T(s, `a${6 + i}fade_bt${i}`, [{ text: bars[i][0] + " %  ", options: { bold: true, color: i === 0 ? TEAL_L : TXT } }, { text: bars[i][1], options: { color: MUTED } }], x, 6.28, 1.45, 0.45, { size: 11 });
    }
    const c = [["8 of 28", "cells of stand 9 in severe decline while its average reads “stable”"], ["3 of 5", "real conversions found only by the cells (stands 12, 18, 6)"]];
    for (let i = 0; i < 2; i++) {
      const y = 1.85 + i * 1.62;
      card(s, `a${2 + i}float_c${i}`, 8.55, y, 4.18, 1.48);
      T(s, `a${2 + i}float_c${i}n`, c[i][0], 8.8, y + 0.15, 3.8, 0.65, { face: LIGHT, size: 34, color: i === 0 ? CORAL : GOLD });
      T(s, `a${2 + i}float_c${i}t`, c[i][1], 8.8, y + 0.82, 3.75, 0.6, { size: 13 });
    }
    card(s, "a4float_rule", 8.55, 5.09, 4.18, 1.66, { fill: "E8F0F9", tr: 5 });
    label(s, "a4float_rulel", "One alert rule", 8.8, 5.24, 3.5);
    pill(s, "a4float_r1", "stand ≤ −1.5σ", 8.8, 5.6, 1.6, { size: 13 });
    T(s, "a4float_or", "OR", 10.45, 5.6, 0.45, 0.4, { face: HEAD, size: 13, color: GOLD, align: "center", valign: "middle" });
    pill(s, "a4float_r2", "any cell ≤ −3.5σ", 10.95, 5.6, 1.62, { size: 13, fill: CORAL, line: CORAL, color: "A04B58" });
    T(s, "a4float_rulet", "calibrated together: 0.96 false-alarm episodes per stand-year", 8.8, 6.12, 3.8, 0.5, { size: 12, color: MUTED });
  }

  // =============== 11 · HOW WE DIFFER ===============
  {
    const s = slide("OCEAN_B", "Innovation & differentiation", "How we differ from what exists today", [-2.4, -2.4, 6.5], [8.8, 3.6, 6.5], "different");
    const head = ["", "Field surveys", "One-off satellite maps", "Free loss alerts (Global Mangrove Watch)", "Blue Carbon Guardian"];
    const rows = [["How often", "campaigns", "yearly or less", "monthly", "every ~5 days"],
      ["Corrects for the tide", "n/a", "not usually", "not documented", "✓  tide model"],
      ["Says where inside a stand", "✓", "—", "—", "✓  200 m cells"],
      ["Published false-alarm rate", "n/a", "n/a", "accuracy only", "✓  ≈ 1 per stand-year"],
      ["Carbon at stake per alert", "—", "—", "—", "✓  field-based"],
      ["Gulf coverage", "✓", "✓", "not confirmed", "✓  Abu Dhabi + Tarut Bay"]];
    const cell = (t, i, j) => ({ text: t, options: {
      bold: j === 0 || j === 4, color: j === 4 ? "FFFFFF" : j === 0 ? TXT : (t === "—" || t === "n/a" ? "8A9BB0" : "3A4D63"),
      fill: { color: j === 4 ? "3F6E9E" : (i % 2 ? "F5F8FC" : "FFFFFF") }, align: j === 0 ? "left" : "center", valign: "middle", fontFace: j === 0 || j === 4 ? HEAD : BODY } });
    const table = [head.map((t, j) => ({ text: t, options: { bold: true, color: j === 4 ? "FFFFFF" : TEAL_L, fill: { color: j === 4 ? "2F5D8F" : "E3EDF8" }, align: j === 0 ? "left" : "center", valign: "middle", fontFace: HEAD, fontSize: 12 } })),
      ...rows.map((r, i) => r.map((t, j) => cell(t, i, j)))];
    s.addTable(table, { objectName: "a1float_tbl", x: 0.6, y: 1.85, w: 12.13, colW: [3.0, 1.9, 2.1, 2.45, 2.68], rowH: 0.52, fontSize: 13, margin: 0.08,
      border: { type: "solid", color: "D3E0EE", pt: 0.75 } });
    card(s, "a3float_dm", 0.6, 5.75, 12.13, 1.0, { fill: "E8F0F9", tr: 5 });
    T(s, "a3float_dmt", [{ text: "Complementary, not competing: ", options: { bold: true, color: TEAL_L } }, { text: "Global Mangrove Watch flags loss worldwide; we add the tide model, the 200 m cells, a measured false-alarm rate and the carbon at stake — built and tested for the Gulf." }], 0.85, 5.75, 11.7, 1.0, { size: 14, valign: "middle" });
  }

  // =============== 12 · REAL EVENTS ===============
  {
    const s = slide("OCEAN_A", "Validation 1 · real events", "Five real conversions, confirmed on sub-metre imagery", [-2.2, -2.6, 6], [9.2, 3.6, 6], "validation-real");
    const tiles = [["stand5_before_after_2021_2026.png", 1806 / 802, "Stand 5", "reclamation with finger canals"], ["stand9_before_after_2020_2026.png", 2206 / 1468, "Stand 9", "canal development, south-east"],
      ["stand12_key_years.png", 1404 / 413, "Stand 12", "found only by the cells"], ["stand18_key_years.png", 1404 / 413, "Stand 18", "found only by the cells, 2025"]];
    for (let i = 0; i < 4; i++) {
      const top = i < 2, x = 0.6 + (i % 2) * 3.75, y = top ? 1.85 : 4.92, o = 1 + i, tw = 3.6, th = top ? 2.92 : 1.83;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a${o}zoom_t${i}`, x, y, w: tw, h: th, rectRadius: 0.1, fill: { color: "FFFFFF" }, line: { type: "none" }, shadow: shadow() });
      const aw = tw - 0.2, ah = th - 0.62; let w = aw, h = aw / tiles[i][1]; if (h > ah) { h = ah; w = ah * tiles[i][1]; }
      s.addImage({ objectName: `a${o}zoom_t${i}i`, path: IMG(tiles[i][0]), x: x + (tw - w) / 2, y: y + 0.1 + (ah - h) / 2, w, h });
      T(s, `a${o}zoom_t${i}l`, [{ text: tiles[i][2] + "  ", options: { bold: true, color: "0B2236" } }, { text: tiles[i][3], options: { color: "4A5F75" } }], x + 0.15, y + th - 0.45, tw - 0.3, 0.35, { size: 12, valign: "middle" });
    }
    // gantt: alert start vs [last intact, first disturbed] capture window
    card(s, "a1float_gc", 8.25, 1.85, 4.48, 3.75);
    label(s, "a1float_gl", "When did the alert start?", 8.45, 1.98, 4);
    const rows = [["Stand 5", "2022-03-28", "2023-02-22", "2022-10-25"], ["Stand 9", "2022-03-28", "2023-02-22", "2022-12-07"], ["Stand 12", "2022-03-28", "2023-02-22", "2022-12-17"], ["Stand 6", "2022-03-28", "2023-02-22", "2023-02-17"], ["Stand 18", "2023-11-14", "2025-01-06", "2024-10-29"]];
    const t0 = Date.parse("2022-01-01"), t1 = Date.parse("2025-04-01"), L = 9.3, R = 12.55, X = (d) => L + (Date.parse(d) - t0) / (t1 - t0) * (R - L);
    [2022, 2023, 2024, 2025].forEach((yr) => {
      const x = X(`${yr}-01-01`);
      s.addShape(pres.shapes.LINE, { objectName: `a1float_gy${yr}`, x, y: 2.35, w: 0, h: 2.65, line: { color: LINE, width: 0.75, dashType: "dash" } });
      T(s, `a1float_gyt${yr}`, String(yr), x - 0.3, 5.03, 0.6, 0.25, { size: 10, color: MUTED, align: "center" });
    });
    rows.forEach((r, i) => {
      const y = 2.45 + i * 0.5;
      T(s, `a2fade_gn${i}`, r[0], 8.45, y, 0.85, 0.3, { face: HEAD, size: 11, valign: "middle" });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a2fade_gw${i}`, x: X(r[1]), y: y + 0.05, w: X(r[2]) - X(r[1]), h: 0.2, rectRadius: 0.06, fill: { color: BLUE, transparency: 55 }, line: { color: BLUE, width: 0.75 } });
      s.addShape(pres.shapes.DIAMOND, { objectName: `a${3 + i}pop_gd${i}`, x: X(r[3]) - 0.13, y: y + 0.02, w: 0.26, h: 0.26, fill: { color: CORAL }, line: { color: "FFFFFF", width: 1 } });
    });
    s.addShape(pres.shapes.OVAL, { objectName: "a8ping_d0", x: X(rows[0][3]) - 0.16, y: 2.45 - 0.01, w: 0.32, h: 0.32, fill: { type: "none" }, line: { color: CORAL, width: 2 } });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a8fade_lg1", x: 8.45, y: 5.33, w: 0.3, h: 0.14, rectRadius: 0.05, fill: { color: BLUE, transparency: 55 }, line: { color: BLUE, width: 0.75 } });
    T(s, "a8fade_lg1t", "last intact → first capture with works", 8.82, 5.27, 2.4, 0.26, { size: 10, color: MUTED });
    s.addShape(pres.shapes.DIAMOND, { objectName: "a8fade_lg2", x: 11.3, y: 5.3, w: 0.18, h: 0.18, fill: { color: CORAL }, line: { type: "none" } });
    T(s, "a8fade_lg2t", "our alert starts", 11.53, 5.27, 1.1, 0.26, { size: 10, color: MUTED });
    card(s, "a9float_msg", 8.25, 5.75, 4.48, 1.0, { fill: "E8F0F9", tr: 5 });
    T(s, "a9float_msgt", [{ text: "Every alert began inside the window. ", options: { bold: true, color: TEAL_L } }, { text: "Detection as works happen, not advance warning." }], 8.45, 5.75, 4.15, 1.0, { size: 13, valign: "middle" });
  }

  // =============== 13 · VALIDATION ===============
  {
    const s = slide("OCEAN_C", "Validation 2 · chance, unseen stands, second sensor", "Every rate next to its chance rate", [4, -3.4, 6], [-2.4, 3.8, 6], "validation");
    card(s, "a1float_cc", 0.6, 1.85, 7.45, 3.95);
    s.addChart(pres.charts.BAR, [
      { name: "detected", labels: ["Whole stand loses 20 % · 6 months", "Whole stand loses 10 % · 6 months", "A tenth of a stand loses half · 60 days"], values: [83, 63, 73] },
      { name: "by chance (same test, no loss)", labels: ["Whole stand loses 20 % · 6 months", "Whole stand loses 10 % · 6 months", "A tenth of a stand loses half · 60 days"], values: [36, 36, 13] }],
      { objectName: "a2wipe_sim", x: 0.75, y: 1.95, w: 7.15, h: 3.75, barDir: "bar", barGapWidthPct: 55, chartColors: [TEAL, "B9C6D4"],
        showTitle: true, title: "Artificial loss injected into stands with no known change", titleColor: TXT, titleFontFace: BODY, titleFontSize: 13,
        showLegend: true, legendPos: "b", legendColor: MUTED, legendFontFace: BODY, legendFontSize: 11,
        showValue: true, dataLabelPosition: "outEnd", dataLabelColor: TXT, dataLabelFontSize: 12, dataLabelFormatCode: '0" %"', dataLabelFontFace: BODY,
        catAxisLabelColor: TXT, catAxisLabelFontFace: BODY, catAxisLabelFontSize: 11, valAxisHidden: true, valAxisMaxVal: 100, valAxisMinVal: 0, valGridLine: { style: "none" }, catGridLine: { style: "none" }, catAxisLineColor: LINE });
    T(s, "a3fade_simc", "A detection counts only if a new alert starts after the loss begins. ~160–240 trials per row.", 0.6, 5.88, 7.45, 0.3, { size: 11, color: MUTED });
    const K = [["Calibrated · 25 stands", "0.96", "false-alarm episodes per stand-year", GOLD], ["Unseen · 65 stands", "0.79", "per stand-year, 305 stand-years, incl. Saudi Tarut Bay", TEAL_L], ["EnMAP · same dates", "r = 0.84–0.99", "vs our Sentinel-2 indices; stand-5 loss 62 ha vs our 26 ha", "6E60A8"]];
    for (let i = 0; i < 3; i++) {
      const y = 1.85 + i * 1.36;
      card(s, `a${3 + i}float_k${i}`, 8.3, y, 4.43, 1.24, i === 1 ? { fill: "E8F0F9", tr: 5 } : {});
      label(s, `a${3 + i}float_k${i}l`, K[i][0], 8.52, y + 0.12, 4.1, i === 2 ? "6E60A8" : TEAL);
      T(s, `a${3 + i}float_k${i}n`, K[i][1], 8.52, y + 0.38, 4.1, 0.5, { face: LIGHT, size: 26, color: K[i][3] });
      T(s, `a${3 + i}float_k${i}t`, K[i][2], 8.52, y + 0.86, 4.1, 0.32, { size: 11, color: MUTED });
    }
    card(s, "a6float_claim", 0.6, 6.22, 12.13, 0.6, { fill: GOLD, tr: 88, line: GOLD });
    T(s, "a6float_claimt", [{ text: "What we do not claim: ", options: { bold: true, color: GOLD } }, { text: "advance warning, field verification, species discrimination, or that hyperspectral classifies better (F1 0.74 vs 0.72). We withdrew our own first test (58 % / 90 %): it had no chance baseline." }], 0.85, 6.22, 11.7, 0.6, { size: 12, valign: "middle" });
  }

  // =============== 14 · IMPACT & BUSINESS ===============
  {
    const s = slide("OCEAN_A", "Impact & business viability", "Carbon at stake, and who pays to protect it", [8.4, -3, 6.5], [-2.6, 3.4, 6], "impact");
    const kp = [["108 t C/ha", "field density near the stands (90 % CI 79–138); 82 % of it is in the soil", GOLD], ["247 kt C", "pilot stock, 2,281 ha (range 180–316) ≈ 907 kt CO₂e", GOLD], ["2.8–6.7 kt C", "stock on the 26–62 ha lost at stand 5: what one alert puts on the table", CORAL]];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.1;
      card(s, `a${1 + i}float_kp${i}`, x, 1.85, 3.93, 1.4, i === 2 ? { fill: "FBEDEF", tr: 20, line: "E8C4CA" } : {});
      T(s, `a${1 + i}float_kp${i}n`, kp[i][0], x + 0.25, 1.95, 3.5, 0.62, { face: LIGHT, size: 32, color: kp[i][2] });
      T(s, `a${1 + i}float_kp${i}t`, kp[i][1], x + 0.25, 2.6, 3.5, 0.6, { size: 12, color: MUTED });
    }
    card(s, "a4float_tc", 0.6, 3.45, 7.25, 3.3);
    label(s, "a4float_tl", "Service tiers (prices are pilot hypotheses)", 0.85, 3.6, 6.8);
    const tiers = [["Monitor", "$12k", "per site / yr", "alert, cell map, condition, carbon, monthly reports"], ["Evidence", "$25k", "per site / yr", "+ sub-metre check of every alert, audit pack"], ["Development watch", "$8k", "per project / yr", "for coastal developers and EIA consultants"]];
    for (let i = 0; i < 3; i++) {
      const x = 0.85 + i * 2.28, o = 5 + i;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: `a${o}pop_t${i}`, x, y: 3.98, w: 2.15, h: 1.9, rectRadius: 0.1, fill: { color: TEAL, transparency: i === 0 ? 78 : 90 }, line: { color: TEAL, width: 0.75, transparency: 40 } });
      T(s, `a${o}pop_t${i}n`, tiers[i][0], x + 0.15, 4.06, 1.9, 0.3, { face: HEAD, size: 13 });
      T(s, `a${o}pop_t${i}p`, tiers[i][1], x + 0.15, 4.36, 1.9, 0.55, { face: LIGHT, size: 28, color: TEAL_L });
      T(s, `a${o}pop_t${i}u`, tiers[i][2], x + 0.15, 4.9, 1.9, 0.25, { size: 11, color: MUTED });
      T(s, `a${o}pop_t${i}d`, tiers[i][3], x + 0.15, 5.18, 1.9, 0.65, { size: 11 });
    }
    T(s, "a8fade_cost", [{ text: "Cost to serve ≈ $3.3k / site / yr: ", options: { bold: true } }, { text: "compute < $5 (measured), sub-metre checks $500–750, analyst $2k (assumption)." }], 0.85, 6.02, 6.8, 0.6, { size: 12, color: "3A4D63" });
    card(s, "a6float_comp", 8.05, 3.45, 4.68, 1.55);
    label(s, "a6float_compl", "Competition", 8.3, 3.6, 4);
    T(s, "a6float_compt", "Global Mangrove Watch sends free monthly loss alerts (Gulf coverage not confirmed). We are complementary: tide-aware, calibrated, stand + cell, carbon and reports.", 8.3, 3.9, 4.25, 1.05, { size: 12 });
    card(s, "a7float_mk", 8.05, 5.15, 4.68, 1.6, { fill: "E8F0F9", tr: 5 });
    label(s, "a7float_mkl", "The honest market", 8.3, 5.28, 4);
    T(s, "a7float_mkt", [{ text: "Gulf + Red Sea subscriptions ≈ $0.2–0.4 M / yr. The real prize: a " }, { text: "national MRV contract", options: { bold: true, color: GOLD } }, { text: " or a monitoring layer on " }, { text: "gIQ", options: { bold: true, color: GOLD } }, { text: ". SDG 13 · 14 · 15." }], 8.3, 5.58, 4.25, 1.1, { size: 13 });
  }

  // =============== 15 · SCALE & REPRODUCIBILITY ===============
  {
    const s = slide("OCEAN_B", "Bonus criteria · beyond the proof of concept", "Reproducible today, built to scale tomorrow", [-2.6, -2.2, 6.5], [8.9, 3.4, 6.5], "scale");
    card(s, "a1float_rc", 0.6, 1.85, 5.95, 4.9);
    label(s, "a1float_rl", "Bonus · documentation & reproducibility", 0.85, 2.0, 5.6);
    const R = [["LuGithub", "Public repository, MIT licence", "code, notebook, figures, provenance and licences"], ["LuCheckCircle", "Re-runs end to end in ~24 s", "outputs committed · pinned requirements · example in/out"],
      ["LuShieldCheck", "Clean-machine test passed", "fresh environment, same numbers, 0 errors"], ["LuSearch", "Every number traceable", "each figure comes from a script and a written summary"], ["LuMonitor", "Live website + site reports", "anyone can open the monitor and check a stand"]];
    for (let i = 0; i < 5; i++) {
      const y = 2.42 + i * 0.84, o = 2 + i;
      await iconCircle(s, `a${o}float_r${i}`, R[i][0], 0.85, y, 0.54);
      T(s, `a${o}float_r${i}t`, R[i][1], 1.55, y - 0.02, 4.8, 0.32, { face: HEAD, size: 15 });
      T(s, `a${o}float_r${i}d`, R[i][2], 1.55, y + 0.3, 4.85, 0.3, { size: 12, color: MUTED });
    }
    label(s, "a1fade_sl", "Bonus · scalability beyond the PoC", 6.85, 1.85, 5.8);
    const P = [["LuCheckCircle", "Proven now", "91 stands · 2 countries · 2 Sentinel-2 tiles · 65 unseen stands at 0.79 false alarms / stand-yr · compute < $5 per site per year", true],
      ["LuFlag", "Incubation", "Satellite 813 in the spectral step · deployment on gIQ · a pilot customer + site records · more EnMAP dates", false],
      ["LuRocket", "Scale", "Gulf ≈ 165 km² + Red Sea ≈ 200 km² of mangrove · sub-metre data for small stands (Bahrain) · national MRV, licensing", false]];
    s.addShape(pres.shapes.LINE, { objectName: "a2fade_spine", x: 7.2, y: 2.6, w: 0, h: 3.2, line: { color: TEAL, width: 1.5, dashType: "dash" } });
    for (let i = 0; i < 3; i++) {
      const y = 2.22 + i * 1.53, o = 3 + i * 2;
      card(s, `a${o}float_p${i}`, 7.55, y, 5.18, 1.38, P[i][3] ? { fill: "E8F0F9", tr: 5 } : {});
      await iconCircle(s, `a${o}pop_p${i}ic`, P[i][0], 6.92, y + 0.41, 0.56, P[i][3] ? GOLD : TEAL);
      T(s, `a${o}float_p${i}t`, P[i][1], 7.8, y + 0.12, 4.7, 0.34, { face: HEAD, size: 15, color: P[i][3] ? GOLD : TXT });
      T(s, `a${o}float_p${i}d`, P[i][2], 7.8, y + 0.48, 4.75, 0.85, { size: 12, color: "3A4D63" });
    }
    T(s, "a8fade_src", "Areas: Frontiers in Marine Science 2025. Compute measured; prices assumed.", 6.85, 6.75, 5.2, 0.22, { size: 9, color: "8A9BB0" });
  }

  // =============== 17 · CLOSE ===============
  {
    usePalette(HERO_P);
    const s = pres.addSlide({ masterName: "HERO" });
    glows(s, [-2.4, -3, 7.5], [7.8, 2.6, 7.5]);
    s.addNotes(NOTES.close);
    T(s, "a0fade_k", [{ text: "TEAM BLUE ATHAR  ·  ", options: { charSpacing: 4 } }, { text: "الأثر الأزرق", options: { charSpacing: 0 } }], 0.8, 1.05, 8, 0.36, { face: HEAD, size: 13, color: TEAL });
    T(s, "a1float_tag", "Every lost mangrove leaves a trace.\nWe find it from space.", 0.76, 1.5, 11.5, 1.75, { face: HEAD, size: 46, ls: 1.0 });
    T(s, "a1float_merit", "Overall value:  a working product  ·  five real events confirmed  ·  every number reproducible", 0.8, 3.12, 11.7, 0.4, { face: HEAD, size: 16, color: GOLD });
    const K = [["Tide-aware", "29–35 % less noise"], ["5 of 5", "conversions alerted during the works, 3 only by cells"], ["0.79", "false alarms / stand-yr on unseen stands"], ["Open", "public code, re-runs in ~24 s"]];
    for (let i = 0; i < 4; i++) {
      const x = 0.8 + i * 2.97, o = 2 + i;
      card(s, `a${o}float_c${i}`, x, 3.75, 2.8, 1.3, { tr: 30 });
      T(s, `a${o}float_c${i}n`, K[i][0], x + 0.22, 3.83, 2.4, 0.55, { face: LIGHT, size: 28, color: i === 1 ? CORAL : GOLD });
      T(s, `a${o}float_c${i}t`, K[i][1], x + 0.22, 4.4, 2.45, 0.6, { size: 12, color: "CFDCE8" });
    }
    card(s, "a6float_ask", 0.8, 5.25, 11.72, 0.95, { fill: TEAL, tr: 84, line: TEAL });
    T(s, "a6float_askt", [{ text: "Our ask:  ", options: { bold: true, color: TEAL_L } }, { text: "incubation to run a pilot with a Gulf agency or planting programme, mentor access on hyperspectral reading of mangroves, and Satellite 813 scenes when available." }], 1.05, 5.25, 11.3, 0.95, { size: 15, valign: "middle" });
    T(s, "a7fade_links", "nahla-nabil.github.io/blue-carbon-guardian   ·   github.com/Nahla-Nabil/blue-carbon-guardian", 0.8, 6.45, 9, 0.35, { size: 13, color: MUTED });
    T(s, "a7fade_ty", "Thank you", 9.9, 6.38, 2.62, 0.45, { face: HEAD, size: 20, color: GOLD, align: "right" });
    s.addImage({ objectName: "a7fade_fae", path: path.join(__dirname, "flag_ae.png"), x: 10.2, y: 6.49, w: 0.44, h: 0.22 });
    s.addImage({ objectName: "a7fade_fbh", path: path.join(__dirname, "flag_bh.png"), x: 10.72, y: 6.49, w: 0.37, h: 0.22 });
    usePalette(LIGHT_P);
  }

  // =============== 17b · THANK YOU ===============
  {
    usePalette(HERO_P);
    const s = pres.addSlide({ masterName: "HERO" });
    glows(s, [7.6, -2.8, 7.5], [-2.8, 3.2, 7.5]);
    s.addNotes(NOTES.thanks);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a1zoom_flagbg", x: 0.74, y: 1.12, w: 2.92, h: 1.48, rectRadius: 0.06, fill: { color: "FFFFFF" }, line: { type: "none" }, shadow: shadow() });
    s.addImage({ objectName: "a1zoom_flag", path: path.join(__dirname, "flag_ae.png"), x: 0.8, y: 1.18, w: 2.8, h: 1.36 });
    T(s, "a2float_ty", "Thank you", 3.95, 0.98, 8.6, 1.05, { face: HEAD, size: 60 });
    T(s, "a2float_tyar", "شكراً للإمارات", 3.98, 1.98, 8.6, 0.75, { face: HEAD, size: 32, color: "D4E2EE" });
    T(s, "a3float_uae", [{ text: "To the " }, { text: "United Arab Emirates", options: { bold: true, color: GOLD } }, { text: " — for leading the region in protecting its mangroves, and for opening space to Arab youth." }],
      0.8, 3.15, 11.7, 1.15, { face: LIGHT, size: 24 });
    card(s, "a4float_org", 0.8, 4.55, 11.72, 0.95, { fill: TEAL, tr: 84, line: TEAL });
    T(s, "a4float_orgt", [{ text: "With thanks to:  ", options: { bold: true, color: TEAL_L } }, { text: "UAE Space Agency  ·  National Space Academy  ·  Space42  ·  the mentors and the judges" }], 1.05, 4.55, 11.3, 0.95, { size: 17, valign: "middle" });
    s.addImage({ objectName: "a5fade_fbh", path: path.join(__dirname, "flag_bh.png"), x: 0.8, y: 6.08, w: 0.42, h: 0.25 });
    T(s, "a5fade_from", "From Bahrain, with gratitude  —  Nahla Nabil  ·  Team Blue Athar", 1.32, 5.98, 9, 0.45, { size: 14, color: "D4E2EE", valign: "middle" });
    usePalette(LIGHT_P);
  }

  // =============== BACKUP A · TEXTBOOK BASELINE (Q&A only) ===============
  {
    const s = slide("OCEAN_A", "Backup · for questions", "The textbook approach against ours, same alert rule", [8.8, -3, 6], [-2.6, 3.4, 6], "bk-textbook");
    const head = ["Configuration", "Indices", "Tide model", "False alarms per stand-year", "Real conversions caught"];
    const rows = [["A · textbook", "NDVI", "no", "1.61", "5 of 5"], ["B", "NDVI", "yes", "1.04", "5 of 5"], ["C", "NDVI + red edge + SWIR moisture", "no", "1.36", "5 of 5"], ["D · ours", "NDVI + red edge + SWIR moisture", "yes", "0.96", "5 of 5"]];
    const cell = (v, i, j) => ({ text: v, options: { bold: j === 0 || j === 3, color: j === 3 ? (i === 0 ? CORAL : (i === 3 ? TEAL_L : TXT)) : (i === 3 ? TXT : "3A4D63"),
      fill: { color: i === 3 ? "E3EDF8" : (i % 2 ? "F5F8FC" : "FFFFFF") }, align: j < 2 ? "left" : "center", valign: "middle", fontFace: j === 0 || j === 3 ? HEAD : BODY, fontSize: j === 3 ? 16 : 13 } });
    s.addTable([head.map((v, j) => ({ text: v, options: { bold: true, color: TEAL_L, fill: { color: "E3EDF8" }, align: j < 2 ? "left" : "center", valign: "middle", fontFace: HEAD, fontSize: 12 } })),
      ...rows.map((r, i) => r.map((v, j) => cell(v, i, j)))], { objectName: "a1float_tbl", x: 0.6, y: 1.85, w: 12.13, colW: [2.2, 4.0, 1.5, 2.43, 2.0], rowH: 0.55, margin: 0.08,
      border: { type: "solid", color: "D3E0EE", pt: 0.75 } });
    const C = [["40 % fewer false alarms", "20 stands with no known change, 93.9 stand-years: about 16 fewer unnecessary inspections a year for 25 stands."],
      ["The tide model is most of the gain", "NDVI alone 1.61 → with tide terms 1.04; the extra indices bring it to 0.96."],
      ["Honest limit", "Thresholds calibrated for our monitor; all four catch the five conversions. The difference is the false-alarm cost, not detection."]];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.1, o = 2 + i;
      card(s, `a${o}float_c${i}`, x, 5.0, 3.93, 1.75, i === 2 ? { fill: "FBF5EA" } : {});
      T(s, `a${o}float_c${i}t`, C[i][0], x + 0.22, 5.12, 3.55, 0.4, { face: HEAD, size: 15, color: i === 2 ? GOLD : TXT });
      T(s, `a${o}float_c${i}d`, C[i][1], x + 0.22, 5.52, 3.55, 1.15, { size: 12, color: MUTED });
    }
  }

  // =============== BACKUP B · LIMITS (Q&A only) ===============
  {
    const s = slide("OCEAN_B", "Backup · for questions", "Where it breaks — and what we do not claim", [-2.4, -2.6, 6], [9, 3.6, 6], "bk-limits");
    const L = [["LuClock", "Detection, not early warning", "Alerts fire as works happen. We never claim to see stress before it is visible."],
      ["LuLayoutGrid", "10 m pixels", "Patches under ~0.6 ha and young plantings are missed, Bahrain's small stands included."],
      ["LuSearch", "Imagery, not site visits", "Conversions confirmed on dated sub-metre captures, not yet on permits or field records."],
      ["LuActivity", "Simulated losses", "Canopy-cover loss, not leaf stress; every rate shown next to its chance rate."],
      ["LuScanLine", "Hyperspectral", "EnMAP confirms our indices but was not a better classifier (F1 0.74 vs 0.72)."],
      ["LuLeaf", "Carbon", "Area × field density from four sites (2013–14): a stock with a range, never a sequestration rate."]];
    for (let i = 0; i < 6; i++) {
      const x = 0.6 + (i % 3) * 4.1, y = 1.85 + Math.floor(i / 3) * 2.2, o = 1 + Math.floor(i / 3);
      card(s, `a${o}float_l${i}`, x, y, 3.93, 2.0);
      await iconCircle(s, `a${o}float_l${i}ic`, L[i][0], x + 0.22, y + 0.22, 0.56);
      T(s, `a${o}float_l${i}t`, L[i][1], x + 0.95, y + 0.22, 2.85, 0.56, { face: HEAD, size: 15, valign: "middle" });
      T(s, `a${o}float_l${i}d`, L[i][2], x + 0.22, y + 0.92, 3.55, 1.0, { size: 12, color: MUTED });
    }
    T(s, "a3fade_rule", "Rule we kept: no detection rate without its chance rate; no claim of advance warning, field verification or species discrimination.", 0.6, 6.42, 12.1, 0.35, { size: 12, color: TEAL_L });
  }

  // =============== 18 · BACKUP: DEMO VIDEO ===============
  {
    const s = slide("OCEAN_C", "Backup · for questions", "The 2-minute product demo", [8.8, -3, 6], [-2.6, 3.4, 6], "backup");
    const vw = 8.5, vh = vw * 9 / 16, vx = (13.333 - vw) / 2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { objectName: "a1zoom_dframe", x: vx - 0.06, y: 1.85 - 0.06, w: vw + 0.12, h: vh + 0.12, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1.25 }, shadow: shadow() });
    s.addImage({ objectName: "vid_demo", path: path.join(__dirname, "build", "media", "demo.png"), x: vx, y: 1.85, w: vw, h: vh });
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  console.log("wrote", OUT);
})();
