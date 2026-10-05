# Module 3 results: EnMAP hyperspectral (2026-09-23)

Contains modified EnMAP data (c)DLR 2022, 2025.

Scenes: 2022-11-01 (DT4978, quality 0, cloud 2 %, covers all 25 stands) and 2025-04-14 (DT124368, quality 0, cloud 3 %, covers 14 stands incl. stand 5).
L2A land mode, 224 bands 418-2446 nm, 30 m, reflectance = DN x 0.0001. The product's cloud/haze flags were NOT applied: they mislabel bright reclaimed sand
(83 % of stand 5 flagged "cloud" on 14 Apr 2025 while Sentinel-2 on the same day is clear). Water-vapour and noisy SWIR bands (1340-1460, 1790-1960, >2450 nm) dropped.
Pure pixels = WorldCover-2021 mangrove fraction >= 0.7.

## 1. Cross-sensor consistency (does our Sentinel-2 chain agree with an independent hyperspectral sensor?)

EnMAP bands averaged to Sentinel-2 bands; per-stand medians vs our Sentinel-2 stand medians on (almost) the same date.

| date | stands | NDVI r | NDRE r | NDMI (SWIR moisture) r | MNDWI r |
|---|---|---|---|---|---|
| 1 Nov 2022 vs S2 2 Nov 2022 | 25 | 0.97 | 0.95 | 0.84 | 0.91 |
| 14 Apr 2025 vs S2 14 Apr 2025 | 14 | 0.99 | 0.98 | 0.97 | 0.97 |

Pearson r across stands. Small mean offsets (S2 minus EnMAP NDVI: -0.08 in 2022, +0.01 in 2025) are expected from band definitions, pixel size and a one-day gap.

## 2. Stand 5, two epochs (pixel level, 30 m, mangrove fraction >= 0.5, 1,518 pixels = 136.6 ha)

- converted (NDVI >= 0.25 in Nov 2022 and < 0.15 in Apr 2025): 685 px = 61.6 ha (45 %)
- persistent vegetation (>= 0.25 in both): 312 px = 28.1 ha
- other: 521 px

Spectra: converted pixels go from a vegetation spectrum (red-edge jump, leaf-water absorptions) to a bright, flat, mineral-like spectrum (high SWIR reflectance),
consistent with bare sand or construction material.

**Third estimate of the stand-5 conversion: EnMAP 62 ha vs Sentinel-2 epoch-difference indicator 26 ha (conservative rule). Report the range 26-62 ha; the Sentinel-2 indicator is a lower-bound screening flag.**

Caveats: Nov vs Apr differ in season and tide; the NDVI thresholds are ours; 30 m pixels mix surfaces.
Persistent pixels: NDVI 0.58 -> 0.35, red-edge position -0.8 nm, WBI -0.04, NDII1650 -0.06. Season and tide confounded, NOT evidence of physiological stress.

## 3. Does hyperspectral add separability? (mangrove vs other vegetation)

Random forest, spatial-block CV, n = 2,890 pixels, 150 blocks, WorldCover labels.
Sentinel-2-like 7 bands (simulated from EnMAP): F1 0.722 +/- 0.056. EnMAP full spectrum (~216 bands): F1 0.742 +/- 0.048.
Difference +0.02, within noise: **no significant added separability demonstrated** with these (noisy) labels.

## 4. Mangrove vs brown "hummocky scrub"

AI-assisted reference points inside the scene: 73 mangrove (confidence >= 2) vs 19 scrub/marsh; 3x3 pixel medians.
AUC (Mann-Whitney): NDVI 0.75, NDRE 0.76, red-edge position 0.76, NDWI1240 0.71, WBI 0.70, NDMI 0.68, NDII1650 0.68, 2100 nm absorption 0.66; all p < 0.05.
The scrub is spectrally less vigorous than mangrove, which supports our labels, but Sentinel-2-type indices separate as well as the hyperspectral-only ones.
Species identity (Avicennia vs halophyte) is NOT resolved.

## Honest bottom line: does hyperspectral add value?

Yes, as an independent validator (strong agreement with Sentinel-2 indices) and as a material-identity check on conversions (vegetation to mineral/construction spectrum).
NOT demonstrated: a better classifier, or an early stress detector, with the data we have (two dates, season-confounded, noisy labels). Leaf-physiology stress detection remains future work.
