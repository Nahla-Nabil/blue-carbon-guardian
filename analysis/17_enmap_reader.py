"""EnMAP L2A reader + per-stand spectra + hyperspectral indices (Module 3, step 1).

Data: EnMAP L2A (land mode) scenes ordered from DLR EOWEB, extracted in data/enmap/scenes/<tag>/<scene>/ (NOT to be redistributed: EnMAP licence v1.1;
any derived figure/table must carry "Contains modified EnMAP data (c)DLR <year>").
Scenes: e20221101 (DT4978, tile 002, quality 0, cloud 2 %), e20250414 (DT124368, tile 003, quality 0, cloud 3 %).

What this module provides (import it from other scripts):
  load_scene(tag)      -> dict(cube int16 [224,H,W], wl [224], gain, transform, crs, masks ...)
  reflectance(cube)    -> float32 reflectance with nodata / bad pixels / negative values = NaN
  band_mean(R, wl, lo, hi), band_at(R, wl, nm)  -> spectral helpers
  s2_like(R, wl)       -> dict of Sentinel-2-like bands (B03,B04,B05,B08,B8A,B11,B12) made by averaging EnMAP bands over the S2 spectral ranges (boxcar approximation)
  indices(R, wl)       -> hyperspectral indices incl. those Sentinel-2 cannot make: red-edge position (REP), water band index (WBI), NDWI1240, NDII1650
Run as a script: builds analysis/data/enmap_stand_spectra.csv (mean spectrum of pure-mangrove pixels of every stand, per scene) and prints QC.
"""
import glob, json, numpy as np, pandas as pd, rasterio
from lxml import etree
from rasterio.features import rasterize
from rasterio.warp import reproject, Resampling, transform_geom
from rasterio.transform import Affine

BAD_RANGES = [(1340, 1460), (1790, 1960), (2450, 2600)]      # water-vapour windows + noisy SWIR edge (nm)
NODATA = -32768


def _path(tag, suffix):
    return glob.glob(f"data/enmap/scenes/{tag}/*/*{suffix}")[0]


def load_scene(tag, read_cube=True):
    f = _path(tag, "SPECTRAL_IMAGE.TIF")
    root = etree.parse(_path(tag, "-METADATA.XML")).getroot()
    wl, gain = {}, {}
    for b in root.iter("bandID"):
        n = int(b.get("number"))
        if n in wl: continue
        wl[n] = float(b.find("wavelengthCenterOfBand").text); gain[n] = float(b.find("GainOfBand").text)
    wl = np.array([wl[i] for i in range(1, 225)]); gain = np.array([gain[i] for i in range(1, 225)])
    with rasterio.open(f) as ds:
        out = dict(tag=tag, transform=ds.transform, crs=ds.crs, H=ds.height, W=ds.width, wl=wl, gain=gain, path=f)
        if read_cube: out["cube"] = ds.read()
    for m in ("CLOUD", "CLOUDSHADOW", "HAZE", "CIRRUS"):
        with rasterio.open(_path(tag, f"QL_QUALITY_{m}.TIF")) as d: out[m.lower()] = d.read(1).astype(bool)
    with rasterio.open(_path(tag, "QL_PIXELMASK.TIF")) as d: out["pixmask"] = d.read().astype(bool)      # per-band bad-pixel flag
    out["date"] = tag[1:]
    return out


def reflectance(sc, scene_masks=False):
    """float32 reflectance [224,H,W]; NaN for nodata, per-band flagged pixels and negative values.
    scene_masks=False (default): the product's cloud/haze/cirrus flags are NOT applied. Evidence (Sep 2026): over this AOI they wrongly flag bright reclaimed sand / built surfaces
    (stand 5: 83 % of pixels 'cloud' on 14 Apr 2025, 43 % 'haze' on 1 Nov 2022) while Sentinel-2 scenes of the same days are clear (SCL). Cloud SHADOW is 0 in both scenes; SNOW flag is
    also ignored (false positives on salt/sabkha). Use scene_masks=True only for scenes whose cloud flags you have verified."""
    cube = sc["cube"].astype("float32")
    bad = (cube == NODATA) | sc["pixmask"]
    R = cube * sc["gain"][:, None, None]; R[bad] = np.nan
    if scene_masks:
        scene_bad = sc["cloud"] | sc["cloudshadow"] | sc["haze"] | sc["cirrus"]
        R[:, scene_bad] = np.nan
    R[R < 0] = np.nan
    return R


def band_mean(R, wl, lo, hi):
    idx = np.where((wl >= lo) & (wl <= hi))[0]
    return np.nanmean(R[idx], axis=0)


def band_at(R, wl, nm):
    return R[int(np.argmin(np.abs(wl - nm)))]


def s2_like(R, wl):
    """Sentinel-2-like bands (boxcar over the nominal S2 ranges, nm)."""
    rng = dict(B03=(543, 578), B04=(650, 680), B05=(698, 713), B08=(785, 900), B8A=(855, 875), B11=(1565, 1655), B12=(2100, 2280))
    return {k: band_mean(R, wl, *v) for k, v in rng.items()}


def nd(a, b):
    return (a - b) / (a + b + 1e-9)


def indices(R, wl):
    s = s2_like(R, wl)
    r670, r700, r740, r780 = (band_at(R, wl, x) for x in (670, 700, 740, 780))
    rre = (r670 + r780) / 2
    rep = 700 + 40 * ((rre - r700) / (r740 - r700 + 1e-9))                       # red-edge position (nm), linear-interpolation method
    return dict(
        NDVI_s2=nd(s["B08"], s["B04"]), NDRE_s2=nd(s["B8A"], s["B05"]), NDMI_s2=nd(s["B8A"], s["B11"]), MNDWI_s2=nd(s["B03"], s["B11"]),
        REP=np.clip(rep, 690, 750), WBI=band_at(R, wl, 900) / (band_at(R, wl, 970) + 1e-9),
        NDWI1240=nd(band_at(R, wl, 860), band_at(R, wl, 1240)), NDII1650=nd(band_at(R, wl, 820), band_at(R, wl, 1650)))


def good_band_mask(wl):
    ok = np.ones(len(wl), bool)
    for lo, hi in BAD_RANGES: ok &= ~((wl >= lo) & (wl <= hi))
    return ok


def mangrove_fraction(sc):
    """fraction of each 30 m EnMAP pixel covered by WorldCover-2021 mangrove (class 95), via area-average of the 10 m mask."""
    g = json.load(open("analysis/data/grid.json")); wc = np.load("analysis/data/worldcover_grid.npy") == 95
    src_tr = Affine(*g["transform"]); out = np.zeros((sc["H"], sc["W"]), "float32")
    reproject(wc.astype("float32"), out, src_transform=src_tr, src_crs=g["crs"], dst_transform=sc["transform"], dst_crs=sc["crs"], resampling=Resampling.average)
    return out


def stand_masks(sc):
    gj = json.load(open("analysis/data/stands.geojson")); out = {}
    for f in gj["features"]:
        geom = transform_geom("EPSG:4326", sc["crs"].to_string(), f["geometry"])
        out[f["properties"]["stand"]] = rasterize([(geom, 1)], out_shape=(sc["H"], sc["W"]), transform=sc["transform"], fill=0, dtype="uint8").astype(bool)
    return out


if __name__ == "__main__":
    rows = []
    for tag in ("e20221101", "e20250414"):
        sc = load_scene(tag); R = reflectance(sc); wl = sc["wl"]; ok = good_band_mask(wl)
        frac = mangrove_fraction(sc); masks = stand_masks(sc)
        valid_scene = np.isfinite(R[[int(np.argmin(abs(wl - x))) for x in (560, 665, 865, 1650)]]).all(axis=0)
        print(f"\n== {tag}: {sc['H']}x{sc['W']}, wavelengths {wl[0]:.0f}-{wl[-1]:.0f} nm ({len(wl)} bands, {ok.sum()} after dropping vapour/noisy), valid pixels {valid_scene.mean() * 100:.0f} %")
        for k, m in masks.items():
            pure = m & (frac >= 0.7) & valid_scene
            thr = 0.7
            if pure.sum() < 5: pure = m & (frac >= 0.5) & valid_scene; thr = 0.5
            n_all = int(m.sum())
            if pure.sum() == 0: rows.append(dict(scene=tag, stand=k, n_pix=0, n_stand_pix=n_all)); continue
            spec = np.nanmean(R[:, pure], axis=1)
            rows.append(dict(scene=tag, stand=k, n_pix=int(pure.sum()), n_stand_pix=n_all, purity_thr=thr, **{f"r{w:.0f}": v for w, v in zip(wl, spec)}))
        d = pd.DataFrame([r for r in rows if r["scene"] == tag]); print(f" stands with >=5 pure valid pixels: {(d.n_pix >= 5).sum()} / {len(d)} | median pure pixels {d.n_pix.median():.0f}")
        del R
    pd.DataFrame(rows).to_csv("analysis/data/enmap_stand_spectra.csv", index=False)
    print("\nsaved analysis/data/enmap_stand_spectra.csv")
