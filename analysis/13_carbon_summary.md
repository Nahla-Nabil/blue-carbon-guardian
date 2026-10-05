# Carbon density from field data (Schile et al. 2016)

| Site               |   n |   tree |   soil |   total |   soil_depth |   lat |   lon |
|:-------------------|----:|-------:|-------:|--------:|-------------:|------:|------:|
| Jubail Island East |   6 |    7.3 |   70.1 |    77.5 |         40   |  24.5 |  54.5 |
| Eastern Mangrove   |   6 |   17.6 |   61.5 |    79.2 |         34.5 |  24.5 |  54.4 |
| Bu Tinah Jaoub     |   6 |   46.2 |   36.7 |    82.9 |         20.5 |  24.6 |  53.1 |
| Jubail Island      |   6 |   28.2 |   70.9 |    99.2 |        300   |  24.5 |  54.5 |
| Umm al Quwain      |   6 |   27.8 |   76.6 |   104.4 |         50   |  25.5 |  55.6 |
| Al Shalila         |   6 |   10.6 |   93.9 |   104.6 |        200   |  24.7 |  54.7 |
| Marawah Island     |   6 |   21.4 |   83.5 |   104.9 |         26.5 |  24.3 |  53.3 |
| Sinnia             |   6 |   41.1 |   71.6 |   112.7 |         50   |  25.6 |  55.6 |
| Bu Tinah Shamal    |   6 |   29.5 |   89.7 |   119.2 |         26   |  24.6 |  53.1 |
| Al Rams            |   6 |   55.9 |   88   |   143.9 |         50   |  25.9 |  56   |
| Salaam             |   6 |   24.4 |  153.3 |   177.8 |        190   |  24.5 |  54.4 |
| Ajman Al Zorah     |   6 |   90.7 |  101   |   191.7 |        100   |  25.4 |  55.5 |
| Kalba North        |   6 |   80.1 |  140.1 |   220.2 |        100   |  25   |  56.4 |
| Ras Al Kaimah      |   6 |  108.8 |  144.6 |   253.3 |        100   |  25.8 |  55.9 |
| Al Khor            |   6 |   98   |  159.1 |   257.1 |        100   |  25.2 |  55.3 |
| Kalba East         |   6 |   88.1 |  183.1 |   271.2 |        100   | nan   | nan   |
| Kalba West         |   6 |   99.1 |  190.7 |   289.8 |        100   |  25   |  56.4 |
| Kalba South        |   6 |  138.6 |  191.3 |   329.9 |        100   | nan   | nan   |

{
 "local_n": 24,
 "local_sites": [
  "Eastern Mangrove",
  "Jubail Island",
  "Jubail Island East",
  "Salaam"
 ],
 "local_mean": 108.39074160769208,
 "local_p10": 48.14793591465161,
 "local_p50": 94.91569538341211,
 "local_p90": 190.23709790805097,
 "uae_n": 108,
 "uae_mean": 167.74241015737186,
 "uae_p10": 65.60035110987258,
 "uae_p50": 145.77755088811523,
 "uae_p90": 298.21638697036354,
 "ci90_lo": 78.73478201251957,
 "ci90_hi": 138.47370513784665,
 "n_sites": 4,
 "soil_uncapped_local": 144.37561872934143,
 "tree_local": 19.414271813683335,
 "soil_local": 88.97646979400874,
 "soil_depth_median": 106.0
}

## EO (Sentinel-2 2020-21) vs field tree/total carbon (2013-14 plots)

95 plots with EO values across 16 sites. Plot-level Spearman rho (p-value):
- tree carbon: NDVI +0.08 (p=0.42, ns), NDMI -0.01 (ns), NDRE +0.27 (p=0.009)
- total carbon (tree+soil): NDVI +0.22 (p=0.036), NDMI +0.02 (ns), NDRE +0.38 (p<0.001)

Site-level (n=16 site means): none significant (largest NDRE vs total_c rho=0.45, p=0.078).

**Reading:** NDRE shows a weak-to-moderate, statistically significant plot-level association with total carbon (explains roughly 14% of variance, rho^2), but the
7-8 year gap between field sampling (2013) and imagery (2020-21), tidal/seasonal noise (not corrected here), and a modest sample size mean this is **far too weak to
use as a biomass model**. NDMI shows no relationship despite tracking canopy moisture well in the health-monitoring module -- it is a different signal at plot scale.

**Conclusion for the product:** carbon is computed as stand area x field-measured density (the local 108 t C/ha figure), NOT from an imagery-derived biomass equation.
This EO-vs-field test is reported as a validation / exploration step, and the weak result is stated honestly rather than presented as a working biomass model.
