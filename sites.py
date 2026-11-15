# a list of sites used for the project
from pathlib import Path

import rasterio
from rasterio.warp import transform

HERE = Path(__file__).parent

moon_lonlat = "+proj=longlat +R=1737400 +no_defs"
observer_height = 2.0

sites = [
    {
        "name":"Haworth",
        "lat": -86.7639,
        "lon": -22.7770,
        "dem" : "data/Haworth_final_adj_5mpp_surf.tif"
    },
    {
        "name":"Noble Rim 1",
        "lat": -85.4381,
        "lon": 37.3667,
        "dem" : "data/Site06_final_adj_5mpp_surf.tif"
    },
    {
        "name":"Malapert massif",
        "lat": -85.9948,
        "lon": -0.2358,
        "dem" : "data/Site23_final_adj_5mpp_surf.tif"
    },
    {
        "name":"de Gerlache rim",
        "latitude": -88.2300,
        "longitude": -64.6284,
        "dem" : "data/SL2_final_adj_5mpp_surf.tif"
    },
    {
        "name":"Leibnitz beta plateau",
        "latitude": -85.4266,
        "longitude": 31.7428,
        "dem" : "data/Site20_final_adj_5mpp_surf.tif"
    },
    {
        "name":"Connecting ridge",
        "latitude": -89.4632,
        "longitude": -137.4896,
        "dem" : "data/Site01_final_adj_5mpp_surf.tif"
    },
    {
        "name":"Peak near Shackleton",
        "latitude": -88.8110,
        "longitude": 123.6901,
        "dem" : "data/Site07_final_adj_5mpp_surf.tif"
    },
    {
        "name":"Shoemaker",
        "latitude": -87.1835,
        "longitude": 62.8350,
        "dem" : "data/Shoemaker_final_adj_5mpp_surf.tif"
    }
        
]

def dem_center(dem_path):
    """Return (lat, lon) of the center of a DEM file"""
    with rasterio.open(dem_path) as d:
        x = (d.bounds.left + d.bounds.right) / 2
        y = (d.bounds.top + d.bounds.bottom) / 2
        lons, lats = transform(d.crs, moon_lonlat, [x], [y])
    return lats[0], lons[0]

def get_sites():
    """Return the site list with missing coordinates filled from the DEMs."""
    out = []
    for s in sites:
        s = dict(s)
        if s.get("lat") is None and s.get("dem"):
            s["lat"], s["lon"] = dem_center(s["dem"])
        out.append(s)
    return out


if __name__ == "__main__":
    for s in sites:
        if s["dem"]:
            lat, lon = dem_center(s["dem"])
            print(f'{s["name"]:20s} lat {lat:9.4f}  lon {lon:9.4f}   ({s["dem"]})')
        else:
            print(f'{s["name"]:20s} no DEM yet')
