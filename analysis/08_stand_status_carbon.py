"""Product data: per-stand status, alert episodes, long-term trend, carbon stock / exposure, stand polygons (GeoJSON) and dashboard series.

Uses the approved configuration B of analysis/07 (tide terms = MNDWI, MNDWI^2, flooded fraction; rolling monthly refit; median-of-5 alert rule;
thresholds calibrated to <= 1 alert episode per stand-year: ndvi 1.3, ndre 1.4, ndmi 1.4, composite 1.3 sigma).
CARBON: placeholder density range from published values (UAE natural mangrove ~156 t C/ha; UAE lagoon mangrove 94.3 +/- 19.6 t C/ha, Schile et al. 2017 as
cited in Frontiers Mar. Sci. 2025 review) -> triangular(74.7, 94.3, 156.0). MUST be replaced/validated with the Dryad field dataset (doi 10.15146/R3K59Z).
'exposure' = ecosystem carbon stock inside flagged stands (NOT a loss estimate).
Outputs -> analysis/data/: stand_status.csv, stand_alert_episodes.csv, stands.geojson, dashboard_data.json
"""
import json, numpy as np, pandas as pd, rasterio, pystac_client, planetary_computer as pc
from rasterio.features import shapes
from rasterio.merge import merge
from scipy import ndimage as ndi
from shapely.geometry import shape as shp, mapping

IDX = ["ndvi", "ndre", "ndmi"]; THR = {"ndvi": 1.3, "ndre": 1.4, "ndmi": 1.4, "comp": 1.3}
K_MED, TRAIN_MONTHS, GUARD_D = 5, 36, 90
T0 = pd.Timestamp("2020-01-01"); CO2E = 44 / 12
DENSITY = (74.7, 94.3, 156.0)                                   # t C / ha  (low, mode, high)  PLACEHOLDER, see docstring
rng = np.random.default_rng(11)

df = pd.read_csv("analysis/data/s2_stands_stats.csv"); df["date"] = pd.to_datetime(df["date"])
df = df.dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); df = df[df.valid_frac >= 0.5].sort_values(["stand", "date"])
stands = pd.read_csv("analysis/data/stands.csv").set_index("stand")
S = {k: dict(t=(g.date - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values, y={i: g[f"{i}_p50"].values for i in IDX}) for k, g in df.groupby("stand")}


def design(t, w=None, ff=None):
    a = 2 * np.pi * t / 365.25
    cols = [np.ones_like(t), t / 365.25, np.sin(a), np.cos(a), np.sin(2 * a), np.cos(2 * a)]
    if w is not None: cols += [w, w ** 2, ff]
    return np.column_stack(cols)


def rfit(X, y, iters=10):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(iters):
        r = y - X @ beta; s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9
        u = np.abs(r) / (1.345 * s); wt = np.sqrt(np.where(u <= 1, 1.0, 1.0 / u))
        beta = np.linalg.lstsq(X * wt[:, None], y * wt, rcond=None)[0]
    r = y - X @ beta
    return beta, 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9


def monitor(s, y, d_from="2022-01-01", d_to="2026-12-31"):
    t, w = s["t"], s["w"]; ot, oz = [], []
    tf, tt = (pd.Timestamp(d_from) - T0).days, (pd.Timestamp(d_to) - T0).days
    for m in pd.period_range(pd.Timestamp(d_from).to_period("M"), pd.Timestamp(d_to).to_period("M"), freq="M"):
        ms = (m.start_time - T0).days; me = (m.end_time - T0).days
        tr = (t >= ms - TRAIN_MONTHS * 30.44) & (t <= ms - GUARD_D); te = (t >= max(ms, tf)) & (t <= min(me, tt))
        if tr.sum() < 80 or not te.any(): continue
        beta, sig = rfit(design(t[tr], w[tr], s["ff"][tr]), y[tr])
        ot.append(t[te]); oz.append((y[te] - design(t[te], w[te], s["ff"][te]) @ beta) / sig)
    return np.concatenate(ot), np.concatenate(oz)


def roll(z): return pd.Series(z).rolling(K_MED, min_periods=K_MED).median().values


status, episodes, dash = [], [], {}
for k, s in S.items():
    zs = {i: monitor(s, s["y"][i]) for i in IDX}; t = zs["ndvi"][0]
    z = {**{i: zs[i][1] for i in IDX}, "comp": np.mean([zs[i][1] for i in IDX], axis=0)}
    st = {n: roll(v) for n, v in z.items()}
    on = st["comp"] <= -THR["comp"]
    # episodes of the composite alert (new episode if gap > 30 d)
    j = np.nonzero(on)[0]; groups = []
    for a in j:
        if groups and t[a] - t[groups[-1][-1]] <= 30: groups[-1].append(a)
        else: groups.append([a])
    for gi in groups:
        episodes.append(dict(stand=k, start=(T0 + pd.Timedelta(days=t[gi[0]])).date(), end=(T0 + pd.Timedelta(days=t[gi[-1]])).date(),
                             days=int(t[gi[-1]] - t[gi[0]]), min_z_comp=round(float(np.nanmin(st["comp"][gi])), 2), min_z_ndmi=round(float(np.nanmin(st["ndmi"][gi])), 2)))
    last = len(t) - 1
    # long-term trend from the full-sample fit (tide-aware): index units per year and % of mean per year
    tr_row = {}
    for i in IDX:
        beta, sig = rfit(design(s["t"], s["w"], s["ff"]), s["y"][i]); tr_row[f"trend_{i}_per_yr"] = round(float(beta[1]), 4)
        tr_row[f"trend_{i}_pct_per_yr"] = round(100 * float(beta[1]) / float(np.median(s["y"][i])), 2)
    days_since_last_obs = int((pd.Timestamp("2026-09-19") - (T0 + pd.Timedelta(days=t[last]))).days)
    status.append(dict(stand=k, area_ha=stands.loc[k, "area_ha"], last_obs=(T0 + pd.Timedelta(days=t[last])).date(), obs_gap_days=days_since_last_obs,
                       z_comp_now=round(float(st["comp"][last]), 2), z_ndmi_now=round(float(st["ndmi"][last]), 2), z_ndvi_now=round(float(st["ndvi"][last]), 2),
                       alert_now=bool(on[last]), alerts_2022_2026=len(groups), **tr_row))
    # monthly series for the dashboard: tide-corrected index (y minus tide terms) and composite z (monthly median)
    ser = pd.DataFrame({"date": T0 + pd.to_timedelta(s["t"], unit="D")})
    for i in IDX:
        beta, _ = rfit(design(s["t"], s["w"], s["ff"]), s["y"][i]); Xt = design(s["t"], s["w"], s["ff"])
        tide = Xt[:, 6:] @ beta[6:]; ser[i] = s["y"][i] - tide + float(np.mean(tide))          # tide-corrected series
    m = ser.set_index("date").resample("MS").median().dropna(how="all")
    zc = pd.Series(st["comp"], index=T0 + pd.to_timedelta(t, unit="D")).resample("MS").median()
    dash[int(k)] = dict(months=[d.strftime("%Y-%m") for d in m.index], ndmi=[None if np.isnan(v) else round(float(v), 4) for v in m["ndmi"]],
                        ndvi=[None if np.isnan(v) else round(float(v), 4) for v in m["ndvi"]],
                        z=[None if (d not in zc.index or np.isnan(zc[d])) else round(float(zc[d]), 2) for d in m.index])
stat = pd.DataFrame(status)

# ---- carbon: Monte Carlo per stand (area x density) --------------------------------------------------------------------
dens = rng.triangular(*DENSITY, size=20000)
q = lambda a: np.percentile(a, [10, 50, 90])
rows = []
for r in stat.itertuples():
    c = r.area_ha * dens; lo, md, hi = q(c)
    rows.append(dict(stock_tC_p10=round(lo), stock_tC_p50=round(md), stock_tC_p90=round(hi), stock_tCO2e_p50=round(md * CO2E)))
stat = pd.concat([stat, pd.DataFrame(rows)], axis=1)
flag = stat.alert_now
print(f"stands: {len(stat)} | area {stat.area_ha.sum():.0f} ha | carbon stock p10/p50/p90 = "
      f"{stat.stock_tC_p10.sum() / 1000:.0f} / {stat.stock_tC_p50.sum() / 1000:.0f} / {stat.stock_tC_p90.sum() / 1000:.0f} kt C "
      f"(sum of per-stand p10/p50/p90, indicative)")
print(f"currently flagged stands: {int(flag.sum())} | exposure (p50): {stat.loc[flag, 'stock_tC_p50'].sum() / 1000:.1f} kt C = {stat.loc[flag, 'stock_tCO2e_p50'].sum() / 1000:.1f} kt CO2e")
print(f"episodes 2022-2026: {len(episodes)} total, {len(episodes) / (len(S) * 4.7):.2f} per stand-year")
print("trend NDMI %/yr median:", stat.trend_ndmi_pct_per_yr.median(), "| share of stands with rising NDVI trend:", round((stat.trend_ndvi_per_yr > 0).mean() * 100), "%")
stat.to_csv("analysis/data/stand_status.csv", index=False); pd.DataFrame(episodes).to_csv("analysis/data/stand_alert_episodes.csv", index=False)

# ---- polygons -------------------------------------------------------------------------------------------------------------
BOX = [54.30, 24.35, 54.70, 24.65]; BLOCK = (0.12, 0.09)
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=BOX, datetime="2021-01-01/2021-12-31").items())
arr, tr_ = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=BOX)
mang_all = arr[0] == 95; best, bn = None, -1
for lon in np.arange(BOX[0], BOX[2] - BLOCK[0] + 1e-9, 0.03):
    for lat in np.arange(BOX[1], BOX[3] - BLOCK[1] + 1e-9, 0.03):
        r0, c0 = rasterio.transform.rowcol(tr_, lon, lat + BLOCK[1]); r1, c1 = rasterio.transform.rowcol(tr_, lon + BLOCK[0], lat)
        n = int(mang_all[max(r0, 0):r1, max(c0, 0):c1].sum())
        if n > bn: best, bn = [float(lon), float(lat), float(lon + BLOCK[0]), float(lat + BLOCK[1])], n
wc_arr, wc_tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=best)
lab, n = ndi.label(wc_arr[0] == 95); area = np.bincount(lab.ravel())[1:] * 0.01
keep = [i + 1 for i in np.argsort(-area) if area[i] >= 3.0][:25]
sl = np.zeros_like(lab, dtype="uint16")
for kk, l in enumerate(keep, start=1): sl[lab == l] = kk
feats = []
for geom, val in shapes(sl, mask=sl > 0, transform=wc_tr, connectivity=4):
    kk = int(val)
    if kk in set(stat.stand):
        g = shp(geom).simplify(0.00004)
        r = stat[stat.stand == kk].iloc[0]
        feats.append(dict(type="Feature", geometry=mapping(g), properties=dict(stand=kk, area_ha=float(r.area_ha), alert=bool(r.alert_now), z=float(r.z_comp_now))))
json.dump(dict(type="FeatureCollection", features=feats), open("analysis/data/stands.geojson", "w"))
json.dump(dict(series=dash, region=best), open("analysis/data/dashboard_data.json", "w"))
print("polygons:", len(feats), "| region", np.round(best, 3))
print(stat[["stand", "area_ha", "z_comp_now", "alert_now", "alerts_2022_2026", "trend_ndvi_pct_per_yr", "trend_ndmi_pct_per_yr", "stock_tC_p50"]].head(12).to_string(index=False))
