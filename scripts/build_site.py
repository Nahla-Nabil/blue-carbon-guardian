"""Build the public website docs/index.html (served by GitHub Pages from /docs): landing page + interactive monitor + validation story.
Data: analysis/data/site_data.json (written by analysis/09_build_dashboard.py). Images: docs/assets/. Site reports: docs/reports/ (copies of reports/).
Every number on the page is one already approved in README section 8. Run from the repository root:
    python analysis/09_build_dashboard.py && python scripts/build_site.py

v2 (2026-10-22): English / Arabic switch (RTL), light / dark theme, scroll animations and count-up numbers, FAQ.
Text lives in the T dictionary below (key -> English, Arabic); elements carry data-i18n="key" and are filled in English at build time.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.load(open(ROOT / "analysis/data/site_data.json"))
for s in data["series"].values():          # keep the page light: 3 decimals
    for k in ("ndvi", "ndmi", "z", "zc"):
        if k in s: s[k] = [None if v is None else round(v, 3) for v in s[k]]
REPORTS = sorted(int(p.stem.split("_")[1]) for p in (ROOT / "docs/reports").glob("stand_*_report.html"))

# ---------------------------------------------------------------- page text (English, Arabic)
T = {
    # nav
    "nav_mon": ("Monitor", "المراقبة"), "nav_how": ("How it works", "كيف يعمل"), "nav_ev": ("Real events", "أحداث حقيقية"),
    "nav_val": ("Validation", "التحقق"), "nav_carbon": ("Carbon", "الكربون"), "nav_faq": ("FAQ", "أسئلة شائعة"),
    # hero
    "eyebrow": ("Arab Youth Space Hackathon 2026 · Challenge 813 · Finalist", "هاكاثون الشباب العربي للفضاء 2026 · تحدي 813 · متأهل للنهائي"),
    "title": ("Blue Carbon Guardian", "حارس الكربون الأزرق"),
    "sub": ("Tide-aware satellite monitoring for Gulf mangroves. It flags losses stand by stand and in 200&nbsp;m cells, shows where to inspect, and reports the carbon at stake.",
            "مراقبة غابات القرم في الخليج بالأقمار الصناعية مع تصحيح أثر المدّ والجزر. يرصد النظام الخسائر في كل منطقة وفي خلايا بمساحة 200 متر، ويحدّد مواضع التفتيش، ويقدّر الكربون المعرَّض للخطر."),
    "tag_team": ("Team Blue Athar · <span style=\"font-family:'IBM Plex Sans Arabic'\">الأثر الأزرق</span>", "فريق الأثر الأزرق · Blue Athar"), "tag_theme": ("Ecosystem Health &amp; Blue Carbon", "صحة النظم البيئية والكربون الأزرق"),
    "tag_by": ("by Nahla Nabil · Bahrain", "إعداد نهلة نبيل · البحرين"),
    "cta_mon": ("Open the monitor", "افتح لوحة المراقبة"), "cta_video": ("Demo video", "فيديو العرض"), "cta_slides": ("Slides (PDF)", "العرض التقديمي (PDF)"),
    "k1": ("real mangrove losses caught, confirmed on 0.3–0.5 m imagery", "حالات فقدان حقيقية للقرم رُصدت وتأكدت بصور دقتها 0.3–0.5 متر"),
    "k2": ("fewer false alarms than NDVI alone", "إنذارات كاذبة أقل من NDVI وحده"),
    "k3": ("partial loss caught within 60 days (13 % by chance)", "نسبة رصد الخسارة الجزئية خلال 60 يوماً (13% بالصدفة)"),
    "k4": ("carbon stock in the pilot area", "مخزون الكربون في منطقة التجربة"),
    # monitor
    "mon_k": ("Live product · Abu Dhabi pilot", "منتج فعلي · تجربة أبوظبي"), "mon_h": ("The monitor", "لوحة المراقبة"),
    "mon_lede": ("25 mangrove stands (2,281 ha), Sentinel-2 from 2020 to <span id=\"lastobs\">Oct 2026</span>. Click a stand on the map or in the table. Switch to <b>200 m cells</b> to see where inside a stand the change is.",
                 "25 منطقة قرم (2,281 هكتاراً)، وصور Sentinel-2 من 2020 حتى <span id=\"lastobs\">أكتوبر 2026</span>. انقر على أي منطقة في الخريطة أو الجدول، وانتقل إلى <b>خلايا 200 متر</b> لترى موضع التغيّر داخل المنطقة."),
    "b_stands": ("Stands", "المناطق"), "b_cells": ("200 m cells", "خلايا 200 م"),
    "map_note": ("Colour = condition, last 12 months vs 2020–21", "اللون = الحالة: آخر 12 شهراً مقارنةً بـ2020–2021"),
    "lg_stable": ("stable", "مستقر"), "lg_impr": ("improving", "في تحسّن"), "lg_dec": ("decline", "تراجع"), "lg_sev": ("severe decline", "تراجع حاد"), "lg_alert": ("alert active", "إنذار نشط"),
    "read_h": ("How to read it", "كيف تقرأ الخريطة"),
    "read_p": ("<b>Alert</b> = a recent drop below what tide, season and trend predict (combined stand + cell rule). <b>Condition</b> = the last 12 months against the stand's own 2020–21 baseline. A red cell inside a blue stand means: the stand is fine on average, inspect that part.",
               "<b>الإنذار</b> = انخفاض حديث دون ما يتوقعه النموذج وفق المدّ والموسم والاتجاه العام (قاعدة مشتركة للمنطقة والخلايا). <b>الحالة</b> = آخر 12 شهراً مقارنةً بخط أساس المنطقة نفسها لعامي 2020–2021. خلية حمراء داخل منطقة زرقاء تعني: المنطقة سليمة في المتوسط، لكن افحص هذا الجزء."),
    "mon_note": ("Alert rule: stand average ≤ −1.5σ OR any 200 m cell ≤ −3.5σ (about one false-alarm episode per stand-year). Condition and alert are screening results, not field verification. Contains modified Copernicus Sentinel data 2020–2026.",
                 "قاعدة الإنذار: متوسط المنطقة ≤ −1.5σ أو أي خلية ≤ −3.5σ (نحو إنذار كاذب واحد لكل منطقة سنوياً). الحالة والإنذار نتائج فرز أولي، وليست تحققاً ميدانياً. يتضمن بيانات Copernicus Sentinel معدّلة 2020–2026."),
    # risk register (added after expert feedback from the Bahrain Space Agency, 26 Oct 2026)
    "nav_risk": ("Risks", "المخاطر"),
    "risk_k": ("Risk register · ranked by priority", "سجل المخاطر · مرتّب حسب الأولوية"), "risk_h": ("What to inspect first", "ماذا نفتّش أولاً"),
    "risk_lede": ("Every flag becomes a case with a date, a likely cause, a confidence level and an action for the inspector. A case stays open until a person checks it and closes it with a reason.",
                  "كل تنبيه يصبح ملفاً له تاريخ وسبب محتمل ومستوى ثقة وإجراء للمفتش. ويبقى الملف مفتوحاً حتى يفحصه شخص ويغلقه مع ذكر السبب."),
    "risk_rule": ("<b>Urgent</b>: loss confirmed on sub-metre imagery and ≥ 10 ha of cells to inspect. <b>Monitor</b>: a smaller confirmed loss, or cells nobody has checked yet. <b>Closed</b>: checked, with the reason recorded. Carbon at stake = area × 108 t C/ha (upper bound where whole cells are counted). Prioritisation added after expert evaluation and feedback from the Bahrain Space Agency.",
                  "<b>عاجل</b>: خسارة مؤكدة بصور دون المتر و10 هكتارات أو أكثر من الخلايا للتفتيش. <b>للمتابعة</b>: خسارة مؤكدة أصغر، أو خلايا لم يفحصها أحد بعد. <b>مغلق</b>: فُحص وسُجّل السبب. الكربون المعرّض للخطر = المساحة × 108 طن/هكتار (حدّ أعلى حين تُحسب الخلايا كاملة). أُضيف ترتيب الأولويات بعد تقييم وملاحظات خبراء وكالة البحرين للفضاء."),
    # regional context (why it matters): pledges, area, pressure, market; every figure sourced below the cards
    "nav_reg": ("Region", "المنطقة"),
    "reg_k": ("Why it matters in the region", "لماذا يهمّ في المنطقة"), "reg_h": ("Big national pledges, and a coast that is changing fast", "تعهّدات وطنية كبيرة، وساحل يتغيّر بسرعة"),
    "reg_lede": ("Gulf states have committed to planting hundreds of millions of mangroves while their coasts are being developed. Both need a way to see, every few days, where mangroves are holding and where they are being lost.",
                 "التزمت دول الخليج بزراعة مئات الملايين من أشجار القرم، في الوقت الذي تتطوّر فيه سواحلها. وكلا الأمرين يحتاج إلى وسيلة ترى كل بضعة أيام أين يصمد القرم وأين يُفقد."),
    "ae_n": ("UAE", "الإمارات"), "ae_p": ("mangroves by 2030 (Ministry of Climate Change and Environment, COP26, 2021). Abu Dhabi Mangrove Initiative (EAD, 2022) and the first GCC mangrove monitoring guide (EAD with IUCN, Feb 2026).",
                                       "شجرة قرم بحلول 2030 (وزارة التغيّر المناخي والبيئة، COP26، 2021). ومبادرة أبوظبي للقرم (هيئة البيئة – أبوظبي، 2022)، وأول دليل خليجي لمراقبة القرم (هيئة البيئة مع IUCN، فبراير 2026)."),
    "sa_n": ("Saudi Arabia", "السعودية"), "sa_p": ("mangroves by 2030 (Saudi Green Initiative). Red Sea Global alone aims for 50 million by 2030.",
                                                 "شجرة قرم بحلول 2030 (مبادرة السعودية الخضراء). وتستهدف البحر الأحمر الدولية وحدها 50 مليوناً بحلول 2030."),
    "bh_n": ("Bahrain", "البحرين"), "bh_p": ("its mangroves by 2035, pledged at COP26 (2021) on the path to net zero by 2060. Its stands are small, so they need higher-resolution imagery.",
                                            "مضاعفة القرم أربع مرات بحلول 2035، تعهّد في COP26 (2021) ضمن مسار الحياد الكربوني بحلول 2060. ومناطقها صغيرة، فتحتاج صوراً أعلى دقة."),
    "ar_n": ("Arab region", "المنطقة العربية"), "ar_p": ("km² of mangrove on the Gulf (≈ 165) and Red Sea (≈ 200) coasts, and monitoring is still “uneven” (Frontiers in Marine Science, 2025).",
                                                       "كم² من القرم على سواحل الخليج (≈ 165) والبحر الأحمر (≈ 200)، والمراقبة ما زالت «غير منتظمة» (Frontiers in Marine Science، 2025)."),
    "pr1": ("of our 25 pilot stands lost part of their mangrove to coastal development between 2022 and 2025, each confirmed on sub-metre imagery (our own result).",
            "من مناطقنا التجريبية الـ25 فقدت جزءاً من قرمها لصالح التطوير الساحلي بين 2022 و2025، وكلها مؤكدة بصور دون المتر (نتيجتنا)."),
    "pr2": ("per tonne of CO₂e: blue-carbon credit prices in 2024–25 (S&P Global Platts), so a hectare that is lost is also value that is lost.",
            "لكل طن مكافئ CO₂: أسعار أرصدة الكربون الأزرق في 2024–2025 (S&P Global Platts)، فالهكتار المفقود قيمة مفقودة أيضاً."),
    "reg_src": ("Sources", "المصادر"),
    # expert evaluation (Bahrain Space Agency official statement, approved for use 26 Oct 2026)
    "bsa_k": ("Expert Evaluation and Feedback", "تقييم وملاحظات الخبراء"), "bsa_h": ("Bahrain Space Agency", "وكالة البحرين للفضاء"),
    "bsa_q": ("“The Bahrain Space Agency commends Ms. Nahla Nabil for presenting Blue Carbon Guardian, an innovative project using Earth Observation data to monitor regional mangrove ecosystems. The Agency provided specialised assessment and technical feedback, reaffirming its commitment to supporting research and innovation that advance Bahrain's environmental objectives and sustainability goals.”",
              "«تشيد وكالة البحرين للفضاء بالآنسة نهلة نبيل لتقديمها مشروع Blue Carbon Guardian، والذي يوظف بيانات رصد الأرض بشكل مبتكر لمراقبة النظم البيئية لأشجار القرم على مستوى المنطقة. وقد قدمت الوكالة تقييماً متخصصاً وملاحظات فنية، تأكيداً على دورها في دعم المبادرات البحثية والابتكارات التقنية التي تسهم في تحقيق الأهداف البيئية وتعزيز الاستدامة في مملكة البحرين.»"),
    "bsa_n": ("Official statement of the Bahrain Space Agency. Bahrain has pledged to quadruple its mangroves by 2035; its stands are smaller than Abu Dhabi's, so monitoring them needs higher-resolution imagery than open 10 m data provides.",
              "بيان رسمي من وكالة البحرين للفضاء. وقد تعهّدت البحرين بمضاعفة أشجار القرم أربع مرات بحلول 2035؛ ومناطقها أصغر من مناطق أبوظبي، لذا تحتاج مراقبتها إلى صور أعلى دقة مما توفّره البيانات المفتوحة بدقة 10 أمتار."),
    # how
    "how_k": ("How it works", "كيف يعمل"), "how_h": ("From satellite pixels to an inspection decision", "من بكسلات القمر الصناعي إلى قرار التفتيش"),
    "how_lede": ("On Gulf tidal flats the tide, not the trees, drives most of the change in a satellite index. A simple monitor raises a false alarm at every high tide. We model the tide out first.",
                 "على السواحل المدّية في الخليج، يسبّب المدُّ معظمَ التغيّر في مؤشرات الأقمار الصناعية، لا الأشجار نفسها. والمراقبة البسيطة تطلق إنذاراً كاذباً مع كل مدّ مرتفع، لذلك نعزل أثر المدّ أولاً."),
    "s1h": ("Stands &amp; cells", "المناطق والخلايا"), "s1p": ("WorldCover 2021 mangrove patches ≥ 3 ha, cut into 200 m cells; interior pixels only.", "بقع القرم من WorldCover 2021 (≥ 3 هكتارات)، مقسّمة إلى خلايا 200 متر، مع البكسلات الداخلية فقط."),
    "s2h": ("Sentinel-2 series", "سلسلة Sentinel-2"), "s2p": ("778 dates 2020–26, read in place from the cloud: NDVI, red edge, SWIR moisture, wetness.", "778 تاريخاً بين 2020 و2026 تُقرأ مباشرة من السحابة: الاخضرار، والحافة الحمراء، والرطوبة، ومؤشر الغمر."),
    "s3h": ("Tide-aware model", "نموذج يصحّح أثر المدّ"), "s3p": ("Robust trend + season + tide terms per stand and cell, refitted every month on past data only.", "انحدار متين يجمع الاتجاه العام والموسم والمدّ لكل منطقة وخلية، ويُحدَّث شهرياً على بيانات الماضي فقط."),
    "s4h": ("Alert &amp; condition", "الإنذار والحالة"), "s4p": ("Stand ≤ −1.5σ OR any cell ≤ −3.5σ; condition = last 12 months vs 2020–21.", "المنطقة ≤ −1.5σ أو أي خلية ≤ −3.5σ؛ والحالة = آخر 12 شهراً مقارنةً بـ2020–2021."),
    "s5h": ("Decision", "القرار"), "s5p": ("Cell map, carbon at stake, dashboard, site reports, alert API (concept).", "خريطة الخلايا، والكربون المعرّض للخطر، ولوحة المراقبة، وتقارير المواقع، وواجهة إنذار (مفهوم)."),
    "noise_h": ("Noise removed by the tide model", "الضجيج الذي يزيله نموذج المدّ"), "noise_n": ("Robust residual noise, 25 stands, 2020–2026", "الضجيج المتبقي، 25 منطقة، 2020–2026"),
    "textbook": ("<b>Against NDVI alone</b> (no tide model), same alert rule, same stands: <b>1.61</b> false alarms per stand-year vs <b>0.96</b> for ours, 40 % fewer.",
                 "<b>مقارنةً بـNDVI وحده</b> (دون نموذج المدّ)، بنفس قاعدة الإنذار ونفس المناطق: <b>1.61</b> إنذار كاذب لكل منطقة سنوياً مقابل <b>0.96</b> لنظامنا، أي أقل بنسبة 40%."),
    "cells_h": ("Why cells matter", "لماذا الخلايا مهمة"),
    "cells_p": ("A stand average hides a partial loss. Stand 9 reads <b>“stable”</b> on average while <b>8 of its 28 cells</b> are in severe decline. <b>3 of the 5</b> real conversions were found <b>only</b> at cell level.",
                "متوسط المنطقة يُخفي الخسارة الجزئية. فالمنطقة 9 تبدو <b>«مستقرة»</b> في المتوسط، بينما <b>8 من خلاياها الـ28</b> في تراجع حاد. و<b>3 من الحالات الخمس</b> الحقيقية لم تُرصد <b>إلا</b> على مستوى الخلايا."),
    "c_both": ("stand + cells", "المنطقة + الخلايا"), "c_stand": ("stand average alone", "متوسط المنطقة وحده"), "c_chance": ("by chance", "بالصدفة"),
    "cells_n": ("Partial loss caught within 60 days (simulated, ±7 points).", "رصد الخسارة الجزئية خلال 60 يوماً (محاكاة، ±7 نقاط)."),
    # events
    "ev_k": ("Validation 1 · real events", "التحقق 1 · أحداث حقيقية"), "ev_h": ("Five real conversions, confirmed on sub-metre imagery", "خمس حالات إزالة حقيقية، مؤكدة بصور دون المتر"),
    "ev_lede": ("All five are coastal developments (reclamation, canals, lagoons). Dated WorldView-2/3 and Legion-1 captures (0.3–0.5 m) confirm each one. At every site the alert began <b>between the last intact and the first disturbed capture</b>: detection of works as they happen, not advance warning.",
                "الحالات الخمس كلها مشاريع تطوير ساحلي (ردم وقنوات وبحيرات)، وتؤكدها صور مؤرّخة من WorldView-2/3 وLegion-1 (0.3–0.5 متر). وفي كل موقع بدأ الإنذار <b>بين آخر صورة سليمة وأول صورة تُظهر الأعمال</b>: أي رصد الأعمال أثناء حدوثها، لا تنبؤ مسبق."),
    "strip_h": ("Stand 5 through time (Sentinel-2)", "المنطقة 5 عبر الزمن (Sentinel-2)"),
    "f1": ("<b>Nov 2021</b> · intact fringe", "<b>نوفمبر 2021</b> · حافة سليمة"), "f2": ("<b>Oct 2022</b> · works start, alert fires (25 Oct)", "<b>أكتوبر 2022</b> · بدء الأعمال وانطلاق الإنذار (25 أكتوبر)"),
    "f3": ("<b>Jun 2023</b> · canals cut", "<b>يونيو 2023</b> · شق القنوات"), "f4": ("<b>May 2026</b> · development", "<b>مايو 2026</b> · مشروع عمراني"),
    "e5h": ("Stand 5 · reclamation with finger canals", "المنطقة 5 · ردم مع قنوات متفرعة"), "e5p": ("26–62 ha converted (Sentinel-2 and EnMAP estimates). Alert from 25 Oct 2022.", "تحوّل 26–62 هكتاراً (تقديرات Sentinel-2 وEnMAP). الإنذار منذ 25 أكتوبر 2022."),
    "e9h": ("Stand 9 · canal development in the south-east", "المنطقة 9 · قنوات في الجنوب الشرقي"), "e9p": ("Average “stable”; 8 of 28 cells in severe decline. Alert from 7 Dec 2022.", "المتوسط «مستقر»، و8 من 28 خلية في تراجع حاد. الإنذار منذ 7 ديسمبر 2022."),
    "e12h": ("Stand 12 · found only by the cells", "المنطقة 12 · رصدتها الخلايا وحدها"), "e12p": ("New canal and reclamation at the southern edge. Alert from 17 Dec 2022.", "قناة وردم جديدان على الحافة الجنوبية. الإنذار منذ 17 ديسمبر 2022."),
    "e18h": ("Stand 18 · found only by the cells", "المنطقة 18 · رصدتها الخلايا وحدها"), "e18p": ("The same development reaches it in 2025. Alert from 29 Oct 2024. (Stand 6, the fifth event, is in the timeline below.)", "يصلها المشروع نفسه في 2025. الإنذار منذ 29 أكتوبر 2024. (المنطقة 6، الحالة الخامسة، في الخط الزمني أدناه.)"),
    "gantt_h": ("When did the alert start?", "متى بدأ الإنذار؟"), "gantt_n": ("Bar = last intact capture → first capture with works. Diamond = start of our alert.", "الشريط = من آخر صورة سليمة إلى أول صورة تُظهر الأعمال. المعيّن = بداية إنذارنا."),
    # validation
    "val_k": ("Validation 2 &amp; 3 · against chance, unseen stands, hyperspectral", "التحقق 2 و3 · مقارنةً بالصدفة، ومناطق جديدة، وبيانات فائقة الطيف"),
    "val_h": ("Every rate comes with its chance rate", "كل نسبة تُعرض بجانب نسبة الصدفة"),
    "val_lede": ("We injected artificial loss into real stands with no known change, holding false alarms to about one per stand-year. A detection counts only if a <b>new</b> alert starts after the loss begins; the same test with <b>no</b> loss gives the chance rate.",
                 "زرعنا خسارة اصطناعية في مناطق حقيقية لم يحدث فيها تغيير، مع إبقاء الإنذارات الكاذبة عند نحو إنذار واحد لكل منطقة سنوياً. ولا يُحتسب الرصد إلا إذا بدأ إنذار <b>جديد</b> بعد بدء الخسارة، ويعطي الاختبار نفسه <b>دون</b> خسارة نسبةَ الصدفة."),
    "sim_n": ("~160–240 trials per row (±7 points). We withdrew our own first figure (58 % / 90 %) after a null test showed its metric counted alerts that were already running.",
              "نحو 160–240 تجربة لكل صف (±7 نقاط). وسحبنا رقمنا الأول (58% / 90%) بعدما أظهر اختبار الصفر أن مقياسه كان يحتسب إنذارات قائمة أصلاً."),
    "cal_k": ("Calibrated · 25 pilot stands", "المعايرة · 25 منطقة تجريبية"), "cal_n": ("false-alarm episodes per stand-year (117 stand-years)", "إنذار كاذب لكل منطقة سنوياً (117 سنة-منطقة)"),
    "uns_k": ("Unseen · 65 stands, thresholds fixed", "مناطق جديدة · 65 منطقة بحدود ثابتة"), "uns_n": ("per stand-year over 305 stand-years, including Saudi Arabia's Tarut Bay", "لكل منطقة سنوياً عبر 305 سنة-منطقة، منها خليج تاروت في السعودية"),
    "en_k": ("Hyperspectral · EnMAP, 224 bands", "فائق الطيف · EnMAP، 224 نطاقاً"), "en_h": ("An independent check, and a material fingerprint", "تحقق مستقل وبصمة للمادة"),
    "sim813": ("<b>Ready for Satellite 813:</b> with only 813's 400–1700 nm range (simulated from EnMAP, not real 813 data), 97 % of the converted pixels still match sand or fill, against 0.4 % of the intact ones, and sand is told apart from buildings better than with Sentinel-2-like bands (F1 0.91 vs 0.88).",
               "<b>جاهز للقمر 813:</b> باستخدام نطاق 813 وحده (400–1700 نانومتر، بمحاكاة من EnMAP لا ببيانات 813 حقيقية)، بقيت 97% من البكسلات المُزالة تطابق الرمل أو الردم مقابل 0.4% فقط من السليمة، وتمييز الرمل من المباني أفضل منه بنطاقات شبيهة بـSentinel-2 (F1 0.91 مقابل 0.88)."),
    "en_p": ("<b>r = 0.84–0.99</b> between EnMAP and our Sentinel-2 indices on the same dates. The converted part of stand 5 turns from a vegetation spectrum into a bright, mineral-like one: reclamation, not dieback. As a classifier, EnMAP did not beat multispectral bands (F1 0.74 vs 0.72), and we say so.",
             "<b>r = 0.84–0.99</b> بين EnMAP ومؤشرات Sentinel-2 في التواريخ نفسها. ويتحوّل الجزء المُزال من المنطقة 5 من طيف نباتي إلى طيف ساطع شبيه بالمعادن: ردم لا ذبول. وكمصنِّف، لم يتفوّق EnMAP على النطاقات متعددة الأطياف (F1 0.74 مقابل 0.72)، ونذكر ذلك بوضوح."),
    # carbon
    "car_k": ("Impact · carbon", "الأثر · الكربون"), "car_h": ("Carbon stock, grounded in field measurements", "مخزون كربون مبني على قياسات ميدانية"),
    "c1": ("t C/ha local mean density (90 % CI 79–138), 24 field plots at 4 sites", "طن كربون/هكتار متوسط الكثافة المحلية (فاصل ثقة 90%: 79–138)، 24 قطعة ميدانية في 4 مواقع"),
    "c2": ("carbon in the pilot area, 2,281 ha (90 % range 180–316)", "كربون في منطقة التجربة، 2,281 هكتاراً (المدى 180–316)"),
    "c3": ("of it is in the soil (89 of 108 t C/ha): losing a stand exposes what is underneath", "منه في التربة (89 من 108 طن/هكتار): فقدان القرم يكشف ما تحته"),
    "c4": ("carbon stock on the 26–62 ha converted in stand 5", "مخزون الكربون في الـ26–62 هكتاراً المُزالة في المنطقة 5"),
    "car_n": ("Carbon is area × field density (Schile et al. 2016, CC0): a stock with a range, never a sequestration rate. We tested whether Sentinel-2 indices predict field tree carbon: too weak (best ρ = 0.38).",
              "الكربون = المساحة × الكثافة الميدانية (Schile وآخرون 2016، CC0): مخزون مع نطاق، لا معدل احتجاز. واختبرنا قدرة مؤشرات Sentinel-2 على التنبؤ بكربون الأشجار الميداني: العلاقة ضعيفة (أفضل ρ = 0.38)."),
    # offer
    "off_k": ("Who it is for", "لمن صُمّم"), "off_h": ("A monitoring service with honest unit economics", "خدمة مراقبة باقتصاديات واضحة"),
    "u1": ("Environment agencies", "هيئات البيئة"), "u1d": ("<b>Decision:</b> which stands to inspect this month?", "<b>القرار:</b> أي المناطق نفتّش هذا الشهر؟"), "u1t": ("Today: periodic field surveys, one-off studies.", "اليوم: مسوح ميدانية دورية ودراسات منفردة."),
    "u2": ("Planting &amp; carbon developers", "مطوّرو التشجير ومشاريع الكربون"), "u2d": ("<b>Decision:</b> is the carbon stock we report still there?", "<b>القرار:</b> هل ما زال مخزون الكربون الذي نعلنه موجوداً؟"), "u2t": ("Today: field plots and drone surveys, campaign by campaign.", "اليوم: قطع ميدانية ومسوح بالطائرات المسيّرة، حملة تلو حملة."),
    "u3": ("Coastal developers &amp; regulators", "المطوّرون الساحليون والجهات الرقابية"), "u3d": ("<b>Decision:</b> did construction stay outside the mangrove line?", "<b>القرار:</b> هل بقيت الأعمال خارج حدود القرم؟"), "u3t": ("Today: comparing two dated images by eye.", "اليوم: مقارنة صورتين مؤرختين بالعين."),
    "p1k": ("Monitor", "المراقبة"), "p1": ("per site / year: alert, cell map, condition, carbon, monthly reports", "لكل موقع سنوياً: إنذار، وخريطة خلايا، وحالة، وكربون، وتقارير شهرية"),
    "p2k": ("Evidence", "الأدلة"), "p2": ("per site / year: + sub-metre check of every alert, audit pack", "لكل موقع سنوياً: + تحقق بصور دون المتر لكل إنذار، وحزمة تدقيق"),
    "p3k": ("Development watch", "مراقبة المشاريع"), "p3": ("per construction project / year", "لكل مشروع إنشائي سنوياً"),
    "p4k": ("Cost to serve", "تكلفة التشغيل"), "p4": ("per site / year (compute &lt; $5 measured)", "لكل موقع سنوياً (الحوسبة أقل من 5 دولارات، مقيسة)"),
    "off_n": ("Prices are hypotheses for a pilot. Global Mangrove Watch offers free monthly loss alerts; we are complementary (tide-aware, calibrated, cell level, carbon and reports).",
              "الأسعار فرضيات لتجربة أولى. ويقدّم Global Mangrove Watch إنذارات شهرية مجانية بالخسارة، ونظامنا مكمّل له (يصحّح المدّ، ومُعايَر، وعلى مستوى الخلايا، مع الكربون والتقارير)."),
    "bp": ("Full business plan", "خطة العمل الكاملة"),
    # limits
    "lim_k": ("Limits, stated honestly", "الحدود، بصراحة"), "lim_h": ("What we do not claim", "ما لا ندّعيه"),
    "l1h": ("Detection, not early warning", "رصد لا إنذار مبكر"), "l1p": ("Alerts fire as works happen.", "تنطلق الإنذارات أثناء حدوث الأعمال."),
    "l2h": ("10 m pixels", "بكسلات 10 أمتار"), "l2p": ("Patches under ~0.6 ha and young plantings are missed, Bahrain's small stands included.", "تفوته البقع الأصغر من نحو 0.6 هكتار والزراعات الحديثة، ومنها مناطق البحرين الصغيرة."),
    "l3h": ("Imagery, not site visits", "صور لا زيارات ميدانية"), "l3p": ("Matching alerts to permits with a partner is the first pilot task.", "مطابقة الإنذارات مع التراخيص بالتعاون مع شريك هي أول مهمة في التجربة."),
    # FAQ
    "faq_k": ("FAQ", "أسئلة شائعة"), "faq_h": ("Questions people ask", "أسئلة يطرحها الناس"),
    "q1": ("What does Blue Carbon Guardian do?", "ماذا يفعل حارس الكربون الأزرق؟"),
    "a1": ("It reads free Sentinel-2 satellite images every ~5 days, flags mangrove stands (and 200 m cells inside them) that drop below what tide, season and trend predict, and reports where to inspect and how much carbon is at stake.",
           "يقرأ صور Sentinel-2 المجانية كل خمسة أيام تقريباً، وينبّه إلى مناطق القرم (والخلايا بمساحة 200 متر داخلها) التي تنخفض دون ما يتوقعه النموذج وفق المدّ والموسم والاتجاه العام، ويحدّد مواضع التفتيش وحجم الكربون المعرّض للخطر."),
    "q2": ("Why does the tide matter so much?", "لماذا للمدّ كل هذه الأهمية؟"),
    "a2": ("At high tide, water under the canopy makes healthy mangroves look less green from space, so a simple monitor confuses the tide with tree loss. Modelling the tide cuts index noise by 29–35 % and false alarms by 40 % versus NDVI alone.",
           "عند ارتفاع المدّ، تجعل المياه تحت الأشجار القرمَ السليم يبدو أقل اخضراراً من الفضاء، فتخلط المراقبة البسيطة بين المدّ وفقدان الأشجار. ونمذجة المدّ تخفّض ضجيج المؤشرات بنسبة 29–35%، والإنذارات الكاذبة بنسبة 40% مقارنةً بـNDVI وحده."),
    "q3": ("What are the 200 m cells for?", "ما فائدة خلايا 200 متر؟"),
    "a3": ("An average over a whole stand hides a loss on one side of it. Each stand is split into 4-hectare cells, so the alert says exactly where to send an inspector. Three of the five real losses were found only by the cells.",
           "متوسط المنطقة كلها يُخفي خسارة في أحد أطرافها، لذلك تُقسَّم كل منطقة إلى خلايا مساحتها 4 هكتارات، فيحدّد الإنذار بدقة أين يُرسَل المفتش. وثلاث من الحالات الخمس الحقيقية لم ترصدها إلا الخلايا."),
    "q4": ("Is it an early-warning system?", "هل هو نظام إنذار مبكر؟"),
    "a4": ("No, and we say so. It detects works while they happen: at every confirmed site the alert began between the last intact and the first disturbed sub-metre image. We never claim it sees stress before it is visible.",
           "لا، ونقول ذلك بوضوح. فهو يرصد الأعمال أثناء حدوثها: ففي كل موقع مؤكد بدأ الإنذار بين آخر صورة سليمة وأول صورة تُظهر الأعمال. ولا ندّعي أنه يرى الإجهاد قبل ظهوره."),
    "q5": ("How do you know the alerts are right?", "كيف تتأكدون من صحة الإنذارات؟"),
    "a5": ("Three ways: five real conversions confirmed on dated 0.3–0.5 m imagery; simulated losses scored against a chance baseline (73 % vs 13 %); and thresholds frozen and run on 65 stands the model never saw, where false alarms stayed at 0.79 per stand-year.",
           "بثلاث طرق: خمس حالات حقيقية مؤكدة بصور مؤرّخة دقتها 0.3–0.5 متر؛ وخسائر محاكاة تُقارن بنسبة الصدفة (73% مقابل 13%)؛ وحدود ثابتة طُبّقت على 65 منطقة لم يرها النموذج، وبقيت الإنذارات الكاذبة فيها عند 0.79 لكل منطقة سنوياً."),
    "q6": ("What data does it use, and what about Satellite 813?", "ما البيانات المستخدمة، وماذا عن القمر 813؟"),
    "a6": ("Free Sentinel-2 imagery for monitoring, EnMAP hyperspectral as an independent check, ESA WorldCover for outlines, and published field plots for carbon. Every index we use sits inside Satellite 813's ~400–1700 nm range, so 813 can explain what a flagged cell became. We simulated its band range with EnMAP: the stand-5 loss still reads as sand and fill (97 % of converted pixels, 0.4 % of intact ones). Real 813 scenes are the next step.",
           "صور Sentinel-2 المجانية للمراقبة، وبيانات EnMAP فائقة الطيف للتحقق المستقل، وESA WorldCover لحدود المناطق، وقياسات ميدانية منشورة للكربون. وكل المؤشرات المستخدمة تقع ضمن نطاق القمر 813 (نحو 400–1700 نانومتر)، فيمكنه تفسير ما آلت إليه الخلية المنبَّه عليها. وقد حاكينا نطاقاته باستخدام EnMAP: فبقيت خسارة المنطقة 5 تُقرأ رملاً وردماً (97% من البكسلات المُزالة، و0.4% فقط من السليمة). والخطوة التالية صور 813 حقيقية."),
    "q7": ("Does it work in Bahrain?", "هل يعمل في البحرين؟"),
    "a7": ("Bahrain has pledged to quadruple its mangroves by 2035, so the need is real. But not yet at 10 m: most of Bahrain's mangrove patches are under 4 hectares, too small for Sentinel-2 pixels. That needs very-high-resolution imagery (a few metres or finer). Satellite 813, at 20 m, adds spectral detail rather than spatial detail, so for Bahrain it would explain what changed, not find smaller patches.",
           "تعهّدت البحرين بمضاعفة أشجار القرم أربع مرات بحلول 2035، فالحاجة حقيقية. لكن ليس بعد بدقة 10 أمتار: فمعظم بقع القرم في البحرين أصغر من 4 هكتارات، أي أصغر من أن تلتقطها بكسلات Sentinel-2. ويتطلب ذلك صوراً عالية الدقة جداً (بضعة أمتار أو أقل). أما القمر 813 فدقته 20 متراً، ويضيف تفاصيل طيفية لا مكانية، أي أنه يفسّر ما الذي تغيّر، لكنه لا يرصد البقع الأصغر."),
    "q8": ("Can I check or reproduce the results?", "هل يمكنني التحقق من النتائج أو إعادة إنتاجها؟"),
    "a8": ("Yes. The code, notebook, example input and outputs are public under the MIT licence; the notebook re-runs end to end in about 24 seconds on a clean machine with the same numbers.",
           "نعم. الكود والدفتر البرمجي والمدخلات والمخرجات النموذجية منشورة للعموم بترخيص MIT، ويُعاد تشغيل الدفتر كاملاً في نحو 24 ثانية على جهاز جديد بالأرقام نفسها."),
    "q9": ("Who is it for, and what would it cost?", "لمن هو، وكم سيكلّف؟"),
    "a9": ("Environment agencies, planting and carbon-project developers, and coastal regulators. Pilot hypothesis: about USD 12k per site per year, with a measured compute cost under USD 5 per site per year.",
           "هيئات البيئة، ومطوّرو التشجير ومشاريع الكربون، والجهات الرقابية الساحلية. والفرضية للتجربة الأولى: نحو 12 ألف دولار لكل موقع سنوياً، بتكلفة حوسبة مقيسة أقل من 5 دولارات لكل موقع سنوياً."),
    # footer
    "ft_code": ("Code &amp; notebook (GitHub)", "الكود والدفتر البرمجي (GitHub)"), "ft_api": ("Alert API concept", "مفهوم واجهة الإنذار"), "ft_feed": ("Live alert feed (JSON)", "خلاصة الإنذارات (JSON)"),
    "feed": ("Updated with every new Sentinel-2 image; latest data and alerts as JSON:", "يُحدَّث مع كل صورة Sentinel-2 جديدة؛ آخر البيانات والإنذارات بصيغة JSON:"), "ft_sum": ("Arabic summary (PDF)", "ملخص عربي (PDF)"),
}

# dynamic strings used by the monitor script
DYN = {
    "en": {"stand": "Stand", "stable": "stable", "improving": "improving", "decline": "decline", "severe decline": "severe decline",
           "noalert": "No active alert.", "alertnow": "Alert active now.", "eps": "alert episodes 2022–26 (combined stand + cell rule).",
           "area": "stand area", "stock": "carbon stock", "ndvi": "NDVI, last 12 months vs 2020–21", "of": "of", "cells": "cells", "indecl": "in decline",
           "toinspect": "ha to inspect", "score": "Alert score, 2022–2026", "avg": "stand average", "worst": "worst 200 m cell", "alert": "alert",
           "tcndvi": "Tide-corrected NDVI, monthly 2020–2026", "report": "Open the site report", "reports": "Printable site reports are generated for any stand (examples: stands ",
           "th": ["Stand", "Area (ha)", "Condition", "NDVI change", "Cells in decline", "Alert episodes 2022–26", "Carbon (kt C)"],
           "raw": "raw", "tide": "tide model", "chance": "by chance",
           "sim": [["A tenth of a stand loses half its canopy", "within 60 days"], ["A whole stand loses 10 % of its canopy", "within 6 months"], ["A whole stand loses 20 % of its canopy", "within 6 months"]],
           "locale": "en-GB", "theme_l": "Light", "theme_d": "Dark",
           "urgent": "Urgent", "monitor": "Monitor", "closed": "Closed", "opened": "Open since", "closedon": "Closed on", "cause": "Likely cause",
           "conf": "Confidence", "action": "Inspector action", "toinsp": "to inspect", "atstake": "carbon at stake", "upto": "up to", "view": "View on the map"},
    "ar": {"stand": "المنطقة", "stable": "مستقر", "improving": "في تحسّن", "decline": "تراجع", "severe decline": "تراجع حاد",
           "noalert": "لا إنذار نشط.", "alertnow": "إنذار نشط الآن.", "eps": "فترات إنذار 2022–2026 (قاعدة المنطقة + الخلايا).",
           "area": "مساحة المنطقة", "stock": "مخزون الكربون", "ndvi": "NDVI، آخر 12 شهراً مقابل 2020–2021", "of": "من", "cells": "خلية", "indecl": "في تراجع",
           "toinspect": "هكتار للتفتيش", "score": "مؤشر الإنذار، 2022–2026", "avg": "متوسط المنطقة", "worst": "أسوأ خلية 200 م", "alert": "إنذار",
           "tcndvi": "NDVI بعد تصحيح المدّ، شهرياً 2020–2026", "report": "افتح تقرير الموقع", "reports": "تُولَّد تقارير قابلة للطباعة لأي منطقة (أمثلة: المناطق ",
           "th": ["المنطقة", "المساحة (هكتار)", "الحالة", "تغيّر NDVI", "خلايا في تراجع", "فترات الإنذار 2022–26", "الكربون (ألف طن)"],
           "raw": "دون تصحيح", "tide": "مع نموذج المدّ", "chance": "بالصدفة",
           "sim": [["عُشر المنطقة يفقد نصف غطائه", "خلال 60 يوماً"], ["المنطقة كلها تفقد 10% من غطائها", "خلال 6 أشهر"], ["المنطقة كلها تفقد 20% من غطائها", "خلال 6 أشهر"]],
           "locale": "ar-u-nu-latn", "theme_l": "فاتح", "theme_d": "داكن",
           "urgent": "عاجل", "monitor": "للمتابعة", "closed": "مغلق", "opened": "مفتوح منذ", "closedon": "أُغلق في", "cause": "السبب المحتمل",
           "conf": "مستوى الثقة", "action": "إجراء المفتش", "toinsp": "للتفتيش", "atstake": "كربون معرّض للخطر", "upto": "حتى", "view": "اعرضها على الخريطة"},
}

PAGE = r"""<!doctype html>
<html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blue Carbon Guardian</title>
<meta name="description" content="Tide-aware satellite monitoring for Gulf mangroves: alerts per stand and per 200 m cell, carbon at stake, validated on real events.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>/* theme + language before first paint (no flash) */
(function(){var t=null,l=null;try{t=localStorage.getItem("bcg-theme");l=localStorage.getItem("bcg-lang")}catch(e){}
 if(!t)t=(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches)?"dark":"light";
 document.documentElement.setAttribute("data-theme",t);if(l==="ar"){document.documentElement.lang="ar";document.documentElement.dir="rtl"}})();</script>
<style>
:root{--navy:#06235A;--blue:#1E6FD9;--cyan:#0EA5E9;--coral:#FF4D6D;--amber:#FFB020;--green:#2E9E6B;
  --bg:#FFFFFF;--surface:#FFFFFF;--soft:#F4F8FF;--ice:#E8F2FF;--line:#D6E6FF;--ink:#0B1B3F;--head:#06235A;--muted:#4A5F86;--grid:#E6EEF9;--mapbg:#EEF5FF;
  --shadow:0 10px 30px rgba(10,61,145,.07);--accent:#1E6FD9;--seg:#E8F2FF;--segon:#FFFFFF;--th:#06235A}
:root[data-theme="dark"]{--bg:#050C1F;--surface:#0B1631;--soft:#0E1C3D;--ice:#132650;--line:#1D3263;--ink:#E3EDFF;--head:#F2F7FF;--muted:#9DB3D9;--grid:#1A2C55;--mapbg:#0A1734;
  --shadow:0 10px 30px rgba(0,0,0,.35);--accent:#5AA9FF;--seg:#132650;--segon:#1F3A72;--th:#132650}
*{box-sizing:border-box;margin:0}
html{scroll-behavior:smooth}
body{font-family:'IBM Plex Sans',system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6;transition:background .3s,color .3s}
html[lang="ar"] body{font-family:'IBM Plex Sans Arabic','IBM Plex Sans',system-ui,sans-serif;line-height:1.8}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.k{font-family:'IBM Plex Mono',monospace;font-size:12.5px;letter-spacing:3px;text-transform:uppercase;color:var(--accent);font-weight:600}
html[lang="ar"] .k{font-family:inherit;letter-spacing:0;font-size:14px}
h2{font-size:clamp(28px,4vw,42px);line-height:1.2;color:var(--head);margin:8px 0 12px}
h4{color:var(--head)}
.lede{font-size:18px;color:var(--muted);max-width:780px}
section{padding:88px 0}
.alt{background:var(--soft)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow);padding:24px;transition:transform .25s,box-shadow .25s,background .3s,border-color .3s}
.card.lift:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(10,61,145,.13)}
.dark{background:linear-gradient(135deg,#06235A,#0B4A9E)!important;color:#fff;border:none!important}
.dark h4,.dark b{color:#fff}.dark .note,.dark p{color:#BFDFFF}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.big{font-size:42px;font-weight:700;line-height:1.05;background:linear-gradient(90deg,#0A3D91,#1E6FD9 60%,#0EA5E9);-webkit-background-clip:text;background-clip:text;color:transparent}
:root[data-theme="dark"] .big{background:linear-gradient(90deg,#7FC1FF,#A9E4FF);-webkit-background-clip:text;background-clip:text}
.pill{display:inline-block;padding:4px 12px;border-radius:999px;font-size:13px;font-weight:600;background:var(--ice);color:var(--accent);border:1px solid var(--line)}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:12px;font-weight:600;font-size:15px;transition:transform .2s,box-shadow .2s}
.btn:hover{transform:translateY(-2px)}
.btn.p{background:#fff;color:#06235A;box-shadow:0 8px 24px rgba(0,0,0,.2)} .btn.s{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.35)}
.note{font-size:13.5px;color:var(--muted)}
/* nav */
nav{position:sticky;top:0;z-index:50;background:rgba(3,11,38,.86);backdrop-filter:blur(12px);border-bottom:1px solid rgba(169,228,255,.14)}
nav .wrap{display:flex;align-items:center;gap:20px;height:62px}
nav .brand{color:#fff;font-weight:700;display:flex;align-items:center;gap:10px;margin-inline-end:auto;white-space:nowrap}
nav a.l{color:#BFDFFF;font-size:14px;white-space:nowrap;transition:color .2s} nav a.l:hover{color:#fff}
.tog{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.08);border:1px solid rgba(169,228,255,.3);color:#fff;border-radius:10px;padding:7px 11px;font:600 13px inherit;cursor:pointer;font-family:inherit;transition:background .2s}
.tog:hover{background:rgba(255,255,255,.18)}
.tog svg{width:16px;height:16px}
.sun{display:none}:root[data-theme="dark"] .sun{display:block}:root[data-theme="dark"] .moon{display:none}
/* hero */
.hero{background:radial-gradient(900px 520px at 80% 20%,rgba(76,169,255,.30),transparent 70%),linear-gradient(120deg,#030B26 0%,#06235A 42%,#0B4A9E 78%,#1477D6 100%);color:#fff;padding:86px 0 70px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:56px 56px;animation:drift 40s linear infinite}
@keyframes drift{to{background-position:56px 56px}}
.orbit{position:absolute;width:760px;height:760px;inset-inline-end:-220px;top:-260px;border:1px dashed rgba(169,228,255,.18);border-radius:50%;animation:spin 60s linear infinite;pointer-events:none}
.orbit:after{content:"";position:absolute;width:12px;height:12px;border-radius:50%;background:#7FD3FF;box-shadow:0 0 18px 6px rgba(127,211,255,.6);top:50%;left:-6px}
@keyframes spin{to{transform:rotate(360deg)}}
.hero .wrap{position:relative;display:grid;grid-template-columns:1.1fr .9fr;gap:44px;align-items:center}
.eyebrow{font-family:'IBM Plex Mono',monospace;font-size:12.5px;letter-spacing:2.5px;color:#8FD3FF;text-transform:uppercase}
html[lang="ar"] .eyebrow{font-family:inherit;letter-spacing:0;font-size:14px}
.hero h1{font-size:clamp(38px,4.8vw,62px);line-height:1.08;background:linear-gradient(90deg,#fff,#CBEBFF 60%,#7FD3FF);-webkit-background-clip:text;background-clip:text;color:transparent;margin:14px 0}
.hero p.sub{font-size:19px;color:#D8EEFF;max-width:620px}
.hero .tags{margin:20px 0 28px;display:flex;flex-wrap:wrap;gap:8px}
.hero .tags>span{padding:5px 13px;border-radius:999px;font-size:13.5px;background:rgba(108,199,255,.13);border:1px solid rgba(108,199,255,.38);color:#D8EEFF}
.hero .ctas{display:flex;flex-wrap:wrap;gap:12px}
.heroimg{border-radius:20px;overflow:hidden;border:1px solid rgba(169,228,255,.35);box-shadow:0 30px 70px rgba(0,0,0,.35);animation:float 7s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-8px)}}
.heroimg img{display:block;width:100%}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:46px}
.kpi{padding:18px 20px;border-radius:18px;background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.05));border:1px solid rgba(169,228,255,.32)}
.kpi b{display:block;font-size:34px;line-height:1.1;background:linear-gradient(90deg,#fff,#A9E4FF);-webkit-background-clip:text;background-clip:text;color:transparent;direction:ltr;unicode-bidi:isolate}
html[lang="ar"] .kpi b{text-align:right}
.kpi>span{font-size:14px;color:#BFDFFF}
/* monitor */
.mon{display:grid;grid-template-columns:1.1fr .9fr;gap:20px;margin-top:28px}
.maptools{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.seg{display:inline-flex;background:var(--seg);border-radius:10px;padding:3px}
.seg button{border:0;background:transparent;padding:7px 14px;border-radius:8px;font:600 13px inherit;font-family:inherit;color:var(--accent);cursor:pointer}
.seg button.on{background:var(--segon);box-shadow:0 2px 8px rgba(10,61,145,.15)}
#map{width:100%;height:auto;display:block;background:var(--mapbg);border-radius:14px;direction:ltr}
#map path{cursor:pointer;transition:opacity .15s} #map path:hover{opacity:.7}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--muted);margin-top:10px}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-inline-end:6px;vertical-align:-1px}
.read{margin-top:16px;background:var(--soft);border-radius:12px;padding:14px 16px;font-size:14px}
.det h3{font-size:26px;color:var(--head)}
.badge{display:inline-block;padding:4px 12px;border-radius:999px;font-size:13px;font-weight:700;color:#fff}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}
.stat{background:var(--soft);border-radius:12px;padding:10px 12px}.stat b{display:block;font-size:20px;color:var(--head)}.stat span{font-size:12.5px;color:var(--muted)}
.chart{width:100%;height:auto;display:block;direction:ltr}
.chart .g{stroke:var(--grid)} .chart .t{fill:var(--muted)} .chart .h{fill:var(--head)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{background:var(--th);color:#fff;text-align:start;padding:10px;font-weight:600;cursor:pointer;white-space:nowrap;position:sticky;top:0}
td{padding:8px 10px;border-bottom:1px solid var(--line)} tbody tr{cursor:pointer} tbody tr:hover td{background:var(--soft)} tr.sel td{background:var(--ice)}
.tablewrap{max-height:360px;overflow:auto;border-radius:14px;border:1px solid var(--line);margin-top:20px;background:var(--surface)}
/* steps */
.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:30px;position:relative}
.step .n{font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--cyan);font-weight:600}
.step h4{font-size:18px;margin:6px 0}.step p{font-size:14px;color:var(--muted)}
.flow{position:absolute;top:-14px;inset-inline:0;height:3px;border-radius:3px;background:linear-gradient(90deg,#0A3D91,#0EA5E9);transform-origin:left;transform:scaleX(0);transition:transform 1.6s ease}
html[dir="rtl"] .flow{transform-origin:right}
.in .flow,.flow.in{transform:scaleX(1)}
.bar{height:16px;border-radius:6px;width:0;transition:width 1.2s cubic-bezier(.2,.8,.2,1)}
.cmp{display:grid;grid-template-columns:170px 1fr;gap:10px 18px;align-items:center;margin-top:12px}
.events{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:28px}
.ev img{width:100%;height:260px;object-fit:contain;border-radius:12px;display:block;background:#F4F8FF}
.ev h4{font-size:18px;margin:12px 0 4px}
figure img{width:100%;border-radius:10px;display:block}
.price b{font-size:34px;color:var(--head)}.price.dark b{color:#fff}
/* faq */
.faq{display:grid;gap:12px;margin-top:28px;max-width:900px}
.faq details{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:0 22px;box-shadow:var(--shadow);transition:background .3s}
.faq summary{cursor:pointer;list-style:none;padding:18px 0;font-weight:600;font-size:17px;color:var(--head);display:flex;justify-content:space-between;align-items:center;gap:16px}
.faq summary::-webkit-details-marker{display:none}
.faq summary:after{content:"+";font-size:24px;color:var(--accent);transition:transform .25s;flex:none}
.faq details[open] summary:after{transform:rotate(45deg)}
.faq details p{padding:0 0 18px;color:var(--muted);font-size:15.5px}
/* regional context */
.ctry .big{direction:ltr;unicode-bidi:isolate}html[lang="ar"] .ctry .big{text-align:right}
.ctry b{display:block;font-size:16px;color:var(--head);margin-bottom:4px}.dark.ctry b{color:#fff}
.ctry .flag{display:block;width:40px;height:24px;border-radius:4px;margin-bottom:10px;box-shadow:0 0 0 1px rgba(0,0,0,.12)}
/* risk register */
.riskcount{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.riskcount span{padding:6px 14px;border-radius:999px;font-weight:700;font-size:14px;color:#fff}
.risks{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px}
.risk{border-inline-start:6px solid var(--line);cursor:pointer}
.risk.urgent{border-inline-start-color:#FF4D6D}.risk.monitor{border-inline-start-color:#FFB020}.risk.closed{border-inline-start-color:#2E9E6B;opacity:.85}
.risk h4{font-size:18px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.risk dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:13.5px;margin-top:10px}
.risk dt{color:var(--muted);white-space:nowrap}.risk dd{margin:0;color:var(--ink)}
.risk .meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
@media(max-width:900px){.risks{grid-template-columns:1fr}}
footer{background:#030B26;color:#BFDFFF;padding:46px 0;font-size:14px}
footer a{color:#fff}
/* scroll reveal */
.reveal{opacity:0;transform:translateY(26px);transition:opacity .8s ease,transform .8s ease}
.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}.reveal{opacity:1;transform:none}.bar{width:var(--w)!important}.flow{transform:none}}
@media(max-width:980px){nav a.l{display:none}}
@media(max-width:900px){.hero .wrap,.mon,.grid2,.grid3,.events{grid-template-columns:1fr}.kpis,.grid4{grid-template-columns:1fr 1fr}.steps{grid-template-columns:1fr}.cmp{grid-template-columns:1fr}.orbit{display:none}section{padding:64px 0}}
@media(max-width:520px){.kpis,.grid4{grid-template-columns:1fr}.wrap{padding:0 16px}nav .brand span{display:none}}
</style></head>
<body>
<nav><div class="wrap">
  <a class="brand" href="#top"><svg width="26" height="26" viewBox="0 0 240 240"><circle cx="120" cy="120" r="104" fill="none" stroke="#7FD3FF" stroke-width="14"/><path d="M120 52 C 160 80 168 128 120 170 C 72 128 80 80 120 52 Z" fill="none" stroke="#fff" stroke-width="14"/></svg><span data-i18n="title"></span></a>
  <a class="l" href="#monitor" data-i18n="nav_mon"></a><a class="l" href="#risks" data-i18n="nav_risk"></a><a class="l" href="#how" data-i18n="nav_how"></a><a class="l" href="#events" data-i18n="nav_ev"></a><a class="l" href="#validation" data-i18n="nav_val"></a><a class="l" href="#carbon" data-i18n="nav_carbon"></a><a class="l" href="#region" data-i18n="nav_reg"></a><a class="l" href="#faq" data-i18n="nav_faq"></a>
  <button class="tog" id="langBtn" aria-label="Switch language"><span id="langLbl">العربية</span></button>
  <button class="tog" id="themeBtn" aria-label="Switch light / dark theme"><svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
  <a class="tog" href="https://github.com/Nahla-Nabil/blue-carbon-guardian" aria-label="GitHub">GitHub ↗</a>
</div></nav>

<header class="hero" id="top"><div class="orbit"></div><div class="wrap">
  <div class="reveal">
    <div class="eyebrow" data-i18n="eyebrow"></div>
    <h1 data-i18n="title"></h1>
    <p class="sub" data-i18n="sub"></p>
    <div class="tags"><span style="background:rgba(255,255,255,.16);color:#fff;font-weight:600" data-i18n="tag_team"></span><span data-i18n="tag_theme"></span><span data-i18n="tag_by"></span></div>
    <div class="ctas"><a class="btn p" href="#monitor"><span data-i18n="cta_mon"></span> →</a><a class="btn s" href="https://github.com/Nahla-Nabil/blue-carbon-guardian#-demo-video-214--english-narration-arabic-subtitles">▶ <span data-i18n="cta_video"></span></a><a class="btn s" href="slides.pdf" data-i18n="cta_slides"></a></div>
  </div>
  <div class="heroimg reveal"><img src="assets/alert_story.gif" alt="Real data, stand 5: Sentinel-2 images, 200 m cells turning red, and the alert score crossing its threshold"></div>
  <div class="kpis" style="grid-column:1/-1">
    <div class="kpi reveal"><b><span class="count" data-to="5">5</span></b><span data-i18n="k1"></span></div>
    <div class="kpi reveal"><b><span class="count" data-to="40">40</span> %</b><span data-i18n="k2"></span></div>
    <div class="kpi reveal"><b><span class="count" data-to="73">73</span> %</b><span data-i18n="k3"></span></div>
    <div class="kpi reveal"><b>≈ <span class="count" data-to="247">247</span> kt C</b><span data-i18n="k4"></span></div>
  </div>
</div></header>

<section id="monitor"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="mon_k"></div><h2 data-i18n="mon_h"></h2><p class="lede" data-i18n="mon_lede"></p></div>
  <div class="mon reveal">
    <div class="card">
      <div class="maptools"><div class="seg"><button id="bStands" class="on" data-i18n="b_stands"></button><button id="bCells" data-i18n="b_cells"></button></div>
        <span class="note" data-i18n="map_note"></span></div>
      <svg id="map"></svg>
      <div class="legend"><span><i class="sw" style="background:#7FB6F5"></i><span data-i18n="lg_stable"></span></span><span><i class="sw" style="background:#2E9E6B"></i><span data-i18n="lg_impr"></span></span><span><i class="sw" style="background:#FFB020"></i><span data-i18n="lg_dec"></span></span><span><i class="sw" style="background:#FF4D6D"></i><span data-i18n="lg_sev"></span></span><span><i class="sw" style="background:transparent;border:2px solid #7C4DFF"></i><span data-i18n="lg_alert"></span></span></div>
      <div class="read"><b style="color:var(--head)" data-i18n="read_h"></b><p style="margin-top:6px" data-i18n="read_p"></p></div>
    </div>
    <div class="card det" id="det"></div>
  </div>
  <div class="tablewrap reveal"><table id="tbl"><thead><tr><th data-k="stand"></th><th data-k="area_ha"></th><th data-k="condition"></th><th data-k="ndvi_change_pct"></th><th data-k="cells_bad"></th><th data-k="alerts_2022_2026"></th><th data-k="stock_tC_p50"></th></tr></thead><tbody></tbody></table></div>
  <p class="note" style="margin-top:10px" data-i18n="mon_note"></p>
  <p class="note" style="margin-top:6px"><span data-i18n="feed"></span> <a href="api/v1/alerts.json" dir="ltr">api/v1/alerts.json</a> · <a href="api/v1/stands.json" dir="ltr">api/v1/stands.json</a> · <a href="api/v1/risks.json" dir="ltr">api/v1/risks.json</a></p>
</div></section>

<section id="risks" style="border-top:1px solid var(--line)"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="risk_k"></div><h2 data-i18n="risk_h"></h2><p class="lede" data-i18n="risk_lede"></p></div>
  <div class="riskcount reveal" id="riskcount"></div>
  <div class="risks" id="risklist"></div>
  <p class="note" style="margin-top:12px" data-i18n="risk_rule"></p>
</div></section>

<section class="alt" id="how"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="how_k"></div><h2 data-i18n="how_h"></h2><p class="lede" data-i18n="how_lede"></p></div>
  <div class="steps reveal"><div class="flow"></div>
    <div class="card step lift"><div class="n">01</div><h4 data-i18n="s1h"></h4><p data-i18n="s1p"></p></div>
    <div class="card step lift"><div class="n">02</div><h4 data-i18n="s2h"></h4><p data-i18n="s2p"></p></div>
    <div class="card step lift"><div class="n">03</div><h4 data-i18n="s3h"></h4><p data-i18n="s3p"></p></div>
    <div class="card step lift"><div class="n">04</div><h4 data-i18n="s4h"></h4><p data-i18n="s4p"></p></div>
    <div class="card step dark lift"><div class="n" style="color:#8FD3FF">05</div><h4 data-i18n="s5h"></h4><p data-i18n="s5p"></p></div>
  </div>
  <div class="grid2" style="margin-top:22px">
    <div class="card reveal"><h4 data-i18n="noise_h"></h4><p class="note" data-i18n="noise_n"></p><div id="noise"></div><p style="margin-top:14px;padding:12px 14px;background:var(--soft);border-radius:10px;font-size:14px" data-i18n="textbook"></p></div>
    <div class="card reveal"><h4 data-i18n="cells_h"></h4><p style="margin-top:8px" data-i18n="cells_p"></p>
      <div class="cmp"><span class="note" data-i18n="c_both"></span><div style="display:flex;align-items:center;gap:8px"><div class="bar" data-w="73" style="background:linear-gradient(90deg,#0A3D91,#0EA5E9)"></div><b>73 %</b></div>
      <span class="note" data-i18n="c_stand"></span><div style="display:flex;align-items:center;gap:8px"><div class="bar" data-w="25" style="background:#7FB6F5"></div><b>25 %</b></div>
      <span class="note" data-i18n="c_chance"></span><div style="display:flex;align-items:center;gap:8px"><div class="bar" data-w="13" style="background:#C9D3E3"></div><b>13 %</b></div></div>
      <p class="note" style="margin-top:8px" data-i18n="cells_n"></p></div>
  </div>
</div></section>

<section id="events"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="ev_k"></div><h2 data-i18n="ev_h"></h2><p class="lede" data-i18n="ev_lede"></p></div>
  <div class="card reveal" style="margin-top:24px"><h4 data-i18n="strip_h"></h4>
    <div class="grid4" style="margin-top:12px">
      <figure><img src="assets/site/s2_2021.jpg" alt="Nov 2021"><figcaption class="note" data-i18n="f1"></figcaption></figure>
      <figure><img src="assets/site/s2_2022.jpg" style="outline:3px solid #FF4D6D" alt="Oct 2022"><figcaption class="note" data-i18n="f2"></figcaption></figure>
      <figure><img src="assets/site/s2_2023.jpg" alt="Jun 2023"><figcaption class="note" data-i18n="f3"></figcaption></figure>
      <figure><img src="assets/site/s2_2026.jpg" alt="May 2026"><figcaption class="note" data-i18n="f4"></figcaption></figure></div></div>
  <div class="events">
    <div class="card ev lift reveal"><img src="assets/site/stand5.jpg" alt="Stand 5 before and after"><h4 data-i18n="e5h"></h4><p class="note" data-i18n="e5p"></p></div>
    <div class="card ev lift reveal"><img src="assets/site/stand9.jpg" alt="Stand 9 before and after"><h4 data-i18n="e9h"></h4><p class="note" data-i18n="e9p"></p></div>
    <div class="card ev lift reveal"><img src="assets/site/stand12.jpg" alt="Stand 12 key years"><h4 data-i18n="e12h"></h4><p class="note" data-i18n="e12p"></p></div>
    <div class="card ev lift reveal"><img src="assets/site/stand18.jpg" alt="Stand 18 key years"><h4 data-i18n="e18h"></h4><p class="note" data-i18n="e18p"></p></div>
  </div>
  <div class="card reveal" style="margin-top:20px"><h4 data-i18n="gantt_h"></h4><p class="note" data-i18n="gantt_n"></p><div id="gantt"></div></div>
</div></section>

<section class="alt" id="validation"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="val_k"></div><h2 data-i18n="val_h"></h2><p class="lede" data-i18n="val_lede"></p></div>
  <div class="grid2" style="margin-top:24px">
    <div class="card reveal"><div id="sim"></div><p class="note" style="margin-top:8px" data-i18n="sim_n"></p></div>
    <div style="display:grid;gap:16px">
      <div class="card reveal"><div class="k" style="color:var(--muted)" data-i18n="cal_k"></div><div class="big" style="margin-top:6px"><span class="count" data-to="0.96" data-dec="2">0.96</span></div><p class="note" data-i18n="cal_n"></p></div>
      <div class="card dark reveal"><div class="k" style="color:#8FD3FF" data-i18n="uns_k"></div><div style="font-size:42px;font-weight:700;margin-top:6px"><span class="count" data-to="0.79" data-dec="2">0.79</span></div><p style="font-size:14px" data-i18n="uns_n"></p></div>
    </div>
  </div>
  <div class="card reveal" style="margin-top:20px"><div class="grid2" style="align-items:center">
    <img src="assets/site/enmap.jpg" style="width:100%;border-radius:10px;background:#fff" alt="EnMAP spectra of stand 5">
    <div><div class="k" data-i18n="en_k"></div><h4 style="font-size:22px;margin:6px 0" data-i18n="en_h"></h4>
      <p data-i18n="en_p"></p>
      <p style="margin-top:8px;padding:10px 12px;background:var(--soft);border-radius:10px;font-size:14px" data-i18n="sim813"></p>
      <p class="note" style="margin-top:6px">Contains modified EnMAP data © DLR 2022, 2025.</p></div></div></div>
</div></section>

<section id="carbon"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="car_k"></div><h2 data-i18n="car_h"></h2></div>
  <div class="grid4" style="margin-top:24px">
    <div class="card lift reveal"><div class="big"><span class="count" data-to="108">108</span></div><p class="note" data-i18n="c1"></p></div>
    <div class="card lift reveal"><div class="big"><span class="count" data-to="247">247</span> kt</div><p class="note" data-i18n="c2"></p></div>
    <div class="card lift reveal"><div class="big"><span class="count" data-to="82">82</span> %</div><p class="note" data-i18n="c3"></p></div>
    <div class="card dark lift reveal"><div style="font-size:40px;font-weight:700;direction:ltr;unicode-bidi:isolate">2.8–6.7 kt</div><p style="font-size:14px" data-i18n="c4"></p></div>
  </div>
  <p class="note reveal" style="margin-top:12px" data-i18n="car_n"></p>
</div></section>

<section id="region" style="border-top:1px solid var(--line)"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="reg_k"></div><h2 data-i18n="reg_h"></h2><p class="lede" data-i18n="reg_lede"></p></div>
  <div class="grid4" style="margin-top:24px">
    <div class="card lift reveal ctry"><i class="flag" style="background:linear-gradient(90deg,#EF3340 0 22%,transparent 22%),linear-gradient(#00843D 0 33%,#fff 33% 66%,#000 66%)"></i><b data-i18n="ae_n"></b><div class="big">100 M</div><p class="note" data-i18n="ae_p"></p></div>
    <div class="card lift reveal ctry"><i class="flag" style="background:#006C35"></i><b data-i18n="sa_n"></b><div class="big">100 M+</div><p class="note" data-i18n="sa_p"></p></div>
    <div class="card lift reveal ctry"><i class="flag" style="background:linear-gradient(90deg,#fff 0 28%,#CE1126 28%)"></i><b data-i18n="bh_n"></b><div class="big">×4</div><p class="note" data-i18n="bh_p"></p></div>
    <div class="card dark lift reveal ctry"><i class="flag" style="background:linear-gradient(90deg,#7FD3FF,#1E6FD9)"></i><b data-i18n="ar_n"></b><div style="font-size:40px;font-weight:700;direction:ltr;unicode-bidi:isolate">≈ 365</div><p style="font-size:14px" data-i18n="ar_p"></p></div>
  </div>
  <div class="grid2" style="margin-top:16px">
    <div class="card reveal" style="display:flex;gap:18px;align-items:center"><div class="big" style="white-space:nowrap">5 / 25</div><p data-i18n="pr1"></p></div>
    <div class="card reveal" style="display:flex;gap:18px;align-items:center"><div class="big" style="white-space:nowrap;direction:ltr">$25–29</div><p data-i18n="pr2"></p></div>
  </div>
  <p class="note" style="margin-top:12px"><b data-i18n="reg_src"></b>: <span dir="ltr">MOCCAE COP26 pledge (2021) · <a href="https://www.ead.gov.ae">Environment Agency – Abu Dhabi</a> · EAD–IUCN GCC mangrove monitoring guide (Gulf News, 24 Feb 2026) · <a href="https://www.sgi.gov.sa">Saudi Green Initiative</a> · <a href="https://www.redseaglobal.com">Red Sea Global</a> (2023) · <a href="https://www.gdnonline.com/Details/1286654/Mangrove-plantation-coverage-%E2%80%98to-expand-four-fold-by-2035%E2%80%99-">GDN Online: Bahrain four-fold by 2035</a> · <a href="https://doi.org/10.3389/fmars.2025.1695426">Frontiers in Marine Science 2025</a> · S&amp;P Global Platts blue-carbon assessments 2024–25 · <a href="https://github.com/Nahla-Nabil/blue-carbon-guardian/blob/main/docs/business_plan_draft.md">full source list</a></span></p>
</div></section>

<section class="alt" id="offer"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="off_k"></div><h2 data-i18n="off_h"></h2></div>
  <div class="grid3" style="margin-top:24px">
    <div class="card lift reveal"><div class="pill" data-i18n="u1"></div><p style="margin-top:10px" data-i18n="u1d"></p><p class="note" data-i18n="u1t"></p></div>
    <div class="card lift reveal"><div class="pill" data-i18n="u2"></div><p style="margin-top:10px" data-i18n="u2d"></p><p class="note" data-i18n="u2t"></p></div>
    <div class="card lift reveal"><div class="pill" data-i18n="u3"></div><p style="margin-top:10px" data-i18n="u3d"></p><p class="note" data-i18n="u3t"></p></div>
  </div>
  <div class="grid4" style="margin-top:18px">
    <div class="card dark price reveal"><div class="k" style="color:#8FD3FF" data-i18n="p1k"></div><b>$12k</b><p style="font-size:14px" data-i18n="p1"></p></div>
    <div class="card price reveal"><div class="k" data-i18n="p2k"></div><b>$25k</b><p class="note" data-i18n="p2"></p></div>
    <div class="card price reveal"><div class="k" data-i18n="p3k"></div><b>$8k</b><p class="note" data-i18n="p3"></p></div>
    <div class="card price reveal"><div class="k" data-i18n="p4k"></div><b>≈ $3.3k</b><p class="note" data-i18n="p4"></p></div>
  </div>
  <p class="note" style="margin-top:10px"><span data-i18n="off_n"></span> <a href="https://github.com/Nahla-Nabil/blue-carbon-guardian/blob/main/docs/business_plan_draft.md" data-i18n="bp"></a> →</p>
</div></section>

<section><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="lim_k"></div><h2 data-i18n="lim_h"></h2></div>
  <div class="grid3" style="margin-top:20px">
    <div class="card reveal"><b data-i18n="l1h"></b><p class="note" data-i18n="l1p"></p></div>
    <div class="card reveal"><b data-i18n="l2h"></b><p class="note" data-i18n="l2p"></p></div>
    <div class="card reveal"><b data-i18n="l3h"></b><p class="note" data-i18n="l3p"></p></div>
  </div>
</div></section>

<section id="expert" style="border-top:1px solid var(--line)"><div class="wrap">
  <div class="card reveal" style="display:grid;grid-template-columns:auto 1fr;gap:26px;align-items:start">
    <div style="font:700 84px/0.8 Georgia,serif;color:#CE1126">&ldquo;</div>
    <div><div class="k" data-i18n="bsa_k"></div><h2 style="font-size:28px" data-i18n="bsa_h"></h2>
      <p style="font-size:17px;font-style:italic;margin-top:6px" data-i18n="bsa_q"></p>
      <p class="note" style="margin-top:10px" data-i18n="bsa_n"></p></div>
  </div>
</div></section>

<section class="alt" id="faq"><div class="wrap">
  <div class="reveal"><div class="k" data-i18n="faq_k"></div><h2 data-i18n="faq_h"></h2></div>
  <div class="faq">__FAQ__</div>
</div></section>

<footer><div class="wrap" style="display:flex;flex-wrap:wrap;gap:28px;justify-content:space-between">
  <div><b style="color:#fff;font-size:16px" data-i18n="title"></b><br>Team Blue Athar · <span style="font-family:'IBM Plex Sans Arabic'">الأثر الأزرق</span> · Nahla Nabil<br>Arab Youth Space Hackathon 2026 · Challenge 813</div>
  <div><a href="https://github.com/Nahla-Nabil/blue-carbon-guardian" data-i18n="ft_code"></a><br><a href="slides.pdf" data-i18n="cta_slides"></a> · <a href="summary_ar.pdf" data-i18n="ft_sum"></a><br><a href="api/v1/alerts.json" data-i18n="ft_feed"></a> · <a href="https://github.com/Nahla-Nabil/blue-carbon-guardian/blob/main/docs/api_alert_concept.md" data-i18n="ft_api"></a></div>
  <div style="max-width:430px;font-size:12.5px">Contains modified Copernicus Sentinel data 2020–2026 · Contains modified EnMAP data © DLR 2022, 2025 · ESA WorldCover 2021 (CC BY 4.0) · Schile et al. 2016 (CC0) · sub-metre captures viewed via Esri World Imagery Wayback (Esri, Maxar, Earthstar Geographics, and the GIS User Community). Code: MIT.</div>
</div></footer>

<script>
const D = __DATA__, REPORTS = __REPORTS__, TXT = __TXT__, DYN = __DYN__, RISKS = __RISKS__;
let LANG = document.documentElement.lang === "ar" ? "ar" : "en";
const fillLast = () => { const el = document.getElementById("lastobs"); if (el) el.textContent = new Date(D.kpi.last_obs).toLocaleDateString(DYN[LANG].locale, {month: "long", year: "numeric"}); };
const L = k => DYN[LANG][k];
const COL = {"stable":"#7FB6F5","improving":"#2E9E6B","decline":"#FFB020","severe decline":"#FF4D6D"};
const NS = "http://www.w3.org/2000/svg";
const ST = {}; D.status.forEach(s => ST[s.stand] = s);
const CELLS = {}; D.cells.forEach(c => (CELLS[c.s] = CELLS[c.s] || []).push(c));
D.status.forEach(s => s.cells_bad = (CELLS[s.stand] || []).filter(c => c.cond !== "stable" && c.cond !== "improving").length);
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
// ---------- language + theme ----------
function applyLang() {
  document.documentElement.lang = LANG; document.documentElement.dir = LANG === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach(el => { const t = TXT[el.dataset.i18n]; if (t) el.innerHTML = t[LANG === "ar" ? 1 : 0]; });
  document.getElementById("langLbl").textContent = LANG === "ar" ? "English" : "العربية";
  document.title = LANG === "ar" ? "حارس الكربون الأزرق" : "Blue Carbon Guardian";
  document.querySelectorAll("#tbl th").forEach((th, i) => th.textContent = L("th")[i]);
  fillLast(); drawStatic(); drawTable(); drawRisks(); select(sel);
}
// ---------- risk register (ranked cases that stay open until a person closes them) ----------
const PCOL = {urgent: "#FF4D6D", monitor: "#FFB020", closed: "#2E9E6B"};
function drawRisks() {
  const lang = LANG === "ar" ? "ar" : "en", fmt = d => new Date(d).toLocaleDateString(L("locale"), {day: "numeric", month: "short", year: "numeric"});
  document.getElementById("riskcount").innerHTML = ["urgent", "monitor", "closed"].map(p => `<span style="background:${PCOL[p]}">${RISKS.counts[p]} · ${L(p)}</span>`).join("");
  document.getElementById("risklist").innerHTML = RISKS.risks.map(r => {
    const c = r.carbon_at_stake, kt = v => (v / 1000).toFixed(1);
    const carb = c ? `<span class="pill" dir="ltr">${r.stand === 5 ? "" : L("upto") + " "}${c.t_c_median_low === c.t_c_median_high ? kt(c.t_c_median_high) : kt(c.t_c_median_low) + "–" + kt(c.t_c_median_high)} kt C ${L("atstake")}</span>` : "";
    return `<div class="card lift risk ${r.priority}" data-k="${r.stand}">
      <h4><span>${r.id} · ${L("stand")} ${r.stand}</span><span class="badge" style="background:${PCOL[r.priority]};font-size:12px">${L(r.priority)}</span></h4>
      <dl><dt>${r.status === "closed" ? L("closedon") : L("opened")}</dt><dd dir="ltr" style="text-align:start">${fmt(r.status === "closed" ? r.closed : r.opened)}</dd>
        <dt>${L("cause")}</dt><dd>${r.likely_cause[lang]}</dd>
        <dt>${L("conf")}</dt><dd><b>${r.confidence[lang]}</b> · <span class="note">${r.confidence_basis[lang]}</span></dd>
        <dt>${L("action")}</dt><dd>${r.action[lang]}</dd></dl>
      <div class="meta">${r.ha_to_inspect ? `<span class="pill" dir="ltr">${r.ha_to_inspect} ha ${L("toinsp")}</span>` : ""}${carb}</div></div>`; }).join("");
  document.querySelectorAll(".risk").forEach(el => el.onclick = () => { select(+el.dataset.k); document.getElementById("monitor").scrollIntoView({behavior: "smooth"}); });
}
document.getElementById("langBtn").onclick = () => { LANG = LANG === "ar" ? "en" : "ar"; try { localStorage.setItem("bcg-lang", LANG) } catch (e) {} applyLang(); };
document.getElementById("themeBtn").onclick = () => { const t = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", t); try { localStorage.setItem("bcg-theme", t) } catch (e) {} drawMap(); select(sel); };
// ---------- map ----------
let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
const rings = g => g.type === "Polygon" ? g.coordinates : g.coordinates.flat();
D.features.forEach(f => rings(f.geometry).forEach(r => r.forEach(([x, y]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); })));
const W = 1000, K = Math.cos(24.5 * Math.PI / 180), H = W * (y1 - y0) / ((x1 - x0) * K), P = 12;
const px = ([x, y]) => [P + (x - x0) / (x1 - x0) * (W - 2 * P), P + (y1 - y) / (y1 - y0) * (H - 2 * P)];
const pathD = g => rings(g).map(r => "M" + r.map(p => px(p).map(v => v.toFixed(1)).join(",")).join("L") + "Z").join("");
const map = document.getElementById("map"); map.setAttribute("viewBox", `0 0 ${W} ${H}`);
let mode = "stands", sel = 5;
function drawMap() {
  map.innerHTML = ""; const edge = cssv("--surface"), head = cssv("--head"), dark = document.documentElement.getAttribute("data-theme") === "dark";
  if (mode === "stands") D.features.forEach(f => { const s = ST[f.properties.stand], p = document.createElementNS(NS, "path");
    p.setAttribute("d", pathD(f.geometry)); p.setAttribute("fill", COL[s.condition] || "#7FB6F5"); p.setAttribute("fill-opacity", ".85");
    p.setAttribute("stroke", s.alert_now ? "#7C4DFF" : (s.stand === sel ? head : edge)); p.setAttribute("stroke-width", s.alert_now || s.stand === sel ? 3 : 1);
    p.onclick = () => select(s.stand); const t = document.createElementNS(NS, "title"); t.textContent = `${L("stand")} ${s.stand} · ${L(s.condition)}`; p.appendChild(t); map.appendChild(p); });
  else { D.features.forEach(f => { const p = document.createElementNS(NS, "path"); p.setAttribute("d", pathD(f.geometry)); p.setAttribute("fill", dark ? "#16294F" : "#DCE8F8");
      p.setAttribute("stroke", f.properties.stand === sel ? head : (dark ? "#2A4275" : "#B9CDEA")); p.setAttribute("stroke-width", f.properties.stand === sel ? 2.5 : 1); p.onclick = () => select(f.properties.stand); map.appendChild(p); });
    D.cells.forEach(c => { const p = document.createElementNS(NS, "path"); p.setAttribute("d", pathD(c.g)); p.setAttribute("fill", COL[c.cond] || "#7FB6F5");
      p.setAttribute("stroke", edge); p.setAttribute("stroke-width", .6); p.onclick = () => select(c.s);
      const t = document.createElementNS(NS, "title"); t.textContent = `${L("stand")} ${c.s} · ${L(c.cond)} · ${c.ha} ha`; p.appendChild(t); map.appendChild(p); }); }
}
document.getElementById("bStands").onclick = e => { mode = "stands"; e.target.classList.add("on"); document.getElementById("bCells").classList.remove("on"); drawMap(); };
document.getElementById("bCells").onclick = e => { mode = "cells"; e.target.classList.add("on"); document.getElementById("bStands").classList.remove("on"); drawMap(); };
// ---------- charts ----------
function lineChart(months, lines, opts) {
  const w = 560, h = 210, l = 40, r = 8, t = 10, b = 24, n = months.length;
  const lo = opts.lo, hi = opts.hi, X = i => l + i / (n - 1) * (w - l - r), Y = v => t + (hi - Math.max(lo, Math.min(hi, v))) / (hi - lo) * (h - t - b);
  let s = `<svg class="chart" viewBox="0 0 ${w} ${h}" font-family="IBM Plex Sans">`;
  (opts.bands || []).forEach(([a, c]) => { const i = months.indexOf(a), j = months.indexOf(c); if (i >= 0) s += `<rect x="${X(i)}" y="${t}" width="${Math.max(3, X(j >= 0 ? j : n - 1) - X(i))}" height="${h - t - b}" fill="rgba(255,77,109,.16)"/>`; });
  opts.ticks.forEach(v => s += `<line class="g" x1="${l}" x2="${w - r}" y1="${Y(v)}" y2="${Y(v)}"/><text class="t" x="${l - 6}" y="${Y(v) + 4}" font-size="10" text-anchor="end">${v}${opts.unit || ""}</text>`);
  (opts.refs || []).forEach(([v, c, lab]) => s += `<line x1="${l}" x2="${w - r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${c}" stroke-dasharray="5 4"/><text x="${w - r - 2}" y="${Y(v) - 4}" font-size="10" fill="${c}" text-anchor="end">${lab}</text>`);
  months.forEach((m, i) => { if (m.endsWith("-01")) s += `<text class="t" x="${X(i)}" y="${h - 6}" font-size="10" text-anchor="middle">${m.slice(0, 4)}</text>`; });
  lines.forEach(([vals, c, wd]) => { let d = "", pen = false; vals.forEach((v, i) => { if (v === null || v === undefined) { pen = false; return; } d += (pen ? "L" : "M") + X(i).toFixed(1) + "," + Y(v).toFixed(1); pen = true; });
    s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${wd}" stroke-linejoin="round"/>`; });
  return s + "</svg>";
}
function select(k) {
  sel = k; const s = ST[k], se = D.series[k], cells = CELLS[k] || [], bad = cells.filter(c => c.cond === "severe decline" || c.cond === "decline");
  const badHa = bad.reduce((a, c) => a + c.ha, 0), eps = D.episodes.filter(e => e.stand === k);
  const i0 = se.months.indexOf("2022-01"), m2 = se.months.slice(i0);
  const bands = eps.map(e => [e.start.slice(0, 7), e.end.slice(0, 7)]);
  const pct = v => (v > 0 ? "+" : "") + Math.round(v) + " %";
  document.getElementById("det").innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h3>${L("stand")} ${k}</h3><span class="badge" style="background:${COL[s.condition]}">${L(s.condition)}</span></div>
    <p class="note">${s.alert_now ? `<b style='color:#7C4DFF'>${L("alertnow")}</b> ` : L("noalert") + " "}${s.alerts_2022_2026} ${L("eps")}</p>
    <div class="stats"><div class="stat"><b dir="ltr">${s.area_ha.toFixed(1)} ha</b><span>${L("area")}</span></div>
      <div class="stat"><b dir="ltr">${(s.stock_tC_p50 / 1000).toFixed(1)} kt C</b><span>${L("stock")} (${(s.stock_tC_p10 / 1000).toFixed(1)}–${(s.stock_tC_p90 / 1000).toFixed(1)})</span></div>
      <div class="stat"><b dir="ltr">${pct(s.ndvi_change_pct)}</b><span>${L("ndvi")}</span></div>
      <div class="stat"><b>${bad.length} ${L("of")} ${cells.length} ${L("cells")}</b><span>${L("indecl")}${bad.length ? " · " + badHa.toFixed(1) + " " + L("toinspect") : ""}</span></div></div>
    <div class="k" style="font-size:11px">${L("score")}</div>
    ${lineChart(m2, [[se.zc.slice(i0), "#FF6B85", 1.8], [se.z.slice(i0), cssv("--accent"), 2.4]], {lo: -12, hi: 4, ticks: [-12, -8, -4, 0, 4], unit: "σ", bands,
      refs: [[-1.5, cssv("--accent"), "stand −1.5σ"], [-3.5, "#FF4D6D", "cell −3.5σ"]]})}
    <p class="note"><span style="color:var(--accent)">━</span> ${L("avg")} &nbsp; <span style="color:#FF6B85">━</span> ${L("worst")} &nbsp; <span style="background:rgba(255,77,109,.2);padding:0 6px">${L("alert")}</span></p>
    <div class="k" style="font-size:11px;margin-top:10px">${L("tcndvi")}</div>
    ${lineChart(se.months, [[se.ndvi, "#2E9E6B", 2]], {lo: Math.min(...se.ndvi.filter(v => v !== null)) - .03, hi: Math.max(...se.ndvi.filter(v => v !== null)) + .03, ticks: [], })}
    ${REPORTS.includes(k) ? `<a class="btn" style="background:#06235A;color:#fff;margin-top:10px" href="reports/stand_${String(k).padStart(2, "0")}_report.html" target="_blank">${L("report")} →</a>` : `<p class="note" style="margin-top:8px">${L("reports")}${REPORTS.join(", ")}).</p>`}`;
  drawMap(); document.querySelectorAll("#tbl tbody tr").forEach(tr => tr.classList.toggle("sel", +tr.dataset.k === k));
}
// ---------- table ----------
let sortK = "condition", asc = true; const ORD = {"severe decline": 0, "decline": 1, "stable": 2, "improving": 3};
function drawTable() {
  const rows = [...D.status].sort((a, b) => { const va = sortK === "condition" ? ORD[a.condition] : a[sortK], vb = sortK === "condition" ? ORD[b.condition] : b[sortK]; return (va > vb ? 1 : va < vb ? -1 : 0) * (asc ? 1 : -1); });
  document.querySelector("#tbl tbody").innerHTML = rows.map(s => `<tr data-k="${s.stand}"><td><b>${s.stand}</b></td><td>${s.area_ha.toFixed(1)}</td><td><span class="badge" style="background:${COL[s.condition]};font-size:11px">${L(s.condition)}</span></td><td dir="ltr" style="text-align:start">${Math.round(s.ndvi_change_pct)} %</td><td>${s.cells_bad} / ${(CELLS[s.stand] || []).length}</td><td>${s.alerts_2022_2026}</td><td>${(s.stock_tC_p50 / 1000).toFixed(1)}</td></tr>`).join("");
  document.querySelectorAll("#tbl tbody tr").forEach(tr => tr.onclick = () => { select(+tr.dataset.k); document.getElementById("monitor").scrollIntoView({behavior: "smooth"}); });
}
document.querySelectorAll("#tbl th").forEach(th => th.onclick = () => { const k = th.dataset.k; asc = sortK === k ? !asc : true; sortK = k; drawTable(); select(sel); });
// ---------- static charts (bars animate in when visible) ----------
function drawStatic() {
  document.getElementById("noise").innerHTML = [["NDVI", .0436, .0298, "−32 %"], ["NDRE (red edge)", .0283, .0183, "−35 %"], ["NDMI (moisture)", .0433, .0306, "−29 %"]].map(([n, a, b, p]) =>
    `<div style="margin-top:12px"><b style="font-size:14px">${n}</b><div class="cmp" style="grid-template-columns:110px 1fr;margin-top:4px;gap:4px 10px"><span class="note">${L("raw")}</span><div class="bar" data-w="${a / .0436 * 90}" style="background:#C9D3E3"></div><span class="note">${L("tide")}</span><div style="display:flex;align-items:center;gap:8px"><div class="bar" data-w="${b / .0436 * 90}" style="background:linear-gradient(90deg,#0A3D91,#0EA5E9)"></div><b style="color:var(--accent);white-space:nowrap" dir="ltr">${p}</b></div></div></div>`).join("");
  document.getElementById("sim").innerHTML = [[73, 13], [63, 36], [83, 36]].map(([d, c], i) =>
    `<div style="margin:14px 0"><b>${L("sim")[i][0]}</b> <span class="note">· ${L("sim")[i][1]}</span><div style="display:flex;align-items:center;gap:8px;margin-top:6px"><div class="bar" data-w="${d * .8}" style="height:22px;background:linear-gradient(90deg,#0A3D91,#0EA5E9)"></div><b style="color:var(--accent)">${d} %</b></div><div style="display:flex;align-items:center;gap:8px;margin-top:4px"><div class="bar" data-w="${c * .8}" style="background:#C9D3E3"></div><span class="note">${c} % ${L("chance")}</span></div></div>`).join("");
  const rows = [[5, "2022-03-28", "2023-02-22", "2022-10-25"], [9, "2022-03-28", "2023-02-22", "2022-12-07"], [12, "2022-03-28", "2023-02-22", "2022-12-17"], [6, "2022-03-28", "2023-02-22", "2023-02-17"], [18, "2023-11-14", "2025-01-06", "2024-10-29"]];
  const t = s => new Date(s).getTime(), a0 = t("2022-01-01"), a1 = t("2025-04-01"), w = 1000, l = 120, X = s => l + (t(s) - a0) / (a1 - a0) * (w - l - 20);
  let s = `<svg class="chart" viewBox="0 0 ${w} 290" font-family="IBM Plex Sans">`;
  [2022, 2023, 2024, 2025].forEach(y => { const x = X(y + "-01-01"); s += `<line class="g" x1="${x}" x2="${x}" y1="0" y2="262"/><text class="t" x="${x}" y="284" font-size="14" text-anchor="middle">${y}</text>`; });
  rows.forEach(([n, a, b, al], i) => { const y = 14 + i * 50; s += `<text class="h" x="0" y="${y + 20}" font-size="15" font-weight="700">${L("stand")} ${n}</text><rect x="${X(a)}" y="${y + 4}" width="${X(b) - X(a)}" height="22" rx="6" fill="#BFDDFF" stroke="#1E6FD9"/><path d="M${X(al)} ${y} l11 15 l-11 15 l-11 -15z" fill="#FF4D6D" stroke="#fff" stroke-width="2"/>`; });
  document.getElementById("gantt").innerHTML = s + "</svg>";
  observe();
}
// ---------- scroll animations ----------
let io = null;
function grow(el) { el.querySelectorAll(".bar[data-w]").forEach(b => { b.style.setProperty("--w", b.dataset.w + "%"); b.style.width = b.dataset.w + "%"; });
  el.querySelectorAll(".count").forEach(c => { if (c.dataset.done) return; c.dataset.done = 1; const to = +c.dataset.to, dec = +(c.dataset.dec || 0), t0 = performance.now(), dur = 1400;
    const step = now => { const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3); c.textContent = (to * e).toFixed(dec); if (p < 1) requestAnimationFrame(step); }; requestAnimationFrame(step); }); }
function observe() {
  const targets = document.querySelectorAll(".reveal, .card, .kpis");
  if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) { targets.forEach(el => { el.classList.add("in"); grow(el); }); return; }
  if (!io) io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); grow(e.target); io.unobserve(e.target); } }), {threshold: .15});
  targets.forEach(el => { if (el.classList.contains("in")) grow(el); else io.observe(el); });
}
applyLang();
</script>
</body></html>"""

def faq_html():
    out = []
    for i in range(1, 10):
        out.append(f'<details class="reveal"><summary data-i18n="q{i}"></summary><p data-i18n="a{i}"></p></details>')
    return "".join(out)

html = PAGE.replace("__FAQ__", faq_html())
# fill every data-i18n element with its English text at build time (readable without JavaScript)
html = re.sub(r'(data-i18n="(\w+)"[^>]*>)(</)', lambda m: m.group(1) + T[m.group(2)][0] + m.group(3), html)
missing = set(re.findall(r'data-i18n="(\w+)"', html)) - set(T)
assert not missing, missing
html = (html.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__REPORTS__", json.dumps(REPORTS))
            .replace("__TXT__", json.dumps(T, ensure_ascii=False, separators=(",", ":"))).replace("__DYN__", json.dumps(DYN, ensure_ascii=False, separators=(",", ":")))
            .replace("__RISKS__", json.dumps(json.load(open(ROOT / "analysis/data/risk_register.json", encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))))
(ROOT / "docs/index.html").write_text(html, encoding="utf-8")
(ROOT / "docs/.nojekyll").write_text("", encoding="utf-8")
print("docs/index.html", round(len(html) / 1024), "KB; reports for stands", REPORTS)
