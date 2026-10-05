# Blue Carbon Guardian: business plan (PoC, English)

**Status (27 Sep 2026):** draft for the PoC submission. Every number is either **measured** by us, **sourced** (list at the end), or an **assumption**
marked (A). Nothing here is a validated market study. A pilot must test the prices and the time per alert.

## 1. Problem and customers
The Gulf is planting mangroves at national scale:
- UAE: 100 million by 2030 [1].
- Saudi Arabia: more than 100 million by 2030 [2]. About 72 million planted is reported by secondary sources; verify before quoting.
- ADNOC: 10 million by 2030, more than 5 million planted [3].
- Red Sea Global: 50 million by 2030 [4].

Existing stands are small and scattered: about 165 km² in the whole Gulf, of which Abu Dhabi alone holds 55-60 km², plus about 200 km² on the Red Sea [5].
They sit next to some of the fastest coastal development in the world. Abu Dhabi's environment agency published the first mangrove monitoring guide for the Gulf in
Feb 2026 [6], so the regulator is asking for monitoring. What is missing is **frequent, stand-level, auditable** evidence of where mangroves are being lost and
how much carbon is at stake.

| Customer | Decision we support | What they do today |
|---|---|---|
| Environment agencies (EAD, MOCCAE; Saudi NCVC) | where to send inspectors; is a protected stand intact? | periodic field surveys, one-off studies, citizen science [6] |
| Planting programmes and developers (ADNOC, Red Sea Global, carbon-project developers) | is the stock we report still there; evidence for credit verification | field plots and drone surveys per campaign |
| Coastal developers, EIA consultants, regulators | did construction stay outside the mangrove line? | comparing two dated images by eye |

## 2. What we sell (all of it is built in the PoC)
- **Alert:** "stand average OR any 200 m cell", calibrated to about 1 false alarm per stand per year.
- **Where:** a map of the 200 m cells, so an inspector knows where to go.
- **Condition:** each stand against its own 2020-21 baseline.
- **Carbon at stake:** field-grounded (108 t C/ha), with a range.
- **Reports:** an automatic site report per stand.
- **Hyperspectral check:** EnMAP (Satellite 813 at incubation).

Demonstrated on 25 stands (2,281 ha) and 66 more unseen stands (1,964 ha), including one block in Saudi Arabia:
- 5 coastal-development conversions inside the stands, confirmed on dated sub-metre imagery; 3 of them were found only by the cell layer.
- In simulation, a partial loss (a tenth of a stand losing half its canopy) is caught within 60 days in about 73 % of cases, against 13 % by chance.
- Out of sample (65 unseen stands, thresholds fixed): 0.79 false-alarm episodes per stand-year, against 0.96 calibrated.

## 3. Alternatives and why a customer would pay us
| Alternative | Strength | Gap we fill |
|---|---|---|
| Global Mangrove Watch monthly loss alerts [7] | free, global; 92 % accuracy reported | started in Africa and is expanding; we could not confirm Gulf coverage (Sep 2026). NDVI thresholds, no tide model, no stand condition, no carbon or reports. We can use GMW extent as input: complementary |
| Field and drone surveys | ground truth, plot carbon | expensive and infrequent; drone surveys are much cheaper than ground plots [8] but are still campaigns |
| Commercial very-high-resolution imagery, monthly | 30-50 cm detail | USD 19 / km² archive, USD 29 / km² tasking [9]: about USD 5,200-8,000 a year in imagery alone for one site's 23 km² of stands, before any analysis |
| In-house tools (ADNOC uses ML to track its plantings [3]) | integrated | ADNOC is a possible partner or customer; the others lack an independent, calibrated, auditable layer |

**Our edge:**
- We model the tide. Tide is the dominant noise on Gulf tidal flats, and correcting for it cut noise by 30-35 %.
- The alert has a measured false-alarm budget.
- The cell layer catches partial losses that stand averages hide.
- Every number is traceable to data. Very-high-resolution imagery is bought **only when an alert fires**.

## 4. Unit economics (per "site" = one ~13 x 10 km block, like our pilot: 25 stands, about 2,300 ha of mangrove)
| Cost item | Per site per year | Basis |
|---|---|---|
| Satellite data | 0 | Sentinel-2, WorldCover, EnMAP are free |
| Compute | < USD 5 | **measured**: full 2020-2026 archive (778 dates) for one block = 22-73 min on 8 threads; monitor for 620 cells = 2 min. At USD 0.384/h for an 8-vCPU cloud VM [10], the whole backfill costs < USD 0.50; monthly updates (~10 new dates) cost cents |
| High-resolution confirmation of alerts | USD 500-750 | ~25 alerts per year (1 per stand-year, **measured**) x 1 km² minimum x USD 19-29 / km² [9] |
| Analyst review and reports | USD 2,000 (A) | 1 h per alert + 2 h per monthly report = ~50 h x USD 40/h (A) |
| Hosting, storage, support | USD 600 (A) | small static dashboard + database |
| **Cost to serve** | **about USD 3,100-3,400** | |

The cost is people and targeted imagery, not satellites or compute. Compare USD 5,200-8,000 a year for blanket monthly high-resolution imagery of one site,
before any analysis.

## 5. Price hypothesis (to be tested in the pilot)
| Offer | Price (A) | Gross margin at cost above |
|---|---|---|
| **Monitor**: alerts, cell map, condition, carbon, monthly site reports | USD 12,000 per site per year (about USD 5 / ha / year) | about 72 % |
| **Evidence**: Monitor + high-resolution confirmation of every alert + quarterly evidence pack for auditors + hyperspectral check | USD 25,000 per site per year | about 70 % (A: more analyst time) |
| **Development watch** (EIA): one construction project next to mangroves, alerts + monthly compliance report | USD 8,000 per project per year | about 75 % (A: cost USD 2,000) |

Anchors, not proof:
- Our flagship case, stand 5, lost 26-62 ha, holding about 2.8-6.7 kt C: about USD 0.28-0.66 million at USD 27 / tCO2e [11]. Monitor is 2-4 % of that one event.
- Mangrove conservation projects cost about USD 12 / tCO2e on average, restoration about USD 270 / tCO2e [12]; monitoring is one of their recurring per-project costs.
- No reliable public per-hectare cost of field MRV was found. The pilot will benchmark against the customer's own survey costs.

## 6. Market size (bottom-up, honest)
- **Existing Gulf + Red Sea mangroves:** about 365 km² (165 + 200 [5]), about 16 pilot-size sites. At USD 12-25k each, that is **USD 0.2-0.4 million a year**:
  a niche on its own.
- **Planted stands:** the four programmes above add several hundred million seedlings. They become visible to 10 m satellites only as canopies close, so this is a
  growing, multi-year market. Young plantings need very-high-resolution imagery or Satellite 813 (incubation).
- **Development watch:** every coastal project near mangroves needs compliance monitoring. The count is unknown and is an open item.
- **Beyond the region:** 147,359 km² of mangroves worldwide [13]. Arid-coast mangroves (Red Sea, Oman, Iran, Pakistan, East Africa) share our tide and
  small-stand problem.

**The economic potential is not selling small subscriptions one by one.** It is:
1. a national MRV contract for a 100-million-mangrove programme;
2. becoming the monitoring layer on a platform such as Space42's gIQ;
3. licensing the tide-aware and cell-level method to others.

## 7. Go-to-market and milestones
1. **Oct-Dec 2026 (incubation):** one pilot with an Abu Dhabi stakeholder (EAD, ADNOC or a coastal developer) through the hackathon network. Measure time per
   alert and imagery cost, and confirm the 4 conversions with the partner's records or high-resolution imagery.
2. **Q1 2027:** deploy on gIQ; add Satellite 813 when available; first paid site.
3. **2027:** 3-6 paid sites across the UAE and Saudi Arabia; bid for a national programme monitoring contract.

## 8. Three-year scenario (all figures are assumptions (A), for illustration; cost to serve: USD 3.3k per Monitor site, 7.5k per Evidence site, 2k per project)
| Year | Sites (Monitor / Evidence) | Development-watch projects | Revenue | Cost to serve | Team (3 people, A: USD 180k/yr) |
|---|---|---|---|---|---|
| 2027 | 2 / 0 (+1 free pilot) | 1 | USD 32k | USD 12k | covered by incubation / grants (A) |
| 2028 | 5 / 2 | 4 | USD 142k | USD 40k | USD 180k (result: -78k) |
| 2029 | 10 / 5 | 8 | USD 309k | USD 87k | USD 180k (result: +42k) |

Break-even on this path is around year 3. A single national contract would bring it forward. Without one, this stays a small business, and we say so.

## 9. Risks
| Risk | Mitigation |
|---|---|
| Few paying customers in a small market | pilot first; aim for a national contract or a platform licence |
| Free global tools (GMW) expand into the Gulf | be the calibrated, tide-aware, stand-level product with carbon and reports; use GMW as an input |
| Validation limits: 4 events seen at 10 m, AI-assisted labels, simulated losses | confirm with a partner's records or high-resolution imagery in the pilot; publish the method |
| Young plantings invisible at 10 m | very-high-resolution / Satellite 813 tier at incubation |
| Carbon uses 4 nearby field sites (2013-14) | partner field plots; report ranges, never sequestration rates |
| Price and analyst time are assumptions | measure both in the pilot |

## Sources
[1] UAE / MOCCAE COP26 pledge and Abu Dhabi Mangrove Initiative (mediaoffice.abudhabi, ead.gov.ae, admangroves.ae).
[2] Saudi Green Initiative: more than 100 million mangroves by 2030 (vision2030.gov.sa, sgi.gov.sa); "72 million planted": thesauditimes.net (secondary, verify).
[3] ADNOC press releases 2023-2025 and Abu Dhabi Media Office (10 million by 2030; 5 millionth seedling; drone planting; ML monitoring).
[4] Red Sea Global, "on track to plant 50 million mangrove trees by 2030", redseaglobal.com, Jul 2023.
[5] Frontiers in Marine Science 2025 review of Middle Eastern mangroves, doi 10.3389/fmars.2025.1695426 (Gulf ~165 km², Abu Dhabi 55-60 km², Red Sea ~200 km²).
[6] Gulf News, 24 Feb 2026: EAD with the IUCN Mangrove Specialist Group, supported by ADNOC, the British Embassy and ZSL, launches the first mangrove monitoring guide for the GCC.
[7] Mangrove Alliance, 29 Aug 2025; Bunting et al., Remote Sensing 15:2050 (2023), GMW monthly alerts, Africa prototype, 92 % accuracy.
[8] Geocarto International 2024 review of UAV monitoring of mangrove blue carbon (UAV-SfM cheaper than ground plots).
[9] SkyWatch data pricing page, Sep 2026: very high resolution (30-49 cm) archive USD 19 / km², tasking USD 29 / km².
[10] Azure Standard_D8s_v5, 8 vCPU / 32 GiB, from USD 0.384 / h pay-as-you-go (cloudprice.net / instances.vantage.sh, Sep 2026).
[11] S&P Global Platts blue-carbon assessments 2024-2025 (USD 25-29 / tCO2e; record 29.30 on 28 Aug 2025).
[12] Blue Carbon Cost Tool, Frontiers in Marine Science 2025, doi 10.3389/fmars.2025.1622255 (mean USD 12 / tCO2e conservation, USD 270 / tCO2e restoration).
[13] Bunting et al. 2022, Global Mangrove Watch v3.0, Remote Sensing 14:3657 (147,359 km² in 2020).
Contains modified Copernicus Sentinel data; contains modified EnMAP data (c) DLR 2022, 2025.
