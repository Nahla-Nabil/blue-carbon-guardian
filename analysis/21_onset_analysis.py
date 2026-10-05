"""Onset dating, step 2: when did the conversion inside stands 5 and 9 start, and how long after that did our stand-level alert fire?

Input : analysis/data/onset_series.csv (analysis/20), analysis/data/stand_alert_episodes.csv (analysis/07/08)
Method: paired difference d(t) = index(loss pixels) - index(control pixels of the same stand); tide/season/sensor effects shared by both cancel.
        Fit a constant - linear ramp - constant model (levels a -> b, ramp from t1 to t2, monthly grid) by least squares.
        t1 = start of change ("onset"), t2 = end of the ramp. 90 % interval for t1 from a residual bootstrap (300 draws; approximate: residuals
        are not perfectly homoscedastic).
        Also a threshold onset: first date from which the rolling median of 5 stays below (2020 baseline mean - 3 robust sd) for >= 10 consecutive observations.
Report: detection delay = first stand-level alert episode that starts within [t1 - 90 d, t2] minus t1. Negative = alert before the fitted onset.
CAUTION: loss pixels were selected using 2021 vs 2025 imagery, so this dates an already-known change; it is not an unbiased detection test.
Outputs: analysis/data/onset_results.csv, analysis/21_onset.png
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
S = pd.read_csv("analysis/data/onset_series.csv"); S["date"] = pd.to_datetime(S["date"])
EP = pd.read_csv("analysis/data/stand_alert_episodes.csv", parse_dates=["start", "end"])
BASE_END = pd.Timestamp("2020-12-31")


def paired(stand, idx):
    p = S[(S.stand == stand)].pivot_table(index="date", columns="part", values=idx).dropna()
    return (p["loss"] - p["control"]).sort_index()


def ramp_fit(t, y, grid, boot=0):
    """Constant-ramp-constant least squares; returns (t1, t2, a, b, sse) and optional bootstrap t1 draws."""
    def best(yv):
        bestv = (np.inf,)
        for i, t1 in enumerate(grid):
            for t2 in grid[i + 1:]:
                r = np.clip((t - t1) / (t2 - t1), 0, 1)
                B = np.stack([1 - r, r], 1)
                coef, res, *_ = np.linalg.lstsq(B, yv, rcond=None)
                sse = float(((B @ coef - yv) ** 2).sum())
                if sse < bestv[0]:
                    bestv = (sse, t1, t2, coef[0], coef[1])
        return bestv
    sse, t1, t2, a, b = best(y)
    draws = []
    if boot:
        r = np.clip((t - t1) / (t2 - t1), 0, 1); fit = a * (1 - r) + b * r; res = y - fit
        for _ in range(boot):
            draws.append(best(fit + rng.choice(res, len(res)))[1])
    return t1, t2, a, b, sse, np.array(draws)


def threshold_onset(d):
    base = d[d.index <= BASE_END]; mu = base.mean(); sd = 1.4826 * np.median(np.abs(base - base.median()))
    thr = mu - 3 * sd; roll = d.rolling(5).median(); below = (roll <= thr).astype(int).values
    for i in range(len(below) - 9):
        if below[i:i + 10].all():
            return d.index[i], thr
    return pd.NaT, thr


rows, fig = [], plt.figure(figsize=(15, 8))
for col, stand in enumerate((5, 9)):
    for row, idx in enumerate(("ndvi", "ndmi")):
        d = paired(stand, idx); t = ((d.index - pd.Timestamp("2020-01-01")).days).values.astype(float)
        grid = np.arange(0, t.max() - 60, 30.0)
        t1, t2, a, b, sse, draws = ramp_fit(t, d.values, grid, boot=300)
        lo, hi = np.percentile(draws, [5, 95])
        day = lambda x: pd.Timestamp("2020-01-01") + pd.Timedelta(days=float(x))
        thr_date, thr = threshold_onset(d)
        eps = EP[EP.stand == stand].sort_values("start")
        cand = eps[(eps.start >= day(t1) - pd.Timedelta(days=90)) & (eps.start <= day(t2))]
        first_alert = cand.start.iloc[0] if len(cand) else pd.NaT
        rows.append(dict(stand=stand, index=idx, level_before=round(a, 3), level_after=round(b, 3), onset_t1=day(t1).date(), onset_90ci=f"{day(lo).date()} .. {day(hi).date()}",
                         ramp_end_t2=day(t2).date(), threshold_onset=(thr_date.date() if pd.notna(thr_date) else None),
                         first_alert_in_window=(first_alert.date() if pd.notna(first_alert) else None),
                         delay_days=(int((first_alert - day(t1)).days) if pd.notna(first_alert) else None),
                         all_alert_starts=";".join(str(x.date()) for x in eps.start)))
        ax = fig.add_subplot(2, 2, row * 2 + col + 1)
        ax.plot(d.index, d.values, ".", ms=3, color="#557"); r = np.clip((t - t1) / (t2 - t1), 0, 1); ax.plot(d.index, a * (1 - r) + b * r, "r-", lw=2)
        for _, e in eps.iterrows():
            ax.axvspan(e.start, max(e.end, e.start + pd.Timedelta(days=8)), color="purple", alpha=.2)
        ax.axvspan(day(lo), day(hi), color="orange", alpha=.25); ax.set_title(f"Stand {stand}: {idx.upper()} loss pixels - control (red = ramp fit, orange = 90 % CI of onset, purple = stand alert episodes)", fontsize=8)
plt.tight_layout(); plt.savefig("analysis/21_onset.png", dpi=90)
res = pd.DataFrame(rows); res.to_csv("analysis/data/onset_results.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20); print(res.to_string(index=False))
