"""Re-test of the stand-level backtest (analysis/07) with a NULL scenario and onset-based detection.

Problem found on 2026-09-27 (analysis/29): analysis/07 counted a trial as 'detected' if the alert state was on at ANY date after the injected loss began.
An alert episode already running at the start (episodes last weeks to months), or a real change in the same stand, then counts as a detection, and 07 had no
no-loss scenario to show how often that happens by chance.
Here, on the same stand series (config B, thresholds of analysis/08: NDVI 1.3, NDRE 1.4, NDMI 1.4, composite 1.3 sigma):
  - detection = a NEW alert episode (no alert in the previous 30 days) starting within [t0, t0 + 180 d]
  - scenarios: NO loss (null = detection by chance), and whole-stand canopy-cover loss 5 / 10 / 20 % (linear mixing, 60-day ramp, bare NDVI .05 / NDRE .03 / NDMI 0)
  - stands with changes seen on imagery (5, 6, 9, 12, 18) are excluded from the trials
  - the old metric of 07 is also reported on the same trials, to show the size of the bias
Outputs: analysis/data/backtest_null_trials.csv, analysis/30_backtest_null.md
"""
import numpy as np, pandas as pd, time, json

src = open("analysis/23_scaleout_monitor.py", encoding="utf-8").read().split("# ---- step 0")[0]; ns = {}; exec(src, ns)
monitor, roll, IDX, T0 = ns["monitor"], ns["roll"], ns["IDX"], ns["T0"]
THR = {"ndvi": 1.3, "ndre": 1.4, "ndmi": 1.4, "comp": 1.3}; BARE = {"ndvi": 0.05, "ndre": 0.03, "ndmi": 0.00}
FRACS, N_INJ, RAMP_D, HORIZON_D, EXCLUDE = [0.0, 0.05, 0.10, 0.20], 12, 60, 180, {5, 6, 9, 12, 18}
rng = np.random.default_rng(7); t_start = time.time()

df = pd.read_csv("analysis/data/s2_stands_stats.csv"); df["date"] = pd.to_datetime(df["date"])
df = df.dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); df = df[df.valid_frac >= 0.5].sort_values(["stand", "date"])
S = {k: dict(t=(g.date - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values, y={i: g[f"{i}_p50"].values for i in IDX})
     for k, g in df.groupby("stand") if k not in EXCLUDE}


def first_onset(t, on, t0):
    j = np.nonzero(on)[0]; ons = [a for n, a in enumerate(j) if n == 0 or t[a] - t[j[n - 1]] > 30]
    ons = [a for a in ons if t0 <= t[a] <= t0 + HORIZON_D]; return (t[ons[0]] - t0) if ons else np.nan


def first_state(t, on, t0):                                   # the metric of analysis/07
    j = np.nonzero(on & (t >= t0) & (t <= t0 + HORIZON_D))[0]; return (t[j[0]] - t0) if len(j) else np.nan


trials = []
for k, s in S.items():
    t_min, t_max = (pd.Timestamp("2022-07-01") - T0).days, s["t"].max() - HORIZON_D
    for t0 in np.sort(rng.uniform(t_min, t_max, N_INJ)):
        d_from = str((T0 + pd.Timedelta(days=t0 - 100)).date()); d_to = str((T0 + pd.Timedelta(days=t0 + HORIZON_D)).date())
        for f in FRACS:
            ramp = np.clip((s["t"] - t0) / RAMP_D, 0, 1)
            zs = {i: monitor(s, s["y"][i] * (1 - f * ramp) + f * ramp * BARE[i], d_from, d_to) for i in IDX}; t = zs["ndvi"][0]
            if len(t) < 8: continue
            st = {**{i: roll(zs[i][1]) for i in IDX}, "comp": roll(np.mean([zs[i][1] for i in IDX], axis=0))}
            for name, z in st.items():
                on = np.nan_to_num(z, nan=0.0) <= -THR[name]
                trials.append(dict(stand=k, t0=t0, frac=f, detector=name, onset_delay=first_onset(t, on, t0), state_delay=first_state(t, on, t0)))
    print(f"  stand {k} ({time.time() - t_start:.0f}s)", flush=True)
tr = pd.DataFrame(trials); tr.to_csv("analysis/data/backtest_null_trials.csv", index=False)
agg = tr.groupby(["frac", "detector"]).agg(n=("stand", "size"),
    new_60=("onset_delay", lambda d: 100 * (d <= 60).mean()), new_180=("onset_delay", lambda d: 100 * d.notna().mean()),
    old_60=("state_delay", lambda d: 100 * (d <= 60).mean()), old_180=("state_delay", lambda d: 100 * d.notna().mean())).round(1)
null = agg.xs(0.0, level="frac")
agg["lift_60"] = [round(r.new_60 - null.loc[d, "new_60"], 1) for (f, d), r in agg.iterrows()]
agg["lift_180"] = [round(r.new_180 - null.loc[d, "new_180"], 1) for (f, d), r in agg.iterrows()]
pd.set_option("display.width", 200); print(agg.to_string())
with open("analysis/30_backtest_null.md", "w", encoding="utf-8") as fh:
    fh.write("# Stand-level backtest re-tested with a null scenario (analysis/30)\n\n" + __doc__ + "\n\n"
             "new_* = onset-based detection (% of trials, within 60 / 180 days); old_* = the metric of analysis/07; lift = new minus the null rate of the same detector.\n\n"
             + agg.to_markdown() + "\n")
print(f"done in {time.time() - t_start:.0f}s")
