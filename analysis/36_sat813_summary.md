# Simulated Satellite 813 (analysis/36, 22 Oct 2026)

**Question.** Satellite 813 (~205 bands, ~400–1700 nm, 20 m) was not available in the proof of concept. Does our hyperspectral step still work if we
only have the 813 spectral range?

**Set-up.** The two EnMAP scenes used in analysis/18 (1 Nov 2022, 14 Apr 2025). "813 range" = the EnMAP bands inside 400–1700 nm, with the
water-vapour window 1340–1460 nm removed: 152 of 216 usable bands. Same stand-5 pixel groups as analysis/18 (679 converted, 258 persistent
vegetation pixels). Reference spectra = pure WorldCover-2021 pixels (fraction ≥ 0.8) in the 2022 scene. Class matching = smallest spectral angle.
Classifiers = Random Forest, 5-fold spatial-block cross-validation (~750 m blocks). Script: `analysis/36_sat813_sim.py`; numbers in
`analysis/data/sat813_sim.json`; figure `analysis/36_sat813_sim.png`.

**What the simulation is not.** Not real 813 data (no 813 noise, calibration or band shapes). Spatially conservative: the cube stays at EnMAP's
30 m, while 813 is 20 m. Spectrally coarser than 813: EnMAP samples ~6.5 nm (VNIR) / ~10 nm (SWIR) against 813's ~5 nm.

## Results

| Test | Full EnMAP (420–2450 nm) | 813 range (400–1700 nm) |
|---|---|---|
| T1 · monitor indices (NDVI, red edge, NDMI at 1610 nm, MNDWI) inside the range | yes | **yes, all four** (only Sentinel-2 B12 at 2190 nm falls outside, and the monitor does not use it) |
| T2 · stand-5 converted pixels whose 2025 spectrum matches bare / built-up | 78 % | **97 %** |
| T2 · persistent-vegetation pixels whose 2025 spectrum matches bare / built-up (false positives) | 0 % | **0.4 %** |
| T2 · median spectral-angle change 2022 → 2025, converted vs persistent | 27° vs 12° | 21° vs 12° |
| T3 · stand-5 area "mangrove-like → bare/built-like" | 53 ha | **61 ha** (NDVI rule of analysis/18: 62 ha); 2025 labels agree on 85 % of pixels |
| T4 · F1 mangrove vs other vegetation (S2-like bands: 0.72) | 0.75 ± 0.02 | 0.73 ± 0.03 |
| T4 · F1 bare / sand vs built-up (S2-like bands: 0.88; S2-like without B12: 0.79) | 0.95 ± 0.02 | **0.91 ± 0.02** |

## Reading
- **The fingerprint survives.** With only the 813 range, the stand-5 conversion still reads as vegetation → sand / fill: 97 % of converted pixels
  match a bare or built-up spectrum in 2025, against 0.4 % of the persistent vegetation next to them. The converted area (61 ha) sits inside the
  26–62 ha range we already quote.
- **Every monitor index fits.** Sentinel-2 can say *when* and 813 can say *what*, with the same indices.
- **What 813 adds over Sentinel-2-like bands:** telling bare sand / fill from built-up surfaces (F1 0.91 vs 0.88, and 0.79 if Sentinel-2's SWIR-2
  band is also unavailable). That is the distinction between "land is being reclaimed" and "buildings are going up".
- **What 813 loses against the full EnMAP range:** a little (0.91 vs 0.95 for sand vs built-up). It also confirms mangrove identity less well:
  only 48 % of the persistent-vegetation pixels match the mangrove reference in 2022 with the 813 range, against 83 % with the full spectrum.
- **No gain for mangrove vs other vegetation** (0.73 vs 0.72 for S2-like bands): same conclusion as analysis/18.

**APPROVED wording:** "We simulated Satellite 813's band range with EnMAP (400–1700 nm, at 30 m; not real 813 data). The stand-5 conversion still
reads as vegetation to sand and fill: 97 % of converted pixels match a bare or built spectrum in 2025, against 0.4 % of the vegetation next to them.
Every index the monitor uses fits inside the range, and for telling sand from buildings the 813 range beats Sentinel-2-like bands (F1 0.91 vs 0.88)."

**NOT allowed:** "tested on Satellite 813 data", "813 detects loss", "813 is better than EnMAP", "813 classifies mangroves better", any species claim.

Contains modified EnMAP data © DLR 2022, 2025.
