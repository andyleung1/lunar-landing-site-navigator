# precompute.py
# Optional warm-up: works out and saves the terrain horizon for every site
# that has a DEM. That is the slowest step, so doing it here means the
# Streamlit app doesn't have to do it the first time someone picks a site.
# 
# the app works sun and earth positions for whatever dates you choose, and remembers recent results.
#
# python precompute.py

from horizon import saved_horizon
from sites import get_sites


def main():
    for site in get_sites():
        if not site.get("dem"):
            print(f'{site["name"]}: no DEM, nothing to precompute.')
            continue
        print(f'{site["name"]}: working out the terrain horizon...')
        _, _, reach_km = saved_horizon(site)
        print(f"  done (DEM reaches {reach_km:.1f} km).")


if __name__ == "__main__":
    main()