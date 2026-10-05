"""Build the reference-labeling sample for the team (online photo-interpretation, no fieldwork).

Design (standard stratified reference sampling):
  * strata come from ESA WorldCover 2021 inside the Abu Dhabi box:
      mangrove_core (100) | mangrove_edge (40) | near_nonmangrove within ~300 m, class-balanced (100) | far_background (60)
  * points are >= 150 m apart, and get a 1 km "block" id so we can split train/test SPATIALLY later
    (the organizers warn against random splits of neighbouring pixels).
  * BLIND labeling: the files given to teammates contain NO stratum / WorldCover class, only coordinates.
  * 300 unique points split evenly over 3 annotators + 20 shared points labeled by all three (agreement check).

Outputs (folder labeling/): points_master.csv (private), points_<name>.csv, points_<name>.kml, labels_template columns inside.
Requires: pystac-client, planetary-computer, rasterio, scipy, numpy, pandas
"""
import os, numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.merge import merge
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

BOX = [54.30, 24.35, 54.70, 24.65]
ANNOTATORS = ["A", "B", "C"]          # blind annotator files (the PoC used AI-assisted labels: labeling/returned/labels_Claude_AI.csv)
N = {"mangrove_core": 100, "mangrove_edge": 40, "near_nonmangrove": 100, "far_background": 60}
N_SHARED = 20
MIN_SEP_M, NEAR_M, FAR_MAX_M = 150, 300, 3000
rng = np.random.default_rng(2026)
OUT = "labeling"; os.makedirs(OUT, exist_ok=True)

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
items = list(cat.search(collections=["esa-worldcover"], bbox=BOX, datetime="2021-01-01/2021-12-31").items())
arr, tr = merge([rasterio.open(i.assets["map"].href) for i in items], bounds=BOX)
wc = arr[0]; H, W = wc.shape
mang = wc == 95
px_m = 9.0                                                   # ~9 m per WorldCover pixel at this latitude (approximation)
core = ndi.binary_erosion(mang, iterations=1)
edge = mang & ~core
dist_m = ndi.distance_transform_edt(~mang) * px_m           # metres to the nearest mangrove pixel
strata = {
    "mangrove_core": core,
    "mangrove_edge": edge,
    "near_nonmangrove": (~mang) & (dist_m <= NEAR_M) & (wc != 0),
    "far_background": (~mang) & (dist_m > NEAR_M) & (dist_m <= FAR_MAX_M) & (wc != 0),
}
lat0 = (BOX[1] + BOX[3]) / 2
to_xy = lambda lon, lat: np.c_[(lon - BOX[0]) * np.cos(np.radians(lat0)) * 111320, (lat - BOX[1]) * 110574]


def pick(mask, n, taken_xy, weights_by_class=None):
    """random pixels from `mask`, >= MIN_SEP_M from every already-chosen point"""
    rows, cols = np.nonzero(mask)
    if len(rows) == 0:
        return []
    order = rng.permutation(len(rows)); out = []
    for k in order:
        r, c = rows[k], cols[k]
        lon, lat = rasterio.transform.xy(tr, r, c)
        xy = to_xy(np.array([lon]), np.array([lat]))[0]
        if taken_xy and cKDTree(np.array(taken_xy)).query(xy)[0] < MIN_SEP_M:
            continue
        taken_xy.append(xy); out.append((lon, lat, int(wc[r, c])))
        if len(out) >= n:
            break
    return out


taken, rows_out = [], []
for name, mask in strata.items():
    if name == "near_nonmangrove":                             # class-balanced: water, bare, built, trees, shrub, grass, crop, wetland
        classes = [c for c in np.unique(wc[mask]) if (mask & (wc == c)).sum() > 50]
        per = int(np.ceil(N[name] / len(classes))); got = []
        for c in classes:
            got += pick(mask & (wc == c), per, taken)
        got = got[:N[name]]
    else:
        got = pick(mask, N[name], taken)
    print(f"{name:18s}: wanted {N[name]:3d}, got {len(got):3d}")
    rows_out += [dict(stratum=name, lon=lo, lat=la, wc_class=cl) for lo, la, cl in got]

df = pd.DataFrame(rows_out).sample(frac=1, random_state=1).reset_index(drop=True)
df.insert(0, "point_id", [f"P{i + 1:03d}" for i in range(len(df))])
xy = to_xy(df.lon.values, df.lat.values)
df["block_1km"] = [f"B{int(x // 1000)}_{int(y // 1000)}" for x, y in xy]       # for spatial train/test splits later
shared = df.sample(N_SHARED, random_state=7).point_id.tolist()
df["group"] = "unique"; df.loc[df.point_id.isin(shared), "group"] = "shared"
uniq = df[df.group == "unique"].sort_values(["stratum", "point_id"])
df["annotator"] = ""                                                          # unique points: round-robin inside strata
for i, idx in enumerate(uniq.index):
    df.loc[idx, "annotator"] = ANNOTATORS[i % len(ANNOTATORS)]
df.loc[df.group == "shared", "annotator"] = "all"
df.to_csv(f"{OUT}/points_master.csv", index=False)
print(df.groupby(["stratum", "group"]).size().unstack(fill_value=0)); print(df.annotator.value_counts().to_dict())


def kml(points, title):
    pm = "".join(f"<Placemark><name>{r.point_id}</name><Point><coordinates>{r.lon:.6f},{r.lat:.6f},0</coordinates></Point></Placemark>"
                 for r in points.itertuples())
    return f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{title}</name>{pm}</Document></kml>'


for a in ANNOTATORS:
    mine = df[(df.annotator == a) | (df.annotator == "all")].sort_values("point_id")
    out = pd.DataFrame({
        "point_id": mine.point_id, "lon": mine.lon.round(6), "lat": mine.lat.round(6),
        "google_maps_satellite": [f"https://www.google.com/maps/@{la:.6f},{lo:.6f},250m/data=!3m1!1e3" for lo, la in zip(mine.lon, mine.lat)],
        "label": "", "confidence_1to3": "", "image_date": "", "notes": ""})
    out.to_csv(f"{OUT}/points_{a}.csv", index=False, encoding="utf-8-sig")
    open(f"{OUT}/points_{a}.kml", "w", encoding="utf-8").write(kml(mine, f"Mangrove labeling - {a}"))
    print(a, len(out), "points")
