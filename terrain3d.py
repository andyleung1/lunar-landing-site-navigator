# terrain3d.py
# Builds the interactive 3D terrain view for one site, as a single HTML string
# that app.py shows inside the page. Needs viewer_template.html in this folder.
#
# Requires: numpy, tifffile

import base64
import json
import math
from pathlib import Path

import numpy as np
import tifffile

R_MOON = 1737400.0   # metres, the sphere the DEM heights are measured from
TEMPLATE = Path(__file__).with_name("viewer_template.html")


def polar_xy(lat, lon):
    """Latitude/longitude in degrees -> south polar stereographic X, Y in metres."""
    r = 2 * R_MOON * math.tan(math.radians(90 + lat) / 2)
    return r * math.sin(math.radians(lon)), r * math.cos(math.radians(lon))


def pack_dem(dem_path, step=8):
    """Read a DEM GeoTIFF and shrink it for the browser.

    step averages that many pixels together (8 turns a 5 m grid into 40 m).
    Heights are stored as 16-bit numbers, which keeps them accurate to
    better than 10 cm.
    """
    with tifffile.TiffFile(dem_path) as tif:
        page = tif.pages[0]
        z = page.asarray().astype(np.float32)
        tags = {t.name: t.value for t in page.tags}
    cell = float(tags["ModelPixelScaleTag"][0])
    x0, y0 = tags["ModelTiepointTag"][3:5]            # top-left corner, metres

    rows, cols = (z.shape[0] // step) * step, (z.shape[1] // step) * step
    z = np.nanmean(z[:rows, :cols].reshape(rows // step, step, cols // step, step), axis=(1, 3))
    zmin, zmax = float(np.nanmin(z)), float(np.nanmax(z))
    q = np.round((np.nan_to_num(z, nan=zmin) - zmin) / (zmax - zmin) * 65535).astype("<u2")

    cx, cy = x0 + cols * cell / 2, y0 - rows * cell / 2   # centre of the DEM
    return {
        "w": q.shape[1], "h": q.shape[0], "cell": cell * step,
        "cx": cx, "cy": cy,
        "lat": -90 + 2 * math.degrees(math.atan(math.hypot(cx, cy) / (2 * R_MOON))),
        "lon": math.degrees(math.atan2(cx, cy)) % 360,
        "zmin": round(zmin, 2), "zmax": round(zmax, 2),
        "data": base64.b64encode(q.tobytes()).decode("ascii"),
    }


def viewer_html(dem_path, name="Site", lat=None, lon=None, step=8):
    """Full HTML page for the 3D view of one DEM.

    If lat/lon are given and fall inside the DEM, a white ring marks that spot.
    """
    site = pack_dem(dem_path, step)
    site["id"], site["name"] = "site", name

    if lat is not None and lon is not None:
        x, y = polar_xy(lat, lon)
        half_w, half_h = site["w"] * site["cell"] / 2, site["h"] * site["cell"] / 2
        if abs(x - site["cx"]) <= half_w and abs(y - site["cy"]) <= half_h:
            site["mark"] = [x, y]

    html = TEMPLATE.read_text(encoding="utf-8")
    return html.replace("__SITES_JSON__", json.dumps([site], separators=(",", ":")))
