# metrics.py
# Sunlight, Earth visibility and solar power at a site, including terrain.
#
# Run it from a terminal in the project folder:
# python metrics.py

import numpy as np
import pandas as pd

from horizon import horizon_mask, saved_horizon
from positions import ask_number, ask_start_time, choose_site
from positions import earth, frame, moon, pc, sun, ts

# ---------- Settings you can change ----------

PANEL_AREA_M2 = 1.0        # panel area in square meters
PANEL_EFFICIENCY = 0.30    # fraction of sunlight turned into electricity
SOLAR_CONSTANT = 1361.0    # sunlight strength at 1 AU from the Sun, W per m^2
SUN_RADIUS_DEG = 0.267     # the Sun's disk is about 0.53 degrees across


def sun_fraction(height_deg):
    """Fraction of the Sun's disk above the horizon (0 to 1).

    height_deg is how far the Sun's center is above the terrain horizon.
    """
    x = np.clip(height_deg / SUN_RADIUS_DEG, -1, 1)
    hidden = (np.arccos(x) - x * np.sqrt(1 - x**2)) / np.pi
    return 1 - hidden


def longest_run(flags):
    """Length of the longest stretch of True values in a row."""
    best = run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        best = max(best, run)
    return best

def make_times(start, end, step_hours):
    """Skyfield times from `start` up to (not including) `end`, every step_hours.
    start and end are datetimes (or dates) in UTC."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    total_hours = (end - start) / pd.Timedelta(hours=1)
    hours = np.arange(0, total_hours, step_hours) + start.hour + start.minute / 60
    return ts.utc(start.year, start.month, start.day, hours)


def compute_table(site, times):
    """One row per time: where the Sun and Earth are, the terrain in their
    direction, whether they are visible, and sunlight on a vertical panel
    that turns to face the Sun (per m^2, before efficiency)."""
    place = moon + pc.build_latlon_degrees(frame, site["lat"], site["lon"])
    sun_alt, sun_az, sun_dist = place.at(times).observe(sun).apparent().altaz()
    earth_alt, earth_az, _ = place.at(times).observe(earth).apparent().altaz()

    if site.get("dem"):
        az, horizon, _ = saved_horizon(site)
        sun_terrain = np.interp(sun_az.degrees, az, horizon, period=360)
        earth_terrain = np.interp(earth_az.degrees, az, horizon, period=360)
    else:
        sun_terrain = np.zeros(len(times))      # no DEM: flat terrain
        earth_terrain = np.zeros(len(times))

    sunlit = sun_fraction(sun_alt.degrees - sun_terrain)

    return pd.DataFrame({
        "time": times.utc_datetime(),
        "sun_alt": sun_alt.degrees,
        "sun_az": sun_az.degrees,
        "sun_terrain": sun_terrain,
        "sunlit": sunlit,                       # fraction of Sun's disk, 0 to 1
        "earth_alt": earth_alt.degrees,
        "earth_az": earth_az.degrees,
        "earth_terrain": earth_terrain,
        "earth_up": earth_alt.degrees > earth_terrain,
        "panel_w_per_m2": SOLAR_CONSTANT / sun_dist.au**2 * sunlit
                          * np.cos(np.radians(sun_alt.degrees)),
    })

def main():
    site = choose_site()
    if not site.get("dem"):
        print(f'{site["name"]} has no DEM, so its terrain horizon is unknown.')
        return

    print("Working out the terrain horizon from the DEM...")
    az, horizon, reach_km = horizon_mask(site)

    start = ask_start_time()
    days = ask_number("How many days to cover", 365)
    step = ask_number("Hours between time steps", 1)

    hours = np.arange(0, days * 24, step) + start.hour + start.minute / 60
    times = ts.utc(start.year, start.month, start.day, hours)

    place = moon + pc.build_latlon_degrees(frame, site["lat"], site["lon"])
    sun_alt, sun_az, sun_dist = place.at(times).observe(sun).apparent().altaz()
    earth_alt, earth_az, _ = place.at(times).observe(earth).apparent().altaz()

    # Terrain height in the direction of the Sun and Earth at each time step.
    sun_horizon = np.interp(sun_az.degrees, az, horizon, period=360)
    earth_horizon = np.interp(earth_az.degrees, az, horizon, period=360)

    sunlit = sun_fraction(sun_alt.degrees - sun_horizon)    # 0 to 1
    earth_up = earth_alt.degrees > earth_horizon            # True/False
    dark = sunlit == 0

    # Power from a vertical panel that turns to face the Sun.
    sunlight = SOLAR_CONSTANT / sun_dist.au**2               # W per m^2
    facing = np.cos(np.radians(sun_alt.degrees))             # tilt loss
    power_w = sunlight * PANEL_AREA_M2 * PANEL_EFFICIENCY * sunlit * facing

    print()
    print(f'{site["name"]}: {days:g} days from {start:%Y-%m-%d %H:%M} UTC, '
          f"every {step:g} h")
    print(f"  Sunlit:                 {100 * sunlit.mean():5.1f} %")
    print(f"  Earth visible:          {100 * earth_up.mean():5.1f} %")
    print(f"  Sunlit AND Earth:       {100 * (sunlit * earth_up).mean():5.1f} %")
    print(f"  Longest darkness:       {longest_run(dark) * step:5.0f} hours "
          f"({longest_run(dark) * step / 24:.1f} days)")
    print(f"  Longest without Earth:  {longest_run(~earth_up) * step:5.0f} hours")
    print(f"  Panel power, average:   {power_w.mean():5.0f} W "
          f"({power_w.mean() * 24 / 1000:.2f} kWh per day)")
    print(f"  Panel power, peak:      {power_w.max():5.0f} W")
    print()
    print(f"  Terrain beyond {reach_km:.1f} km is not in the DEM, so it is not included.")


if __name__ == "__main__":
    main()