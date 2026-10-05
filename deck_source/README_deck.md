# Deck source (Slides Artifact type), v3 of 27 Sep 2026: 14 slides

This is the master copy. The old artifact link (claude.ai/artifact/WLKcW2jw74kAxJBut3RFy5) could not be reached from Claude Code on 27 Sep 2026, and v3 is **not published**.

Order (deck.json): cover, problem, solution, data, innovation (tide), **cells (new)**, validation-sim (corrected, with chance baselines),
validation-real (four events), hyperspectral, product, carbon, business (rewritten), roadmap, team.

## Images
Slides point to two kinds of image source:
- `/_blob/<id>`: assets already uploaded to the old artifact;
- `images/<file>`: local files that must be uploaded when the deck is published, with the `src` replaced by the new asset URL.

| src in slides | slide | local file |
|---|---|---|
| /_blob/5288132c... | validation-real | images/stand5_before_after_2021_2026.png |
| /_blob/cdb6f513... | validation-real | images/stand9_before_after_2020_2026.png |
| /_blob/4f7aa84e... | hyperspectral | images/enmap_stand5_two_epochs.png |
| /_blob/1d8e15d4... | data | images/dash_map_only.png |
| images/dash_stand9_cells_chart.png | cells | same (dashboard stand-9 panel: cell map + two alert-score lines) |
| images/stand12_key_years.png | validation-real | same |
| images/stand18_key_years.png | validation-real | same |
| images/dash_top_cells.png | product | same (dashboard top, map in 200 m cell view) |

## Layout check
`deck_preview.py` (in the session scratchpad; it can be recreated) renders every slide at 1920 x 1080 with the same fonts and checks that the lowest in-flow content
stays above 920 px (the 160 px bottom padding). The v3 result was 0 overflows. Before v3, the data and solution slides overflowed. This preview approximates
the Slides runtime; after publishing, check the deck once in the real viewer.
