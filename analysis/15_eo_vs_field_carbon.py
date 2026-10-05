"""Does a Sentinel-2 index track FIELD tree carbon? Plots (Schile 2016, sampled 2013) vs Sentinel-2 medians of 2020-21 low-cloud scenes (mature natural stands assumed stable; 7-8 yr gap).
For every natural-mangrove plot with coordinates: 3x3-pixel median NDVI/NDMI/NDRE over up to 8 clear scenes; then Spearman correlation at plot level and at SITE level (n=sites).
"""
import time, numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.warp import transform as wt
from scipy.stats import spearmanr
t0 = time.time()
pl = pd.read_csv("analysis/data/carbon_plots.csv").dropna(subset=["lat", "lon"])
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)


def px_stats(item, lon, lat):
    off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4.0")) >= 4 else 0.0
    out = {}
    try:
        for b in ("B03", "B04", "B05", "B08", "B8A", "B11", "SCL"):
            with rasterio.open(item.assets[b].href) as ds:
                x, y = wt("EPSG:4326", ds.crs, [lon], [lat]); r, c = ds.index(x[0], y[0])
                res = ds.res[0]; n = 1 if res >= 20 else 1
                a = ds.read(1, window=((r - 1, r + 2), (c - 1, c + 2)), boundless=True, fill_value=0).astype("float32")
                out[b] = a if b == "SCL" else np.clip((a - off) / 10000, 0, None)
        ok = ~np.isin(out["SCL"], [0, 1, 3, 8, 9, 10, 11])
        if ok.sum() < 2: return None
        f = lambda a, b_: np.nanmedian(((a - b_) / (a + b_ + 1e-6))[ok])
        return f(out["B08"], out["B04"]), f(out["B8A"], out["B11"]), f(out["B8A"], out["B05"]), f(out["B03"], out["B11"])
    except Exception:
        return None


rows = []
for site, g in pl.groupby("Site"):
    bb = [g.lon.min() - .002, g.lat.min() - .002, g.lon.max() + .002, g.lat.max() + .002]
    items = list(cat.search(collections=["sentinel-2-l2a"], bbox=bb, datetime="2020-01-01/2021-12-31", query={"eo:cloud_cover": {"lt": 10}}).items())
    items = sorted(items, key=lambda i: i.properties["eo:cloud_cover"])[:8]
    print(site, len(items), "scenes", f"{time.time() - t0:.0f}s", flush=True)
    for r in g.itertuples():
        v = [px_stats(i, r.lon, r.lat) for i in items]; v = np.array([x for x in v if x is not None])
        if len(v) >= 3: rows.append(dict(Site=site, Plot=r.Plot, tree_c=r.tree_c, soil_oc=r.soil_oc, total_c=r.total_c, ndvi=np.median(v[:, 0]), ndmi=np.median(v[:, 1]), ndre=np.median(v[:, 2]), mndwi=np.median(v[:, 3])))
d = pd.DataFrame(rows); d.to_csv("analysis/data/eo_vs_field.csv", index=False); print("plots with EO values:", len(d), "| sites:", d.Site.nunique())
print("\nPLOT-LEVEL Spearman rho (p):")
for tgt in ("tree_c", "total_c"):
    print(" ", tgt, {ix: f"{spearmanr(d[ix], d[tgt])[0]:+.2f} (p={spearmanr(d[ix], d[tgt])[1]:.3f})" for ix in ("ndvi", "ndmi", "ndre")})
s = d.groupby("Site")[["tree_c", "total_c", "ndvi", "ndmi", "ndre"]].mean(); print(f"\nSITE-LEVEL (n={len(s)}) Spearman rho (p):")
for tgt in ("tree_c", "total_c"):
    print(" ", tgt, {ix: f"{spearmanr(s[ix], s[tgt])[0]:+.2f} (p={spearmanr(s[ix], s[tgt])[1]:.3f})" for ix in ("ndvi", "ndmi", "ndre")})
