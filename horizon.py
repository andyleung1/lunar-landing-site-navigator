# Works out the terrain horizon around a site from its DEM:
# for each compass direction, how many degrees the terrain rises above level.
#
# Run it on its own to print a site's horizon:
# python horizon.py

import re

import numpy as np
import rasterio
import pandas as pd
from rasterio.warp import transform

from sites import HERE, moon_lonlat, observer_height, get_sites

moon_radius = 1737400.0
SAVE_DIR = HERE / "precomputed"


def horizon_mask(site, step_deg=0.5, observer_height_m=observer_height):
    """Return (azimuths, horizon_angles, reach_km) for a site that has a DEM.

    azimuths       compass directions in degrees (0 = north, 90 = east)
    horizon_angles highest terrain angle in each direction, in degrees
    reach_km       how far the DEM extends in the shortest direction; terrain
                   farther away than this is NOT included
    """
    with rasterio.open(HERE / site["dem"]) as d:
        heights = d.read(1).astype("float64")
        if d.nodata is not None:
            heights[heights == d.nodata] = np.nan
        to_pixel = ~d.transform          # map x/y (meters) -> column/row
        crs = d.crs
        pixel_m = abs(d.res[0])
        n_rows, n_cols = heights.shape

    def to_xy(lat, lon):
        xs, ys = transform(moon_lonlat, crs, [lon], [lat])
        return np.array([xs[0], ys[0]])

    # The site's position on the map, and its ground height.
    lat, lon = site["lat"], site["lon"]
    site_xy = to_xy(lat, lon)
    col, row = to_pixel * tuple(site_xy)
    eye = heights[int(row), int(col)] + observer_height_m

    # Which way is north and which way is east on the map at this site?
    # Step a tiny bit north and a tiny bit east, and see where the map moves.
    tiny = 1e-4  # degrees
    north = to_xy(lat + tiny, lon) - site_xy
    east = to_xy(lat, lon + tiny / np.cos(np.radians(lat))) - site_xy
    north /= np.linalg.norm(north)
    east /= np.linalg.norm(east)

    # Distances to sample along each ray, one pixel apart.
    max_dist = np.hypot(n_rows, n_cols) * pixel_m
    dist = np.arange(pixel_m, max_dist, pixel_m)
    drop = dist**2 / (2 * moon_radius)   # how far the surface curves away

    azimuths = np.arange(0.0, 360.0, step_deg)
    angles = np.full(len(azimuths), np.nan)
    reach = np.zeros(len(azimuths))

    for i, az in enumerate(azimuths):
        a = np.radians(az)
        direction = np.cos(a) * north + np.sin(a) * east
        x = site_xy[0] + dist * direction[0]
        y = site_xy[1] + dist * direction[1]
        c, r = to_pixel * (x, y)
        c, r = np.floor(c).astype(int), np.floor(r).astype(int)

        inside = (r >= 0) & (r < n_rows) & (c >= 0) & (c < n_cols)
        h = heights[r[inside], c[inside]]
        ang = np.degrees(np.arctan2(h - eye - drop[inside], dist[inside]))
        angles[i] = np.nanmax(ang)
        reach[i] = dist[inside][-1]

    return azimuths, angles, reach.min() / 1000

def file_name(site_name):
    """'Test: near pole' -> 'test_near_pole' (safe as a Windows file name)."""
    return re.sub(r"[^A-Za-z0-9]+", "_", site_name).strip("_").lower()


def saved_horizon(site):
    """Same result as horizon_mask(site), but saved to a file the first time.

    Later calls read the file instead of recalculating. If the DEM file is
    newer than the saved copy (you replaced the DEM), it recalculates.
    """
    path = SAVE_DIR / f'{file_name(site["name"])}_horizon.parquet'
    dem_path = HERE / site["dem"]
    if path.exists() and path.stat().st_mtime > dem_path.stat().st_mtime:
        saved = pd.read_parquet(path)
        if "reach_km" in saved.columns:   # older saved files lack this; redo them
            return saved["azimuth"].values, saved["terrain"].values, saved["reach_km"].iloc[0]

    az, angles, reach_km = horizon_mask(site)
    SAVE_DIR.mkdir(exist_ok=True)
    pd.DataFrame({"azimuth": az, "terrain": angles, "reach_km": reach_km}).to_parquet(path)
    return az, angles, reach_km

if __name__ == "__main__":
    for s in get_sites():
        if not s.get("dem"):
            continue
        az, ang, reach_km = horizon_mask(s)
        print(f'{s["name"]}: DEM reaches {reach_km:.1f} km in its shortest direction')
        for a in range(0, 360, 30):
            print(f"  az {a:3d}   horizon {np.interp(a, az, ang):6.2f} deg")