"""Out-of-sample test of the product alert, step 2: the combined rule, thresholds FIXED from the pilot (stand average <= -1.5 sigma OR any 200 m cell
<= -3.5 sigma, analysis/29-31), applied without any re-tuning to the 66 scale-out stands (blocks ADN, ADW, TRT; cells from analysis/32).

Question: does the false-alarm budget (0.96 alert episodes per stand-year on the pilot, where it was calibrated) hold on stands the rule never saw?
Caveat: like the pilot calibration, real changes stay in the series, so the measured rate is an upper bound on the false-alarm rate.
Also runs the per-cell condition rule (analysis/23) to list cells in (severe) decline as candidate events for a visual check.
Outputs: analysis/data/scaleout_cells/<block>_cell_status.csv, oos_union_episodes.csv, oos_union_summary.json
"""
import glob, json, numpy as np, pandas as pd

src = open("analysis/23_scaleout_monitor.py", encoding="utf-8").read().split("# ---- step 0")[0]; ns = {}; exec(src, ns)
monitor, roll, analyse, IDX, T0 = ns["monitor"], ns["roll"], ns["analyse"], ns["IDX"], ns["T0"]
U = json.load(open("analysis/data/union_series.json")); TS, TC = U["stand_thr"], U["cell_thr"]
D = "analysis/data/scaleout_cells/"; CARRY_D = 20


def comp_state(s, d_from="2022-01-01", d_to="2026-12-31"):
    zs = {i: monitor(s, s["y"][i], d_from, d_to) for i in IDX}; t = zs["ndvi"][0]
    return (t, roll(np.mean([zs[i][1] for i in IDX], axis=0))) if len(t) else (t, t)


def n_episodes(t, on):
    n, last = 0, -1e9
    for j in np.nonzero(on)[0]:
        if t[j] - last > 30: n += 1
        last = t[j]
    return n


summary, all_eps, cond_rows = {}, [], []
for path in sorted(glob.glob(D + "*_cell_stats.csv")):
    B = path.replace("\\", "/").split("/")[-1].split("_")[0]
    meta = pd.read_csv(D + f"{B}_cells.csv").set_index("cell")
    S = pd.read_csv(path); S = S[S["error"].isna()] if "error" in S else S
    S = S[S.valid_frac >= 0.5].dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); S["date"] = pd.to_datetime(S["date"])
    S["stand"] = S.cell.map(meta.stand)
    tot_rate = dict(stand=0, cells=0, union=0); years = 0.0
    for stand, gs in S.groupby("stand"):
        # cell series, states and condition
        CELL = {}
        for c, g in gs.groupby("cell"):
            g = g.sort_values("date"); CELL[c] = dict(t=(g.date - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values,
                                                      n=g.n_valid.values, y={i: g[f"{i}_p50"].values for i in IDX})
            r, _ = analyse(int(c), g, float(meta.loc[c, "n_px"]) * 0.01)
            if r is not None: cond_rows.append(dict(block=B, stand=stand, cell=int(c), area_ha=r["area_ha"], condition=r["condition"],
                                                    ndvi_change_pct=r["ndvi_change_pct"], ndmi_change_pct=r["ndmi_change_pct"]))
        # stand proxy = pixel-weighted mean of its cells' medians (same as the pilot product rule)
        d = pd.concat([pd.DataFrame(dict(t=s["t"], n=s["n"], w=s["w"], ff=s["ff"], **s["y"])) for s in CELL.values()])
        wsum = d.groupby("t").n.sum(); m = d[["w", "ff"] + IDX].mul(d.n, axis=0).groupby(d.t).sum().div(wsum, axis=0)
        m = m[wsum.reindex(m.index) >= 0.5 * meta[meta.stand == stand].n_px.sum()]
        ts, zs = comp_state(dict(t=m.index.values.astype(float), w=m.w.values, ff=m.ff.values, y={i: m[i].values for i in IDX}))
        if len(ts) < 50: continue
        on_s = np.nan_to_num(zs, nan=0.0) <= -TS
        # cells on the stand's date axis (carry the last state forward up to 20 days)
        dates = np.unique(np.concatenate([ts] + [comp_state(s)[0] for s in []]))
        cstates = {c: comp_state(s) for c, s in CELL.items()}
        grid = np.unique(np.concatenate([ts] + [v[0] for v in cstates.values() if len(v[0])]))
        M = np.full((len(cstates), len(grid)), np.nan)
        for r_, (c, (t, z)) in enumerate(cstates.items()):
            if len(t) == 0: continue
            j = np.searchsorted(t, grid, side="right") - 1; ok = (j >= 0) & (grid - t[np.clip(j, 0, None)] <= CARRY_D); M[r_, ok] = z[j[ok]]
        on_c = (np.nan_to_num(M, nan=0.0) <= -TC).any(0)
        tu = np.concatenate([ts, grid]); onu = np.concatenate([on_s, on_c]); o = np.argsort(tu, kind="stable")
        yrs = (ts.max() - ts.min()) / 365.25; years += yrs
        tot_rate["stand"] += n_episodes(ts, on_s); tot_rate["cells"] += n_episodes(grid, on_c); tot_rate["union"] += n_episodes(tu[o], onu[o])
        tt, oo = tu[o], onu[o]; idx = np.nonzero(oo)[0]; groups = []
        for a in idx:
            if groups and tt[a] - tt[groups[-1][-1]] <= 30: groups[-1].append(a)
            else: groups.append([a])
        for g in groups:
            all_eps.append(dict(block=B, stand=stand, start=(T0 + pd.Timedelta(days=float(tt[g[0]]))).date(), end=(T0 + pd.Timedelta(days=float(tt[g[-1]]))).date()))
    summary[B] = dict(stands=int(S.stand.nunique()), cells=int(S.cell.nunique()), stand_years=round(years, 1),
                      union_per_stand_year=round(tot_rate["union"] / years, 2), stand_part_per_stand_year=round(tot_rate["stand"] / years, 2),
                      cell_part_per_stand_year=round(tot_rate["cells"] / years, 2))
    print(B, summary[B], flush=True)
C = pd.DataFrame(cond_rows)
for B, g in C.groupby("block"): g.to_csv(D + f"{B}_cell_status.csv", index=False)
pd.DataFrame(all_eps).to_csv(D + "oos_union_episodes.csv", index=False)
tot_years = sum(v["stand_years"] for v in summary.values())
summary["ALL"] = dict(stand_years=round(tot_years, 1), union_per_stand_year=round(len(all_eps) / tot_years, 2), pilot_calibrated=0.96, thresholds=f"stand {TS} / cell {TC}")
summary["flagged_cells"] = C[C.condition.isin(["decline", "severe decline"])].groupby(["block", "stand"]).agg(cells=("cell", "size"), ha=("area_ha", "sum")).round(1).reset_index().to_dict("records")
json.dump(summary, open(D + "oos_union_summary.json", "w"), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
