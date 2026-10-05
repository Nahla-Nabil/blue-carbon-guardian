<p align="center"><img src="docs/assets/banner.png" alt="Blue Carbon Guardian: tide-aware satellite monitoring for Gulf mangroves" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/Challenge-813%20·%20Arab%20Youth%20Space%20Hackathon%202026-0A3D91?style=for-the-badge" alt="Challenge 813">
  <img src="https://img.shields.io/badge/Theme-Ecosystem%20Health%20%26%20Blue%20Carbon-1E6FD9?style=for-the-badge" alt="Theme">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Jupyter-runs%20in%20~25%20s-1565C0?logo=jupyter&logoColor=white" alt="Notebook">
  <img src="https://img.shields.io/badge/Sentinel--2-778%20dates-2F80ED" alt="Sentinel-2">
  <img src="https://img.shields.io/badge/EnMAP-224%20bands%20hyperspectral-4F6BED" alt="EnMAP">
  <img src="https://img.shields.io/badge/Confirmed-5%20real%20events%20at%200.3--0.5%20m-0EA5E9" alt="Events">
  <img src="https://img.shields.io/badge/License-MIT-0B2A5B" alt="MIT">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/SDG%2013-Climate%20Action-3F7E44" alt="SDG 13">
  <img src="https://img.shields.io/badge/SDG%2014-Life%20Below%20Water-0A97D9" alt="SDG 14">
  <img src="https://img.shields.io/badge/SDG%2015-Life%20on%20Land-56C02B" alt="SDG 15">
</p>

<p align="center"><b>Team Blue Athar · الأثر الأزرق</b> · Nahla Nabil · Country representation: Palestine<br>
<sub><i>"Every lost mangrove leaves a trace (athar). We find it from space."</i></sub></p>

<p align="center">
<a href="#judges">🏆 For the judges</a> ·
<a href="#1-business-use-case">💼 Use case</a> ·
<a href="#2-the-problem">🌱 Problem</a> ·
<a href="#3-data-used">🛰️ Data</a> ·
<a href="#4-technical-approach">⚙️ Approach</a> ·
<a href="#5-installation">📦 Install</a> ·
<a href="#6-how-to-run">▶️ Run</a> ·
<a href="#7-example-input-and-output">🖼️ Examples</a> ·
<a href="#8-results-and-limitations">📊 Results</a> ·
<a href="#9-author-tools-licence-and-attribution">👩‍💻 Author</a>
</p>

> **We watch Gulf mangroves from space, stand by stand and in 200 m cells.** The system flags losses with a calibrated false-alarm rate, shows where
> inside a stand to inspect, and reports the carbon at stake. It runs on free Sentinel-2 imagery with a tide model, and it is checked against EnMAP
> hyperspectral data and dated sub-metre imagery.

<h3 align="center">⚡ Watch a real mangrove loss trigger the alert</h3>
<p align="center"><img src="docs/assets/alert_story.gif" alt="Animated: stand 5 in Abu Dhabi, 2022 to 2026. Sentinel-2 images show the mangrove fringe being replaced by reclamation and canals while the 200 m cells turn red and the alert score drops below its threshold on 25 October 2022" width="92%"><br>
<sub>Real data, stand 5 (Abu Dhabi), 2022 → 2026: Sentinel-2 images, 200 m cells coloured by their alert state, and the tide-aware alert score.
The alert began between the last sub-metre capture showing intact mangrove (Mar 2022) and the first showing works (Feb 2023).
Contains modified Copernicus Sentinel data 2021–2026. Built by <code>scripts/alert_story_data.py</code> + <code>scripts/make_alert_story.py</code>.</sub></p>

<table align="center">
<tr><td align="center"><b>−29 to −35 %</b><br><sub>noise after the tide model</sub></td>
<td align="center"><b>5</b><br><sub>real conversions confirmed at sub-metre</sub></td>
<td align="center"><b>3 of 5</b><br><sub>seen only by 200 m cells</sub></td>
<td align="center"><b>73 % vs 13 %</b><br><sub>partial loss caught in 60 days vs chance</sub></td>
<td align="center"><b>0.79</b><br><sub>false alarms / stand-year on 65 unseen stands</sub></td>
<td align="center"><b>≈ 247 kt C</b><br><sub>carbon stock, pilot area</sub></td></tr>
</table>

<!-- VIDEO_PLAYER -->
<p align="center"><a href="docs/demo_video.mp4"><img src="docs/assets/video_poster.png" alt="Demo video: click to play the 2-minute video" width="80%"></a><br>
<sub>▶ <a href="docs/demo_video.mp4"><b>Play the 2:14 demo video</b></a> (English narration, Arabic subtitles) ·
<a href="docs/slides.pdf"><b>Slides (PDF)</b></a> · <a href="notebooks/01_blue_carbon_guardian.ipynb"><b>Main notebook</b></a> ·
<a href="dashboard/index.html"><b>Dashboard</b></a> (download and open)</sub></p>

<a id="judges"></a>
## 🏆 For the judges: each criterion and where the evidence is
| Criterion | What we show | Evidence |
|---|---|---|
| 💡 **Creativity / innovation** | A **tide-aware** monitor: on Gulf tidal flats the tide, not the trees, drives most index noise, so we model it out. A **200 m cell** trigger finds partial losses that stand averages hide. | 29-35 % less noise; 3 of the 5 real losses were seen **only** by cells ([§8](#8-results-and-limitations)) |
| 🧪 **Validity / technical soundness** | Every detection rate is quoted **with its chance rate**; thresholds tested on stands the model never saw; real events confirmed on dated sub-metre imagery; one of our own early claims withdrawn | 73 % vs 13 % by chance; 0.79 false alarms per stand-year out of sample; 5 conversions confirmed ([§8](#8-results-and-limitations)) |
| 🌈 **Hyperspectral bonus** | Two EnMAP epochs (224 bands) over the pilot: an independent check of Sentinel-2 and a spectral read of what the land became | r = 0.84-0.99 with Sentinel-2; stand 5 turns from a vegetation to a mineral spectrum ([§8](#what-hyperspectral-added)) |
| 🛠️ **Practical application / product** | Self-contained dashboard, automatic site reports, alert API concept; the notebook runs offline in about 25 s | [`dashboard/`](dashboard/index.html), [`reports/`](reports/), [`docs/api_alert_concept.md`](docs/api_alert_concept.md), [how a user receives it](#how-a-user-receives-it) |
| 🌍 **Benefits, relevance, SDGs** | UAE and Saudi pledges of 100 M mangroves each by 2030; Abu Dhabi's Gulf mangrove monitoring guide (Feb 2026); carbon at stake per stand | ≈ 247 kt C in the pilot area; SDG 13, 14, 15 ([§2](#2-the-problem)) |
| 💼 **Business viability** | Three priced tiers (hypotheses for a pilot), measured cost to serve, competitors named | about USD 3.3k cost per site per year; [`docs/business_plan_draft.md`](docs/business_plan_draft.md) (13 sources) |
| 🎤 **Presentation** | 2-minute video, 16 slides in the guide's order, this README | [`docs/demo_video.mp4`](docs/demo_video.mp4), [`docs/slides.pdf`](docs/slides.pdf) |

**What is new compared with what exists today**
| | Field surveys | One-off satellite maps | Free loss alerts (Global Mangrove Watch) | **Blue Carbon Guardian** |
|---|:-:|:-:|:-:|:-:|
| How often | campaigns | yearly or less | monthly | **every ~5 days** |
| Corrects for the tide | n/a | not usually | not documented | ✅ |
| Says *where inside* a stand | ✅ | ➖ | ➖ | ✅ 200 m cells |
| Published false-alarm rate | n/a | n/a | accuracy only | ✅ about 1 per stand-year |
| Carbon at stake per alert | ➖ | ➖ | ➖ | ✅ |
| Gulf coverage | ✅ | ✅ | not confirmed | ✅ Abu Dhabi + Tarut Bay |

<sub>We see Global Mangrove Watch as complementary, not as a rival (details and sources in the business plan).</sub>

---

## 1. Business use case
| 👤 User | 🎯 Decision | 🕰️ What they use today |
|---|---|---|
| **Environment agencies** (Environment Agency Abu Dhabi, MOCCAE; Saudi Arabia's NCVC) | Which stands to inspect this month? Is a protected stand intact? | Periodic field surveys, one-off studies |
| **Planting programmes and carbon-project developers** (for example ADNOC, Red Sea Global) | Is the carbon stock we report still there? Evidence for verification. | Field plots and drone surveys, campaign by campaign |
| **Coastal developers, environmental-impact consultants, regulators** | Did construction stay outside the mangrove line? | Comparing two dated images by eye |

**Offer (hypotheses for a pilot):**
- **Monitor**, USD 12k per site per year: alert, cell map, condition, carbon, monthly site reports.
- **Evidence**, USD 25k: adds a high-resolution check of every alert and an audit pack.
- **Development watch**, USD 8k per construction project.

The measured cost to serve is about USD 3.3k per site per year. Satellites and compute are nearly free; the cost is analyst time and high-resolution
images bought only when an alert fires. Full plan with 13 sources: [`docs/business_plan_draft.md`](docs/business_plan_draft.md).

## 2. The problem
- 🌱 **The UAE and Saudi Arabia each pledge 100 million mangroves by 2030.** Abu Dhabi published the Gulf's first mangrove monitoring guide in February 2026,
  yet the latest regional review calls Gulf monitoring "uneven" (Frontiers in Marine Science, 2025).
- 🏗️ **The stands are small, scattered and next to fast coastal development.** The Gulf has about 165 km² of mangrove, 55-60 km² of it in Abu Dhabi.
- 🛰️ **Why satellites:** free 5-day Sentinel-2 revisits cover every stand since 2015. Nobody can survey every stand every month on foot.
- 🌊 **Why it is hard:** on Gulf tidal flats the **tide**, not the trees, drives most of the change in a satellite index (r about -0.9 with a wetness signal).
  A naive monitor raises false alarms at every high tide.

## 3. Data used
| Dataset | Provider | Dates | Level | Used for | Licence |
|---|---|---|---|---|---|
| 🛰️ **Sentinel-2 MSI** | ESA / Copernicus, via Microsoft Planetary Computer STAC | 2020-01-01 to 2026-09-19 · 778 dates · tiles 40RBN, 39RUK | L2A surface reflectance | all time series | free and open: "Contains modified Copernicus Sentinel data 2020-2026" |
| 🗺️ **WorldCover v200** | ESA | 2021 | 10 m land cover, class 95 (mangroves) | stand outlines | CC BY 4.0, doi 10.5281/zenodo.7254221 |
| 🌈 **EnMAP** (224 bands, 420-2450 nm, 30 m) | DLR | 1 Nov 2022 · 14 Apr 2025 | L2A land | independent check; what the land became | EnMAP licence v1.1: "Contains modified EnMAP data © DLR 2022, 2025". Raw scenes are **not** redistributed |
| 🌳 **Field carbon plots** | Schile et al. 2016, Dryad doi 10.15146/R3K59Z | 2013-2014 | plot data | carbon density | CC0 |
| 🔍 **World Imagery Wayback** (Maxar WorldView-2/3, Legion-1, 0.31-0.5 m) | Esri | captures 2021-2025 | basemap | confirming the conversions (viewed only, nothing stored) | Esri, Maxar, Earthstar Geographics, and the GIS User Community |

Satellite 813 data were not available during the PoC (per the onboarding guide); the method is ready for them at incubation.

## 4. Technical approach
```mermaid
flowchart LR
    A["🗺️ Stands & 200 m cells<br/>WorldCover 2021, ≥ 3 ha<br/>interior pixels only"] --> B["🛰️ Sentinel-2 L2A<br/>778 dates 2020-26<br/>cloud mask (SCL)"]
    B --> C["📈 Indices per stand & cell<br/>NDVI · red edge (NDRE)<br/>SWIR moisture (NDMI) · wetness (MNDWI)"]
    C --> D["🌊 Tide-aware robust model<br/>trend + season + tide terms<br/>refitted monthly"]
    D --> E{"🚨 Alert<br/>stand ≤ −1.5σ<br/>OR any cell ≤ −3.5σ"}
    D --> F["📉 Condition<br/>last 12 months<br/>vs 2020-21"]
    E --> G["🧭 Decision layer<br/>cell map · carbon at stake<br/>dashboard · site reports"]
    F --> G
    H["🌳 Field carbon<br/>108 t C/ha"] --> G
    I["🌈 EnMAP · 🔍 sub-metre captures<br/>independent checks"] -.-> G
    style A fill:#E8F2FF,stroke:#2F80ED
    style B fill:#D6E8FF,stroke:#2F80ED
    style C fill:#C3DDFF,stroke:#2F80ED
    style D fill:#1E6FD9,color:#fff,stroke:#1E6FD9
    style E fill:#0EA5E9,color:#fff,stroke:#0EA5E9
    style G fill:#0A3D91,color:#fff,stroke:#0A3D91
    style F fill:#C3DDFF,stroke:#2F80ED
    style H fill:#E8F2FF,stroke:#2F80ED
    style I fill:#E8F2FF,stroke:#2F80ED
```
1. **Stands and cells.** ESA WorldCover 2021 mangrove patches of at least 3 ha become stands: 25 pilot stands (2,281 ha) and 65 unseen test stands in Abu
   Dhabi and Saudi Arabia's Tarut Bay. Each stand is cut into 200 m cells.
2. **Series.** For every clean Sentinel-2 date, the median of each index over each stand's and cell's interior pixels, plus the flooded fraction.
3. **Tide-aware model.** A robust (Huber) regression of each index on trend + 2 seasonal harmonics + **tide terms** (MNDWI, MNDWI², flooded fraction),
   refitted every month on the window [t - 36 months, t - 3 months].
4. **Alert.** z = (observed - expected) / robust sigma, averaged over the three indices; the state is the median of the last 5. **Stand state ≤ -1.5 OR any cell
   state ≤ -3.5.** Both thresholds were calibrated together to about 1 false-alarm episode per stand-year.
5. **Condition.** Tide-corrected index over the last 12 months against the 2020-21 median: severe decline, decline, stable or improving.
6. **Carbon.** Area x field density, 108 t C/ha (90 % CI of the mean 79-138): a **stock** with a range, never a sequestration rate.
7. **Checks:**
   - simulated losses with a chance baseline;
   - 65 out-of-sample stands;
   - EnMAP on the same dates;
   - dated sub-metre captures of every converted site.

Code: [`src/bcg/monitor.py`](src/bcg/monitor.py) (core) and [`analysis/`](analysis/) (34 numbered scripts with a summary per result; index in
[`analysis/README.md`](analysis/README.md)).

<a id="how-a-user-receives-it"></a>
### How a user receives it
```mermaid
%%{init: {"theme":"base","themeVariables":{"actorBkg":"#E8F2FF","actorBorder":"#1E6FD9","actorTextColor":"#06235A","actorLineColor":"#9CC8F0","signalColor":"#1E6FD9","signalTextColor":"#06235A","labelBoxBkgColor":"#D6E8FF","labelBoxBorderColor":"#1E6FD9","loopTextColor":"#06235A"}}}%%
sequenceDiagram
    participant S as 🛰️ Sentinel-2 (every ~5 days)
    participant P as ⚙️ Blue Carbon Guardian
    participant A as 🏛️ Agency / project developer
    participant I as 👷 Inspector
    S->>P: new scene (cloud-optimised, read in place)
    P->>P: tide-aware model per stand and per 200 m cell
    alt alert: stand ≤ −1.5σ OR any cell ≤ −3.5σ
        P->>P: check the flagged cells on sub-metre imagery (Evidence tier)
        P->>A: alert by email / JSON API, cell map, carbon at stake
        A->>I: inspect only the flagged cells
    else no alert
        P->>A: monthly site report (condition, trend, carbon)
    end
```

## 5. Installation
Requires **Python 3.12** (tested on 3.12.10). No GPU, no credentials, no API keys.
```bash
git clone https://github.com/Nahla-Nabil/blue-carbon-guardian.git
cd blue-carbon-guardian
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
```

## 6. How to run
```bash
jupyter lab notebooks/01_blue_carbon_guardian.ipynb
```
Run all cells; nothing needs editing. **Runtime is about 25 seconds on a laptop, offline.** We tested it in a fresh environment built from
`requirements.txt`, with 0 errors.
- **Reads** [`data/sample_input/`](data/sample_input/): real Sentinel-2 series of the 25 pilot stands and the 64 cells of stands 9, 12 and 18.
- **Writes** six figures and tables to [`results/`](results/).
- **Ends with** the headline numbers and their limits.

Full pipeline from the satellite archive (needs internet; about 20-60 min per Sentinel-2 step): see the rebuild order in
[`analysis/README.md`](analysis/README.md). The EnMAP steps need your own free DLR licence.

## 7. Example input and output
**Input:** [`data/sample_input/`](data/sample_input/) (3.7 MB). Its README lists the exact STAC collection, tile, dates and processing.

| 🌊 Tide correction cuts the noise by about a third | 🧩 Stand averages hide partial loss; 200 m cells do not |
|---|---|
| ![tide noise](results/01_tide_noise.png) | ![cells](results/03_cells_vs_stand_average.png) |
| 🚨 **Stand 9:** the worst cell crosses its alert level while the stand average barely moves | 📉 **Stand 5** (coastal development) against a stable stand |
| ![alert scores](results/05_stand9_alert_scores.png) | ![stand 5](results/02_stand5_vs_stable.png) |

<p align="center"><img src="docs/assets/stand5_before_after.png" alt="Stand 5 on Sentinel-2 true colour, 2021 and 2026: a coastal reclamation with finger canals takes part of the mangrove polygon" width="85%"><br>
<sub>Stand 5 on Sentinel-2 true colour, 2021 → 2026: a coastal reclamation takes part of the mangrove stand (yellow outline).</sub></p>

<p align="center"><img src="docs/assets/dashboard.png" alt="Blue Carbon Guardian dashboard: KPIs, condition map in 200 m cells, and the stand 9 panel" width="85%"><br>
<sub>The product: <code>dashboard/index.html</code> (one self-contained file). Condition map in 200 m cells; stand panel with where to inspect; carbon at stake.</sub></p>

## 8. Results and limitations
| What we measured | Result | How it was validated |
|---|---|---|
| Noise reduction from the tide model | **29-35 %** on every index | robust residuals, 25 stands, 2020-2026 |
| Real conversions inside our stands | **5** (stands 5, 9, 12, 18, 6), all coastal developments | dated WorldView-2/3 and Legion-1 captures (0.3-0.5 m); the alert began between the last undisturbed and the first disturbed capture at every site |
| Found only by the 200 m cells | **3 of 5** | the stand averages still read "stable" |
| Partial loss (a tenth of a stand losing half its canopy) caught within 60 days | **73 %**, against **13 %** by chance | semi-synthetic backtest with a no-loss null ([`analysis/29`](analysis/29_cell_trigger.md)) |
| Uniform 10 % loss caught within 6 months | **63 %**, against 36 % by chance | same |
| False alarms on unseen stands (thresholds fixed) | **0.79** per stand-year, against 0.96 calibrated | 65 stands, 305 stand-years, including Saudi Arabia ([`analysis/33`](analysis/33_scaleout_union_summary.md)) |
| EnMAP hyperspectral against Sentinel-2 | **r = 0.84-0.99** | same-date stand comparisons |
| Stand 5 loss | **26-62 ha** | two independent methods (Sentinel-2 change indicator, EnMAP pixels) |
| Carbon stock, pilot area | **≈ 247 kt C** (180-316) | 24 field plots near the stands |

### When did the alert start? (dated sub-metre captures)
Each bar is the gap between the last capture showing intact mangrove and the first showing works. The red diamond is the start of our alert.
```mermaid
%%{init: {"theme":"base","themeVariables":{"doneTaskBkgColor":"#9CC8F0","doneTaskBorderColor":"#1E6FD9","critBkgColor":"#FF4D6D","critBorderColor":"#C8384F","sectionBkgColor":"#F2F7FF","altSectionBkgColor":"#FFFFFF"}}}%%
gantt
    dateFormat YYYY-MM-DD
    axisFormat %b %Y
    section Stand 5
    intact to works visible :done, 2022-03-28, 2023-02-22
    alert :milestone, crit, 2022-10-25, 0d
    section Stand 9
    intact to works visible :done, 2022-03-28, 2023-02-22
    alert :milestone, crit, 2022-12-07, 0d
    section Stand 12
    intact to works visible :done, 2022-03-28, 2023-02-22
    alert :milestone, crit, 2022-12-17, 0d
    section Stand 6
    intact to works visible :done, 2022-03-28, 2023-02-22
    alert :milestone, crit, 2023-02-17, 0d
    section Stand 18
    intact to works visible :done, 2023-11-14, 2025-01-06
    alert :milestone, crit, 2024-10-29, 0d
```
<sub>Captures: WorldView-2/3 and Legion-1, 0.3-0.5 m, via Esri World Imagery Wayback (viewed only). Stand 9: works were under way next to the stand.
This is detection **during** the works, not advance warning. Details: [`analysis/34_vhr_summary.md`](analysis/34_vhr_summary.md).</sub>

<a id="what-hyperspectral-added"></a>
### What hyperspectral (EnMAP) added
<p align="center"><img src="docs/assets/enmap_stand5.png" alt="EnMAP spectra of stand 5 in November 2022 and April 2025: persistent pixels keep a vegetation spectrum, converted pixels change to a bright mineral-like spectrum" width="95%"><br>
<sub>Stand 5 on EnMAP, Nov 2022 vs Apr 2025: persistent pixels keep a vegetation spectrum; the 685 converted pixels (about 62 ha) turn into a bright,
mineral-like one (sand and fill). Contains modified EnMAP data © DLR 2022, 2025.</sub></p>

- **Independent check:** EnMAP-derived indices match our Sentinel-2 indices on the same dates (r = 0.84-0.99 across stands).
- **What the land became:** the converted part of stand 5 has a mineral spectrum, which points to reclamation, not dieback.
- **Honest result:** as a mangrove classifier, EnMAP did not beat multispectral bands here (F1 0.74 vs 0.72). Satellite 813 (~205 bands) slots into the
  same step at incubation.

**⚠️ Limits, stated honestly:**
- The alert is detection of works as they happen, **not advance warning**.
- Patches under about 0.6 ha and young plantings are not seen at 10 m.
- Outlines come from a 2021 land-cover map; extent accuracy is modest (F1 about 0.6).
- The confirmations use dated imagery, not site visits or permit records.
- Simulated losses are canopy-cover losses, not leaf stress.
- EnMAP did **not** beat multispectral as a classifier (F1 0.74 against 0.72).
- Carbon density comes from 4 nearby sites (2013-14).
- Reference labels are AI-assisted photo-interpretation.
- We **withdrew** our own first backtest figure (58 % / 90 %) when a null test showed that its metric counted alerts that were already running.

## 9. Author, tools, licence and attribution
**👩‍💻 Author: Nahla Nabil** (Bahrain), Team Blue Athar. Idea, satellite data pipeline, tide-aware model, validation, dashboard and business case.

| 🧰 Tools | Used for |
|---|---|
| Python 3.12 · NumPy · pandas · SciPy · scikit-learn | modelling, statistics, validation |
| rasterio · shapely · pystac-client · planetary-computer | reading Sentinel-2 / WorldCover / EnMAP straight from the cloud (STAC, COG) |
| Matplotlib · Jupyter | figures, notebook |
| HTML + SVG + JavaScript | self-contained dashboard and site reports |
| Playwright · FFmpeg · edge-tts | slide export, demo video (generated narration and music) |
| Claude (Anthropic), an AI coding assistant | assisted development. All results are reproducible from this repository |

**Licence:** code under the MIT licence ([`LICENSE`](LICENSE)). Data keep their own licences (section 3).

**Built on:**
- the official 813 Challenge starter notebooks and data guidance;
- ESA / Copernicus Sentinel-2 via Microsoft Planetary Computer;
- ESA WorldCover;
- DLR EnMAP;
- Schile et al. 2016;
- Esri World Imagery Wayback.

<details><summary><b>📁 Repository layout</b></summary>

```
README.md  LICENSE  requirements.txt
notebooks/01_blue_carbon_guardian.ipynb   main analysis, runs end to end on the sample (outputs committed)
data/sample_input/                        example input (real Sentinel-2 series) + how it was produced
results/                                  example output written by the notebook
src/bcg/monitor.py                        core model (tide-aware monitor, condition, alert rule)
analysis/                                 full pipeline: 34 numbered scripts, a summary .md per result, data/ tables, figures/
dashboard/index.html                      product demo (self-contained)
reports/                                  automatic per-stand site reports
docs/                                     slides.pdf, demo_video.mp4, business plan, API and alert concept, README assets
deck_source/                              slide sources
video/                                    demo-video sources (narration EN + AR, motion graphics, renderer)
scripts/                                  sample-input and notebook builders, slide export, README visuals (banner, alert story), EnMAP download helper
```
</details>

<details><summary><b>✅ PoC submission checklist (official guide)</b></summary>

| Requirement | Where |
|---|---|
| README with the 10 points, in order | this file: title block, then sections 1-9 |
| Functioning notebook with outputs committed | [`notebooks/01_blue_carbon_guardian.ipynb`](notebooks/01_blue_carbon_guardian.ipynb) |
| Pinned `requirements.txt` and Python version | [`requirements.txt`](requirements.txt), Python 3.12 |
| Example input | [`data/sample_input/`](data/sample_input/) (real data + exact STAC parameters) |
| Example output | [`results/`](results/) |
| Slides PDF | [`docs/slides.pdf`](docs/slides.pdf) |
| Licence and data attribution | [`LICENSE`](LICENSE), section 3 |
| No credentials, no restricted imagery | raw EnMAP scenes and Esri imagery are not in the repository |
</details>
