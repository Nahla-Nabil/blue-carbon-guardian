"""Arabic summary for the judges: docs/summary_ar.pdf (A4, right-to-left). Every number is one already approved in README section 8.
Run from the repository root: python scripts/make_summary_ar.py   (needs Playwright + Chrome/Chromium)"""
import base64, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
b64 = lambda p: "data:image/png;base64," + base64.b64encode((ROOT / p).read_bytes()).decode()
IMG = {k: b64(v) for k, v in {"banner": "docs/assets/banner.png", "s21": "deck_source/images/s2_stand5_2021-11.png",
                              "s22": "deck_source/images/s2_stand5_2022-10.png", "s23": "deck_source/images/s2_stand5_2023-06.png",
                              "s26": "deck_source/images/s2_stand5_2026-05.png", "dash": "docs/assets/dashboard.png"}.items()}

KPI = [("<bdi dir='ltr'>29–35%</bdi>", "انخفاض التشويش بفضل نموذج المدّ والجزر"), ("5", "حالات تحويل حقيقية مؤكَّدة بصور دقيقة"), ("3 من 5", "اكتُشفت فقط عبر خلايا 200 م"),
       ("<bdi dir='ltr'>73%</bdi> مقابل <bdi dir='ltr'>13%</bdi>", "كشف الخسارة الجزئية خلال 60 يوماً مقابل الصدفة"), ("0.79", "إنذار خاطئ لكل منطقة سنوياً على 65 منطقة جديدة"), ("≈ 247 ألف طن", "مخزون كربون في منطقة التجربة")]

HTML = f"""<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;600;700&display=swap">
<style>
@page {{ size: A4; margin: 14mm 14mm 16mm 14mm; }}
* {{ box-sizing: border-box; margin: 0; }}
body {{ font-family: 'IBM Plex Sans Arabic', 'IBM Plex Sans', sans-serif; color: #0B1B3F; font-size: 10.3pt; line-height: 1.65; }}
.en {{ font-family: 'IBM Plex Sans', sans-serif; direction: ltr; unicode-bidi: embed; }}
h1 {{ font-size: 22pt; color: #06235A; line-height: 1.3; }}
h2 {{ font-size: 13.5pt; color: #06235A; margin: 16px 0 8px; padding-right: 10px; border-right: 5px solid #1E6FD9; }}
p {{ margin: 4px 0; }}
.lede {{ font-size: 11.5pt; color: #4A5F86; }}
.banner {{ width: 100%; border-radius: 10px; display: block; }}
.kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }}
.kpi {{ background: linear-gradient(135deg, #06235A, #0B4A9E); color: #fff; border-radius: 10px; padding: 9px 12px; }}
.kpi b {{ display: block; font-size: 15pt; direction: rtl; }}
.kpi span {{ font-size: 9pt; color: #BFDFFF; }}
.box {{ background: #F2F7FF; border: 1px solid #D6E6FF; border-radius: 10px; padding: 10px 14px; }}
.dark {{ background: linear-gradient(135deg, #06235A, #0B4A9E); color: #fff; border-radius: 10px; padding: 10px 14px; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9.8pt; }}
th {{ background: #0A3D91; color: #fff; text-align: right; padding: 5px 8px; font-weight: 600; }}
td {{ padding: 4px 8px; border-bottom: 1px solid #D6E6FF; vertical-align: top; }}
tr:nth-child(even) td {{ background: #F7FAFF; }}
.steps {{ display: flex; gap: 6px; align-items: stretch; }}
.step {{ flex: 1; background: #fff; border: 1px solid #C3DDFF; border-radius: 10px; padding: 8px 9px; font-size: 9.2pt; }}
.step b {{ display: block; color: #1E6FD9; font-size: 10pt; }}
.arrow {{ align-self: center; color: #0EA5E9; font-size: 16pt; }}
.imgs {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }}
.imgs div {{ position: relative; }} .imgs img {{ width: 100%; height: 104px; object-fit: cover; border-radius: 8px; display: block; }}
.imgs span {{ position: absolute; top: 5px; right: 5px; background: #06235A; color: #fff; font-size: 8pt; padding: 1px 7px; border-radius: 6px; }}
.imgs .hot span {{ background: #FF4D6D; }}
.cap {{ font-size: 8.5pt; color: #4A5F86; }}
ul {{ padding-right: 18px; margin: 4px 0; }} li {{ margin: 2px 0; }}
.pb {{ break-before: page; }} h2 {{ break-after: avoid; }} .box, .steps, .two, .imgs, tr, li, .dark, .kpis {{ break-inside: avoid; }}
.foot {{ margin-top: 14px; font-size: 8.5pt; color: #4A5F86; border-top: 1px solid #D6E6FF; padding-top: 8px; }}
.tag {{ display: inline-block; background: #E8F2FF; color: #0A3D91; border: 1px solid #C3DDFF; border-radius: 999px; padding: 1px 10px; font-size: 9pt; margin-left: 4px; }}
</style>
<body>
<img class="banner" src="{IMG['banner']}">
<h1 style="margin-top:12px">حارس الكربون الأزرق <span class="en" style="font-size:14pt;color:#1E6FD9">Blue Carbon Guardian</span></h1>
<p class="lede">مراقبة غابات القرم (المانغروف) في الخليج من الفضاء، مع مراعاة المدّ والجزر: من الإنذار إلى الدليل.</p>
<p><span class="tag">فريق الأثر الأزرق · Blue Athar</span><span class="tag">نهلة نبيل</span><span class="tag">المحور: صحة النظم البيئية والتنوع الحيوي والكربون الأزرق</span><span class="tag">التحدي 813</span></p>

<div class="kpis">{"".join(f'<div class="kpi"><b>{a}</b><span>{b}</span></div>' for a, b in KPI)}</div>

<h2>الفكرة في جملة واحدة</h2>
<div class="dark"><p>نظام يراقب كل منطقة قرم، وكل خلية منها بحجم 200 × 200 متر، من صور الأقمار الصناعية المجانية كل 5 أيام تقريباً. يُطلق إنذاراً عندما يُفقد جزء منها، ويحدد <b>أين</b> يجب التفتيش، ويقدّر <b>الكربون المعرَّض للخسارة</b>.</p></div>

<h2>المشكلة</h2>
<ul>
<li>تعهّدت الإمارات بزراعة 100 مليون شجرة قرم، والسعودية بأكثر من 100 مليون، بحلول 2030. وأصدرت هيئة البيئة في أبوظبي مع IUCN أول دليل لمراقبة القرم في الخليج (فبراير 2026).</li>
<li>لكن المراقبة اليوم مسوحات ميدانية متباعدة ودراسات لمرة واحدة. ووصفت مراجعة علمية (2025) المراقبة في الخليج بأنها «غير متكافئة». لا يوجد إنذار مستمر لكل منطقة، ولا تحقق مستقل من مخزون الكربون.</li>
<li><b>الصعوبة التقنية:</b> ينمو القرم في منطقة المدّ والجزر. عندما يرتفع المدّ تغطي المياه ما تحت الأشجار، فتبدو الصورة الفضائية كأن الأشجار فُقدت. لذلك يُطلق أي نظام تقليدي إنذارات كاذبة مع كل مدّ.</li>
</ul>

<h2 class="pb">ماذا يحدث الآن؟ مثال حقيقي (المنطقة 5، أبوظبي)</h2>
<div class="imgs">
<div><img src="{IMG['s21']}"><span>نوفمبر 2021 · سليمة</span></div>
<div class="hot"><img src="{IMG['s22']}"><span>أكتوبر 2022 · بداية الأعمال والإنذار</span></div>
<div><img src="{IMG['s23']}"><span>يونيو 2023 · شقّ القنوات</span></div>
<div><img src="{IMG['s26']}"><span>مايو 2026 · مشروع عمراني</span></div>
</div>
<p class="cap">صور Sentinel-2 بالألوان الطبيعية (تحتوي على بيانات Copernicus Sentinel معدَّلة). بدأ إنذارنا في 25 أكتوبر 2022، أثناء الأعمال.</p>

<h2>طريقة العمل</h2>
<div class="steps">
<div class="step"><b>1. المناطق والخلايا</b>25 منطقة قرم في أبوظبي (2,281 هكتار)، مقسّمة إلى خلايا 200 م</div><div class="arrow">←</div>
<div class="step"><b>2. سلاسل Sentinel-2</b>778 صورة بين 2020 و2026، ومؤشرات الغطاء النباتي والرطوبة والمياه</div><div class="arrow">←</div>
<div class="step"><b>3. نموذج المدّ والجزر</b>نموذج إحصائي يحسب «المتوقَّع» حسب الموسم ومستوى المياه، ويُحدَّث شهرياً</div><div class="arrow">←</div>
<div class="step"><b>4. الإنذار والحالة</b>المنطقة كلها أقل من −1.5σ أو أي خلية أقل من −3.5σ</div><div class="arrow">←</div>
<div class="step"><b>5. القرار</b>خريطة الخلايا، والكربون المعرَّض للخسارة، ولوحة التحكم، وتقرير لكل منطقة</div>
</div>

<h2>أين الابتكار؟</h2>
<div class="two">
<div class="box"><p><b>1. مراعاة المدّ والجزر</b></p><p>وجدنا من بياناتنا أن المدّ هو السبب الرئيسي للتشويش (ارتباط ≈ −0.9 مع رطوبة السطح). نُزيل أثره قبل البحث عن أي خسارة، فينخفض التشويش بنسبة <b>29 إلى 35%</b> في كل المؤشرات.</p></div>
<div class="box"><p><b>2. خلايا بحجم 200 متر</b></p><p>متوسط المنطقة يُخفي الخسارة الجزئية. مثلاً، المنطقة 9 تبدو «مستقرة» في المتوسط، بينما 8 من خلاياها الـ 28 في تراجع حاد. <b>3 من 5</b> حالات حقيقية لم تظهر إلا على مستوى الخلايا.</p></div>
</div>

<h2>النتائج والتحقق</h2>
<table>
<tr><th>ما قسناه</th><th>النتيجة</th><th>طريقة التحقق</th></tr>
<tr><td>حالات تحويل حقيقية</td><td><b>5</b> (المناطق 5، 9، 12، 18، 6): مشاريع ساحلية</td><td>صور أقمار مؤرَّخة بدقة 0.3 إلى 0.5 م (WorldView-2/3، Legion-1). بدأ الإنذار في كل موقع بين آخر صورة سليمة وأول صورة تُظهر الأعمال</td></tr>
<tr><td>خسارة جزئية (عُشر المنطقة يفقد نصف غطائه)</td><td><b>73%</b> خلال 60 يوماً، مقابل <b>13%</b> بالصدفة</td><td>محاكاة على مناطق حقيقية بلا تغيّر معروف، مع اختبار صفري</td></tr>

<tr><td>الإنذارات الخاطئة على مناطق لم يرها النموذج</td><td><b>0.79</b> لكل منطقة سنوياً (0.96 في المعايرة)</td><td>65 منطقة، و305 سنوات-منطقة، منها خليج تاروت في السعودية</td></tr>
<tr><td>البيانات فائقة الطيف (EnMAP، 224 نطاقاً)</td><td>تطابق <b>r = 0.84 إلى 0.99</b> مع Sentinel-2</td><td>صور من التاريخ نفسه. الأرض المحوَّلة في المنطقة 5 تحمل طيفاً معدنياً (رمل وردم)</td></tr>
<tr><td>الخسارة في المنطقة 5</td><td><b>26 إلى 62 هكتاراً</b></td><td>طريقتان مستقلتان (Sentinel-2 و EnMAP)</td></tr>
<tr><td>مخزون الكربون في منطقة التجربة</td><td><b>≈ 247 ألف طن كربون</b> (المدى 180 إلى 316)</td><td>24 قطعة قياس ميدانية قرب المناطق (108 طن/هكتار، 82% منها في التربة)</td></tr>
</table>

<h2 class="pb">المنتج والمستخدمون</h2>
<img src="{IMG['dash']}" style="width:100%;border-radius:10px;border:1px solid #C3DDFF;display:block">
<p class="cap">لوحة التحكم: خريطة الحالة بخلايا 200 م، وتفاصيل المنطقة، والكربون المعرَّض للخسارة.</p>
<table style="margin-top:8px">
<tr><th>المستخدم</th><th>القرار الذي يتخذه</th><th>ماذا يحصل عليه</th></tr>
<tr><td>الجهات البيئية (هيئة البيئة أبوظبي، وزارة التغير المناخي، المركز الوطني للغطاء النباتي)</td><td>أي المناطق نفتّش هذا الشهر؟</td><td>إنذار شهري وخريطة خلايا، فيذهب التفتيش إلى الخلايا المؤشَّرة فقط</td></tr>
<tr><td>برامج التشجير ومطوّرو مشاريع الكربون</td><td>هل مخزون الكربون الذي نعلنه ما زال موجوداً؟</td><td>حالة كل منطقة والكربون بمدى عدم اليقين، وتقرير للتحقق</td></tr>
<tr><td>المطوّرون الساحليون والجهات الرقابية</td><td>هل بقيت الأعمال خارج خط القرم؟</td><td>إنذار عند دخول الأعمال إلى خلايا القرم، مع دليل مؤرَّخ</td></tr>
</table>

<h2>نموذج العمل</h2>
<div class="two">
<div class="box"><p><b>الباقات (فرضيات للتجربة)</b></p><ul><li>المراقبة: 12 ألف دولار لكل موقع سنوياً</li><li>الأدلة: 25 ألف دولار (مع فحص بصور دقيقة لكل إنذار)</li><li>مراقبة المشاريع العمرانية: 8 آلاف دولار لكل مشروع</li></ul></div>
<div class="box"><p><b>تكلفة الخدمة ≈ 3,300 دولار لكل موقع سنوياً</b></p><p>الحوسبة أقل من 5 دولارات (مقيسة)، والصور الدقيقة عند الإنذار فقط (500 إلى 750 دولاراً)، ووقت المحلل (فرضية). المنافس الأقرب Global Mangrove Watch، ونحن مكمِّلون له: نراعي المدّ، ونعمل على مستوى الخلية، ونقدّم الكربون والتقارير.</p></div>
</div>

<h2>الحدود (بصراحة)</h2>
<ul>
<li><b>كشف أثناء الأعمال، لا إنذار مبكر:</b> لا ندّعي رؤية الضرر قبل حدوثه.</li>
<li><b>دقة 10 أمتار:</b> المناطق الأصغر من نحو 0.6 هكتار والزراعات الحديثة لا تُرى، ومنها مناطق القرم الصغيرة في البحرين.</li>
<li><b>تأكيد بالصور لا بالزيارات الميدانية:</b> مطابقة الحالات مع التصاريح وسجلات المواقع هي أول مهمة في التجربة مع شريك.</li>
<li><b>البيانات فائقة الطيف</b> أكدت النتائج، لكنها لم تتفوّق على متعدد الأطياف كمصنِّف (0.74 مقابل 0.72).</li>
<li><b>سحبنا رقماً أعلنّاه سابقاً</b> (58% و90%) بعدما كشف اختبار صفري خطأً في طريقة حسابه.</li>
</ul>

<h2>الخطوات القادمة</h2>
<div class="steps">
<div class="step"><b>الآن (إثبات المفهوم)</b>مراقبة على مستوى المنطقة والخلية، ولوحة تحكم وتقارير، و5 حالات مؤكَّدة، وتحقق EnMAP، واختبار على 65 منطقة جديدة</div><div class="arrow">←</div>
<div class="step"><b>الاحتضان (أكتوبر 2026 إلى يناير 2027)</b>دمج القمر 813، والنشر على منصة gIQ، وعميل تجريبي، ومطابقة الإنذارات مع التصاريح</div><div class="arrow">←</div>
<div class="step"><b>التوسّع (2027 وما بعده)</b>السعودية (الخليج والبحر الأحمر) والبحرين، وصور عالية الدقة للمناطق الصغيرة، وعقد مراقبة وطني</div>
</div>

<div class="foot">
<p><b>الكود والبيانات:</b> <span class="en">github.com/Nahla-Nabil/blue-carbon-guardian</span>. الدفتر الرئيسي يعمل خلال نحو 25 ثانية بلا إنترنت.</p>
<p><b>المصادر:</b> صور Copernicus Sentinel-2 معدَّلة (2020 إلى 2026)، وصور EnMAP معدَّلة © DLR 2022 و2025، وESA WorldCover 2021 (CC BY 4.0)، وقياسات Schile et al. 2016 (CC0)، وأرشيف Esri World Imagery Wayback (للعرض فقط). هذا ملخص عربي مساعد؛ وثائق التسليم الرسمية بالإنجليزية.</p>
</div>
</body></html>"""

out_html = ROOT / "docs" / "_summary_ar.html"; out_html.write_text(HTML, encoding="utf-8")
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(); pg.goto(out_html.as_uri()); pg.wait_for_timeout(2500)
    pg.pdf(path=str(ROOT / "docs" / "summary_ar.pdf"), format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<span></span>",
           footer_template='<div style="width:100%;text-align:center;font-size:8px;color:#4A5F86">Blue Carbon Guardian · Team Blue Athar · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
    b.close()
out_html.unlink(); print("docs/summary_ar.pdf")
