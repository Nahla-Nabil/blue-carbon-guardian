"""Core of the Blue Carbon Guardian monitor. The same logic as analysis/23 and analysis/29-31, packaged for the notebook.

Model (per stand or per 200 m cell, per index NDVI / NDRE / NDMI):
    index(t) = a + b*t + seasonal harmonics (1 and 2 cycles per year) + tide terms (MNDWI, MNDWI^2, flooded fraction) + noise
fitted with a robust (Huber) regression. The tide terms matter: in Gulf mangroves, tide and wetness drive most of the date-to-date noise.

Two outputs:
  ALERT     : every month the model is refitted on [t - 36 months, t - 3 months]; z = (observed - predicted) / robust sigma; the composite
              z = mean over the three indices; the alert state = median of the last 5 composite z.
              Product rule (calibrated in analysis/29 to about 1 false-alarm episode per stand-year on the 25 pilot stands):
              ALERT if stand state <= -1.5 OR any cell state <= -3.5.
  CONDITION : tide-corrected index, median of the last 12 months vs the 2020-21 median (NDVI and NDMI):
              severe decline (both <= -50 %), decline (both <= -15 % and <= -3 sigma), improving (mirror), else stable.
"""
import numpy as np
import pandas as pd

IDX = ["ndvi", "ndre", "ndmi"]
T0 = pd.Timestamp("2020-01-01")
K_MED, TRAIN_MONTHS, GUARD_D, NOW_DAYS, CARRY_D = 5, 36, 90, 365, 20
STAND_THR, CELL_THR = 1.5, 3.5                     # product alert thresholds (sigma), calibrated in analysis/29_cell_trigger.py
CARBON_T_C_PER_HA = (78.7, 108.4, 138.5)           # field density, 90 % CI of the mean (Schile et al. 2016, 24 plots near the stands; analysis/13)
CO2E = 44 / 12


def design(t, w=None, ff=None):
    """Design matrix: intercept, trend (per year), 2 seasonal harmonics, optional tide terms."""
    a = 2 * np.pi * t / 365.25
    cols = [np.ones_like(t), t / 365.25, np.sin(a), np.cos(a), np.sin(2 * a), np.cos(2 * a)]
    if w is not None:
        cols += [w, w ** 2, ff]
    return np.column_stack(cols)


def rfit(X, y, iters=10):
    """Huber-weighted least squares (iteratively reweighted). Returns coefficients and the robust residual sigma (scaled MAD)."""
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(iters):
        r = y - X @ beta; s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9
        u = np.abs(r) / (1.345 * s); wt = np.sqrt(np.where(u <= 1, 1.0, 1.0 / u))
        beta = np.linalg.lstsq(X * wt[:, None], y * wt, rcond=None)[0]
    r = y - X @ beta
    return beta, 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9


def to_series(g):
    """One stand's or cell's rows (columns date, valid_frac, *_p50, mndwi_p50, flooded_frac) -> arrays used by the model."""
    g = g.dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"])
    g = g[g.valid_frac >= 0.5].sort_values("date")
    out = dict(t=(pd.to_datetime(g.date) - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values,
               y={i: g[f"{i}_p50"].values for i in IDX})
    if "n_valid" in g: out["n"] = g.n_valid.values
    return out


def noise_with_without_tide(s, index):
    """Robust residual sigma of the full-period model without and with the tide terms."""
    _, s0 = rfit(design(s["t"]), s["y"][index]); _, s1 = rfit(design(s["t"], s["w"], s["ff"]), s["y"][index])
    return s0, s1


def monitor(s, y, d_from="2022-01-01", d_to="2026-12-31"):
    """Monthly rolling refit; returns (t, z) for the observations between d_from and d_to."""
    t, w = s["t"], s["w"]; ot, oz = [], []
    tf, tt = (pd.Timestamp(d_from) - T0).days, (pd.Timestamp(d_to) - T0).days
    for m in pd.period_range(pd.Timestamp(d_from).to_period("M"), pd.Timestamp(d_to).to_period("M"), freq="M"):
        ms = (m.start_time - T0).days; me = (m.end_time - T0).days
        tr = (t >= ms - TRAIN_MONTHS * 30.44) & (t <= ms - GUARD_D); te = (t >= max(ms, tf)) & (t <= min(me, tt))
        if tr.sum() < 80 or not te.any():
            continue
        beta, sig = rfit(design(t[tr], w[tr], s["ff"][tr]), y[tr])
        ot.append(t[te]); oz.append((y[te] - design(t[te], w[te], s["ff"][te]) @ beta) / sig)
    return (np.concatenate(ot), np.concatenate(oz)) if ot else (np.array([]), np.array([]))


def alert_state(s):
    """(t, median-of-5 composite z) for 2022-2026."""
    zs = {i: monitor(s, s["y"][i]) for i in IDX}; t = zs["ndvi"][0]
    if len(t) == 0:
        return t, t
    return t, pd.Series(np.mean([zs[i][1] for i in IDX], axis=0)).rolling(K_MED, min_periods=K_MED).median().values


def condition(s, now_days=NOW_DAYS):
    """Condition class and its numbers (tide-corrected index, last 12 months vs 2020-21)."""
    out, raw = {}, {}
    for i in ("ndvi", "ndmi"):
        X = design(s["t"], s["w"], s["ff"]); beta, sig = rfit(X, s["y"][i])
        tide = X[:, 6:] @ beta[6:]; ser = s["y"][i] - tide + float(np.mean(tide))
        base = float(np.median(ser[s["t"] < 731])); now = float(np.median(ser[s["t"] >= s["t"][-1] - now_days]))
        raw[i] = (100 * (now - base) / abs(base), (now - base) / sig)
        out.update({f"{i}_base": round(base, 3), f"{i}_now": round(now, 3), f"{i}_change_pct": round(raw[i][0], 1)})
    if all(raw[i][0] <= -50 for i in raw): c = "severe decline"
    elif all(raw[i][0] <= -15 and raw[i][1] <= -3 for i in raw): c = "decline"
    elif all(raw[i][0] >= 15 and raw[i][1] >= 3 for i in raw): c = "improving"
    else: c = "stable"
    out["condition"] = c
    return out


def stand_proxy(cell_series, total_px):
    """Pixel-weighted mean of a stand's cell medians per date (the 'stand average' part of the product alert)."""
    d = pd.concat([pd.DataFrame(dict(t=s["t"], n=s["n"], w=s["w"], ff=s["ff"], **s["y"])) for s in cell_series])
    wsum = d.groupby("t").n.sum(); m = d[["w", "ff"] + IDX].mul(d.n, axis=0).groupby(d.t).sum().div(wsum, axis=0)
    m = m[wsum.reindex(m.index) >= 0.5 * total_px]
    return dict(t=m.index.values.astype(float), w=m.w.values, ff=m.ff.values, y={i: m[i].values for i in IDX})


def episodes(t, on, gap_days=30):
    """Group alerting dates into episodes (a new episode after more than gap_days without alert). Returns a list of (start, end) dates."""
    out = []
    for j in np.nonzero(on)[0]:
        if out and t[j] - out[-1][1] <= gap_days: out[-1][1] = t[j]
        else: out.append([t[j], t[j]])
    return [((T0 + pd.Timedelta(days=float(a))).date(), (T0 + pd.Timedelta(days=float(b))).date()) for a, b in out]


def product_alert(stand_state, cell_states):
    """Combined rule on a common date axis: stand state <= -STAND_THR OR any cell state <= -CELL_THR (states carried forward up to 20 days)."""
    ts, zs = stand_state
    grid = np.unique(np.concatenate([ts] + [t for t, _ in cell_states if len(t)]))

    def carry(t, z):
        v = np.full(len(grid), np.nan)
        if len(t):
            j = np.searchsorted(t, grid, side="right") - 1; ok = (j >= 0) & (grid - t[np.clip(j, 0, None)] <= CARRY_D); v[ok] = z[j[ok]]
        return v
    stand_on = np.nan_to_num(carry(ts, zs), nan=0.0) <= -STAND_THR
    cells_on = np.array([np.nan_to_num(carry(t, z), nan=0.0) <= -CELL_THR for t, z in cell_states]).any(0)
    return grid, stand_on | cells_on, stand_on, cells_on
