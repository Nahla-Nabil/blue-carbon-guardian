# Sub-metre confirmation of the five conversions (analysis/34, 34b; 27 Sep 2026)

Source: Esri World Imagery Wayback, with dated captures read from each release's metadata (`data/vhr_captures.json`). At all five sites the same captures
exist: WorldView-3 (0.31 m) on 13 Aug 2016, 19 Sep 2018 (31 Aug 2018 at stand 9) and 19 Oct 2019; WorldView-2 (0.5 m) on 24 May 2020, 8 Jun 2021, 28 Mar 2022
and 22 Feb 2023; WorldView-3 (0.31 m) on 14 Nov 2023; Legion-1 (0.34 m) on 6 Jan 2025.
Viewed at zoom 17 with the flagged 200 m cells outlined (34b writes the images outside the project; Esri imagery is not redistributed).
Imagery: Esri, Maxar, Earthstar Geographics, and the GIS User Community.

Stand 6 was checked afterwards with `34b_vhr_view.py 6`.

| Stand | What the dated captures show | Last capture before works | First capture with works | Start of our alert (combined rule) |
|---|---|---|---|---|
| 5 | Intact mangrove fringe beside a sand flat; by Feb 2023 the flat is being cut into canals and islands and the north-western flagged cells are cleared; finger canals complete by Nov 2023 | 28 Mar 2022 | 22 Feb 2023 | **25 Oct 2022**, inside the window |
| 9 | Intact in Mar 2022; by Feb 2023 a canal-island development is built along the eastern edge; by Nov 2023 a dredged channel cuts through the flagged south-eastern mangrove | 28 Mar 2022 (works next to the stand) / 22 Feb 2023 (the mangrove itself) | 22 Feb 2023 / 14 Nov 2023 | **7 Dec 2022**, when works next to the stand were under way |
| 12 | Intact in Mar 2022; by Feb 2023 a new road crosses the stand and reclamation lagoons are being built at its southern edge; by Nov 2023 a canal cuts the edge; built up by Jan 2025 | 28 Mar 2022 | 22 Feb 2023 | **17 Dec 2022**, inside the window |
| 6 | Sparse mangrove (NDVI 0.06-0.27) on a tidal flat, intact in Mar 2022; by Feb 2023 new canals encircle it and the land to the east is cleared; by Jan 2025 the north-eastern flagged cell is open water (a lagoon) and houses stand to the north | 28 Mar 2022 | 22 Feb 2023 | **17 Feb 2023** (cells), inside the window |
| 18 | Intact through Mar 2022; circular lagoons reach its south-eastern side by Feb 2023; the flagged cells are still vegetated in Nov 2023; construction enters them by Jan 2025 | 14 Nov 2023 | 6 Jan 2025 | **29 Oct 2024**, inside the window |

## Reading
- **All five conversions are confirmed at 0.3-0.5 m** (stand 6, first listed as "cause unclear", turned out to be development too: a lagoon replaced part of it). Until now they had been seen only at Sentinel-2's 10 m.
- **This resolves the earlier puzzle** of alerts that started before the dated start of change (analysis/21, 28, 31). Those dates came from a ramp fitted to
  10 m index series, and they lag the first ground disturbance. At every site, the alert began between the last undisturbed and the first disturbed sub-metre
  capture (for stand 9: while works were under way next to it).
- Still **detection of works as they happen, not advance warning**. The captures are months apart, so they bracket a date; they do not pin it.

Approved wording: "Sub-metre imagery (WorldView-2/3, Legion-1; dated captures via Esri World Imagery Wayback) confirms five conversions (stands 5, 9, 12, 18, 6). At each site our
alert began between the last undisturbed capture and the first capture showing works."
NOT allowed: "field-verified", "advance warning", any exact start date from these captures.
