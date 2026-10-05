# Delivery concept: API and email alert (mock, not deployed)

Status: **concept with real PoC numbers**. The PoC ships a static dashboard and auto-generated reports. The API below is the
incubation-phase delivery model (gIQ deployment is not available to us during the PoC). Payload values are from our own
`analysis/data/stand_status.csv`; nothing here is a live service.

## Who uses it and what they do today

| User | Decision | Today, without us |
|---|---|---|
| Environment agency inspector | Which stands to visit first this month | Periodic visits or one-off studies; no continuous, stand-level screening |
| Mangrove / carbon-project developer | Is the stock we report still there | Manual survey, expensive and infrequent |
| EIA consultant / coastal regulator | Did a development stay outside the mangrove boundary | Compare two dated images by eye |

## Endpoints (proposed)

| Method | Path | Returns |
|---|---|---|
| GET | `/v1/stands` | List of stands: id, area, condition, alert flag, last observation |
| GET | `/v1/stands/{id}` | Status, indices vs baseline, carbon stock with range, alert episodes |
| GET | `/v1/stands/{id}/series` | Tide-corrected index time series and alert score |
| GET | `/v1/stands/{id}/report?lang=en|ar` | The templated site report (HTML/PDF) |
| POST | `/v1/subscriptions` | Register an email or webhook for alerts on chosen stands |

## Example: `GET /v1/stands/5` (real PoC values)

```json
{
  "stand": 5,
  "area_ha": 176.5,
  "condition": "severe decline",
  "alert_now": false,
  "alert_episodes_2022_2026": 5,
  "last_observation": "2026-09-17",
  "indices": {
    "ndvi": {"baseline_2020_21": 0.274, "now_last_12_months": -0.03, "change_pct": -111.0},
    "ndmi": {"baseline_2020_21": 0.382, "now_last_12_months": -0.015, "change_pct": -104.0}
  },
  "carbon_stock_t_c": {"p10": 13897, "median": 19131, "p90": 24441,
    "basis": "area x field density (Schile et al. 2016 plots near the region); an upper bound for this stand because its outline includes area that is now developed"},
  "evidence": ["Sentinel-2 epoch-difference flag: 26 ha", "EnMAP two-epoch pixel count: 62 ha"],
  "screening_note": "Screening indicator, not ground truth. Verify on site or with very-high-resolution imagery.",
  "attribution": "Contains modified Copernicus Sentinel data; contains modified EnMAP data (c) DLR"
}
```

Note that `alert_now` is false while `condition` is "severe decline": the alert reacts to recent change, the condition compares
with the 2020-21 baseline. Both layers are exposed on purpose.

## Example alert email (mock)

> **Subject:** [Blue Carbon Guardian] Stand 9: new decline signal (screening)
>
> The tide-corrected moisture index of stand 9 (77 ha) has stayed below its expected range for 5 consecutive Sentinel-2
> observations (composite z = [value]; calibrated to at most one alert episode per stand-year). [Template text; the bracketed
> value is filled from the alert table at send time, none is shown here because this is a mock.]
> Carbon stock at stake (upper bound): see report. Suggested action: check very-high-resolution imagery, then inspect on site.
> This is a screening indicator, not a measurement.

## Alert rule (as implemented)

Composite z-score of tide-corrected NDVI/NDMI vs the stand's own seasonal model; alert when the median of the last 5 scores is
at or below the threshold (about -1.3 to -1.4 sigma), calibrated on the real series to at most one episode per stand-year.
Tested on simulated cover loss (detection = a new alert episode after the loss begins, compared with a no-loss null): the stand-level rule above catches a whole-stand
10 % loss within 6 months in about 65 % of cases (40 % by chance). The recommended production rule adds the 200 m cells ("stand average at 1.5 sigma OR any cell
at 3.5 sigma", about 1 false alarm per stand-year): a partial loss (a tenth of a stand losing half its canopy) is caught within 60 days in about 73 % of cases
(13 % by chance). See `analysis/29_cell_trigger.md`. (Replaces an earlier 58 % / 90 % figure that counted alerts already running.)

## Roadmap to deploy

1. Nightly job on cloud compute pulls new Sentinel-2 scenes (open STAC), updates series and status tables.
2. Thin read-only API over the status tables (any web framework); dashboard reads the same API.
3. Email/webhook alerts on new episodes; report generator unchanged.
4. Incubation: deploy on gIQ, add very-high-resolution confirmation and sub-stand detection.
