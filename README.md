Lunar Navigator
Sunlight, Earth visibility and solar power at candidate landing sites near the lunar south pole, using real terrain from LOLA elevation models (DEMs).
For any site and date range, it finds:
% sunlit: how much of the time the Sun is above the local terrain (partial Sun counts partially)
% Earth visible: how much of the time Earth is above the terrain (direct communication)
% sunlit and Earth visible at the same time
Longest darkness: the longest stretch with no Sun at all
Solar power from a vertical, Sun-tracking panel
A Streamlit app shows the results, a 360° panorama of the horizon with the Sun and Earth paths, and a 3D view of the terrain
How it works
Sun and Earth positions come from Skyfield with NASA JPL's DE421 ephemeris and the Moon's orientation (MOON_ME_DE421 frame).
The terrain horizon is traced from each site's DEM: for 720 directions (every 0.5°), the steepest angle up to the terrain, allowing for the Moon's curvature. Observer is 2 m above the ground.
Visibility compares the Sun's and Earth's altitude with the horizon in their direction at each time step (hourly by default).
Project structure
File	Purpose
sites.py	The list of sites and their DEMs, shared by every other file
positions.py	Sun/Earth altitude and azimuth table for a site (command line)
horizon.py	Terrain horizon from a DEM; saves results to `precomputed/`
metrics.py	Sunlight, Earth visibility and power statistics (command line)
terrain3d.py	Builds custom terrain designs around a site
app.py	Streamlit app
precompute.py	Saves every site's horizon ahead of time
theme.py Changes the layout of Streamlit app
Folders (not in version control): `data/` holds the DEM GeoTIFFs; `precomputed/` holds saved horizons and is created automatically.
Setup
Requires Python 3.9 or newer.
```bash
pip install rasterio skyfield streamlit plotly pandas pyarrow numpy tifffile
```
The first run downloads about 30 MB of NASA files (ephemeris and Moon orientation) into the project folder.
Put each site's DEM in `data/` and list it in `sites.py`, e.g.:
```python
{
    "name": "Haworth",
    "lat": None,   # None = use the DEM's center
    "lon": None,
    "dem": "data/Haworth_final_adj_5mpp_surf.tif",
},
```
Usage
App:
```bash
python precompute.py      # optional: saves horizons so the app starts faster
streamlit run app.py
```
In the sidebar, choose a site, the dates (1900–2050) and the terrain (the site's DEM, your own design, or flat ground), then press Update.
Command line:
```bash
python sites.py           # site coordinates
python horizon.py         # each site's horizon, every 30°
python positions.py       # Sun/Earth position table, weekly rows
python metrics.py        # sunlight, Earth visibility and power statistics
```
Adding a site
Download its DEM (see Data sources) or cut one from the south pole mosaic in QGIS, with the site in the middle.
Save it as a GeoTIFF in `data/` and run `check_dem.py` on it.
Add an entry to `sites` in `sites.py`.
Run python precompute.py.
Limitations
Terrain beyond the DEM's edge is ignored. At the pole, distant mountains can block the low Sun, so a small DEM can overstate sunlight. Use 40–100 km of terrain for final numbers.
Features smaller than a DEM pixel (boulders, small craters) are not resolved.
Power is an upper bound: no dust, temperature, wiring losses or battery model.
Data sources and credits
Terrain: LOLA 5 m/pixel south pole site DEMs and mosaic, NASA GSFC Planetary Geodesy Data Archive (site DEMs, mosaic). Please cite Barker et al. (2021), Planetary and Space Science, doi:10.1016/j.pss.2020.105119.
Ephemeris and Moon orientation: NASA JPL DE421 and NAIF kernels (`moon_080317.tf`, `pck00008.tpc`, `moon_pa_de421_1900-2050.bpc`), loaded through Skyfield.
Libraries: Skyfield, rasterio, NumPy, pandas, Streamlit, Plotly, tifffile.
