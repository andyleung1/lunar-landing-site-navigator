from skyfield.api import PlanetaryConstants, load

from datetime import datetime, timezone
import numpy as np
from horizon import saved_horizon
from sites import get_sites

# 1. Load the data files (downloaded the first time)

ts = load.timescale()
eph = load("de421.bsp")
moon, sun, earth = eph["moon"], eph["sun"], eph["earth"]

pc = PlanetaryConstants()
pc.read_text(load("moon_080317.tf"))
pc.read_text(load("pck00008.tpc"))
pc.read_binary(load("moon_pa_de421_1900-2050.bpc"))
frame = pc.build_frame_named("MOON_ME_DE421")

SUN_RADIUS_DEG = 0.267

# 2. Let the user choose a site

def choose_site():
    sites = [s for s in get_sites() if s["lat"] is not None]
    print("Sites:")
    for number, s in enumerate(sites, start=1):
        print(f'  {number}. {s["name"]:20s} lat {s["lat"]:9.4f}  lon {s["lon"]:9.4f}')
    while True:
        answer = input("Choose a site number: ")
        if answer.isdigit() and 1 <= int(answer) <= len(sites):
            return sites[int(answer) - 1]
        print(f"Please type a number from 1 to {len(sites)}.")


# 3. Let the user choose the time(s)

def ask_start_time():
    while True:
        answer = input("Start time in UTC, as YYYY-MM-DD HH:MM (blank = now): ").strip()
        if answer == "":
            return datetime.now(timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
        try:
            return datetime.strptime(answer, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Couldn't read that. Example: 2026-11-14 15:30")


def ask_number(question, default):
    while True:
        answer = input(f"{question} (blank = {default}): ").strip()
        if answer == "":
            return default
        try:
            value = float(answer)
            if value > 0:
                return value
        except ValueError:
            pass
        print("Please type a positive number.")


def choose_times():
    start = ask_start_time()
    weeks = ask_number("How many weeks to cover", 52)
    step = ask_number("Weeks between rows", 1)

    # Offsets from the start in hours: 0, 1 step, 2 steps, ... up to `weeks`.
    # (There are 7 * 24 = 168 hours in a week.)
    count = int(weeks / step) + 1
    offsets = [i * step * 168 for i in range(count)]

    # Skyfield accepts a list of hours and rolls over into the next day/month.
    hour_list = [start.hour + start.minute / 60 + h for h in offsets]
    return ts.utc(start.year, start.month, start.day, hour_list)

# 4. Work out the Sun and Earth positions and print them 

def main():
    site = choose_site()
    times = choose_times()

    place = moon + pc.build_latlon_degrees(frame, site["lat"], site["lon"])

    sun_alt, sun_az, _ = place.at(times).observe(sun).apparent().altaz()
    earth_alt, earth_az, _ = place.at(times).observe(earth).apparent().altaz()

    # Terrain height in the direction of the Sun and Earth at each time.
    if site.get("dem"):
        print("Working out the terrain horizon from the DEM...")
        az, horizon, reach_km = saved_horizon(site)
        sun_terrain = np.interp(sun_az.degrees, az, horizon, period=360)
        earth_terrain = np.interp(earth_az.degrees, az, horizon, period=360)
        note = f"Terrain from the DEM, out to {reach_km:.1f} km (farther terrain not included)."
    else:
        sun_terrain = np.zeros(len(times))
        earth_terrain = np.zeros(len(times))
        note = "No DEM for this site, so the terrain is treated as FLAT (0 degrees)."

    print()
    print(f'{site["name"]}  (lat {site["lat"]:.4f}, lon {site["lon"]:.4f})')
    print("                    ------------- Sun -------------   ------------ Earth ------------")
    print("Time (UTC)          alt      az   terrain  visible     alt      az   terrain  visible")
    for i in range(len(times)):
        print(
            f"{times[i].utc_strftime('%Y-%m-%d %H:%M')}  "
            f"{sun_alt.degrees[i]:6.2f}  {sun_az.degrees[i]:6.1f}  {sun_terrain[i]:6.2f}   "
            f"{sun_visible(sun_alt.degrees[i], sun_terrain[i]):7s}  "
            f"{earth_alt.degrees[i]:6.2f}  {earth_az.degrees[i]:6.1f}  {earth_terrain[i]:6.2f}   "
            f"{'yes' if earth_alt.degrees[i] > earth_terrain[i] else 'no'}"
        )
    print("\nAngles in degrees. 'terrain' is how high the ground rises in that direction.")
    print(note)

def sun_visible(alt, terrain):
    """'yes' if the whole Sun is above the terrain, 'part' if some, 'no' if none."""
    if alt - terrain >= SUN_RADIUS_DEG:
        return "yes"
    if alt - terrain <= -SUN_RADIUS_DEG:
        return "no"
    return "part"

if __name__ == "__main__":
    main()