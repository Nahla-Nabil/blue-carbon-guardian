"""Feasibility spike: for each candidate AOI, how much mangrove is there (ESA WorldCover 2021, class 95),
how fragmented is it, how many *pure* pixels would a 10/20/30 m sensor see, and how many
Sentinel-2 L2A scenes (cloud<20%) exist 2017-2026?"""
import numpy as np, pystac_client, planetary_computer as pc, rasterio
from rasterio.merge import merge
from scipy import ndimage as ndi

AOIS = {  # lon_min, lat_min, lon_max, lat_max  (approximate boxes, to be refined)
 "AbuDhabi (Eastern Mangroves/Jubail)": [54.30,24.35,54.70,24.65],
 "Bahrain (Tubli/Arad/Hawar)":          [50.40,25.55,50.85,26.35],
 "Saudi Gulf - Tarut Bay":              [49.90,26.35,50.35,26.85],
 "Saudi Gulf - Jubail":                 [49.45,26.85,49.85,27.25],
 "Saudi Red Sea - Jazan/Farasan":       [42.00,16.60,42.70,17.20],
}
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

def pure_blocks(mask, k):
    """count k x k blocks (k=2 -> 20 m, k=3 -> 30 m on a 10 m grid) that are 100% mangrove"""
    h, w = (mask.shape[0]//k)*k, (mask.shape[1]//k)*k
    b = mask[:h,:w].reshape(h//k, k, w//k, k)
    return int(b.all(axis=(1,3)).sum())

for name, bb in AOIS.items():
    print("\n=====", name, bb)
    try:
        items = list(cat.search(collections=["esa-worldcover"], bbox=bb, datetime="2021-01-01/2021-12-31").items())
        srcs = [rasterio.open(i.assets["map"].href) for i in items]
        arr, tr = merge(srcs, bounds=bb)
        m = (arr[0] == 95)
        px_ha = 0.01
        lab, n = ndi.label(m)
        sizes = np.bincount(lab.ravel())[1:] * px_ha if n else np.array([])
        print(f"WorldCover2021 mangrove: {m.sum()*px_ha:8.1f} ha in {n} patches | median patch {np.median(sizes) if n else 0:.2f} ha | "
              f"patches >=1 ha: {(sizes>=1).sum()} | >=5 ha: {(sizes>=5).sum()} | largest {sizes.max() if n else 0:.1f} ha")
        for k, lab_ in [(1,"10 m (S2)"),(2,"20 m (813)"),(3,"30 m (Tanager/EnMAP)")]:
            pb = int(m.sum()) if k==1 else pure_blocks(m, k)
            print(f"   pure {lab_:22s}: {pb:7d} pixels  ({pb*k*k*px_ha:8.1f} ha)")
    except Exception as e:
        print("WorldCover ERR", repr(e)[:200])
    try:
        s = list(cat.search(collections=["sentinel-2-l2a"], bbox=bb, datetime="2017-01-01/2026-09-19",
                            query={"eo:cloud_cover": {"lt": 20}}).items())
        dates = sorted({i.datetime.date() for i in s})
        yrs = {}
        for d in dates: yrs[d.year] = yrs.get(d.year,0)+1
        print(f"Sentinel-2 L2A <20% cloud: {len(s)} tile-scenes, {len(dates)} distinct dates | per year: {yrs}")
    except Exception as e:
        print("S2 ERR", repr(e)[:200])
