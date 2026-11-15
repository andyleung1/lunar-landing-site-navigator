# app.py
# Streamlit app: sunlight, Earth visibility and solar power for any dates.
# streamlit run app.py
#
# The Sun/Earth positions are calculated for the dates you pick, then
# remembered, so going back to the same site and dates is instant.
# The terrain horizon is saved to a file (see horizon.py / precompute.py).

import datetime as dt
import math

import pandas as pd
import streamlit as st

from horizon import saved_horizon
from metrics import compute_table, make_times
from sites import get_sites
from terrain3d import viewer_html

EARLIEST = dt.date(1900, 1, 2)    # the NASA files cover 1900 to 2050
LATEST = dt.date(2050, 12, 31)
MAX_STEPS = 50_000                # about 5.7 years at 1-hour steps
MAX_CHART_POINTS = 1500           # more points than this makes the browser slow


@st.cache_data(show_spinner=False)
def site_list():
    return [s for s in get_sites() if s.get("lat") is not None]


@st.cache_data(show_spinner=False, max_entries=20)
def results(site, start, end, step_hours):
    """Sun/Earth table for one site and date range. Remembered (cached), so
    the same site and dates are only calculated once."""
    return compute_table(site, make_times(start, end, step_hours))


@st.cache_data(show_spinner=False, max_entries=10)
def terrain_view(dem_path, name, lat, lon):
    """HTML for the 3D terrain view of one site. Remembered (cached), so the
    DEM is only read and shrunk once per site."""
    return viewer_html(dem_path, name, lat, lon)


def show_html(html, height):
    """Show an HTML page inside the app. Newer Streamlit uses st.iframe;
    older versions use components.html."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)


def longest_run_hours(flags, step_hours):
    """Longest stretch of True values in a row, in hours."""
    if not flags.any():
        return 0.0
    stretch_id = (flags != flags.shift()).cumsum()   # new number at each change
    return flags.groupby(stretch_id).sum().max() * step_hours


def for_chart(table, step_hours):
    """Average rows into larger time blocks so a chart has at most
    MAX_CHART_POINTS points. The statistics still use every row."""
    rows_per_point = max(1, math.ceil(len(table) / MAX_CHART_POINTS))
    if rows_per_point == 1:
        return table
    return table.resample(f"{rows_per_point * step_hours}h").mean()


st.title("Lunar south pole: sunlight and Earth visibility")
sites = site_list()

# ---------- Sidebar: nothing recalculates until "Update" is pressed ----------
with st.sidebar.form("settings"):
    name = st.selectbox("Site", [s["name"] for s in sites])
    start = st.date_input("From", dt.date(2027, 1, 1), min_value=EARLIEST, max_value=LATEST)
    end = st.date_input("To", dt.date(2028, 1, 1), min_value=EARLIEST, max_value=LATEST)
    area = st.number_input("Panel area (m²)", 0.1, 100.0, 1.0, step=0.5)
    efficiency = st.slider("Panel efficiency (%)", 5, 40, 30) / 100
    st.form_submit_button("Update", type="primary")
st.sidebar.caption(f"Any dates from {EARLIEST} to {LATEST}. "
                   "The 'To' day is not included.")

if end <= start:
    st.error("'To' must be after 'From'.")
    st.stop()

site = next(s for s in sites if s["name"] == name)

# Long ranges use bigger steps so the calculation stays quick.
total_hours = (end - start).days * 24
step = max(1, math.ceil(total_hours / MAX_STEPS))

with st.spinner(f"Calculating {name}, {start} to {end}..."):
    try:
        df = results(site, start, end, step)
    except Exception as e:
        st.error(f"Couldn't calculate for these dates: {e}")
        st.stop()

power = df["panel_w_per_m2"] * area * efficiency
dark = df["sunlit"] == 0

st.caption(f'lat {site["lat"]:.4f}, lon {site["lon"]:.4f} · {start} to {end} · '
           f"{len(df)} time steps, every {step} h")
if step > 1:
    st.warning(f"This range is long, so it uses {step}-hour steps instead of 1-hour. "
               f"'Longest darkness' is accurate to about {step} hours.")

c1, c2, c3 = st.columns(3)
c1.metric("Sunlit", f'{100 * df["sunlit"].mean():.1f} %')
c2.metric("Earth visible", f'{100 * df["earth_up"].mean():.1f} %')
c3.metric("Sunlit and Earth", f'{100 * (df["sunlit"] * df["earth_up"]).mean():.1f} %')

c4, c5, c6 = st.columns(3)
c4.metric("Longest darkness", f"{longest_run_hours(dark, step) / 24:.1f} days")
c5.metric("Average power", f"{power.mean():.0f} W")
c6.metric("Energy per day", f"{power.mean() * 24 / 1000:.2f} kWh")

# ---------- Charts (thinned so the browser stays fast) ----------
chart = df.set_index("time")[["sun_alt", "sun_terrain", "earth_alt", "earth_terrain"]]
chart = for_chart(chart.assign(power_w=power.values), step)
if len(chart) < len(df):
    st.caption(f"Charts show averages over {step * len(df) / len(chart):.0f}-hour blocks "
               "to stay responsive. The numbers above use every time step.")

st.subheader("Sun height vs terrain")
st.line_chart(chart[["sun_alt", "sun_terrain"]])

st.subheader("Earth height vs terrain")
st.line_chart(chart[["earth_alt", "earth_terrain"]])

st.subheader("Panel power (W)")
st.line_chart(chart["power_w"])

if site.get("dem"):
    az, terrain, reach_km = saved_horizon(site)
    st.subheader("Terrain horizon")
    st.line_chart(pd.DataFrame({"terrain": terrain}, index=pd.Index(az, name="azimuth")))
    st.caption(f"Terrain beyond {reach_km:.1f} km is not in the DEM.")

    st.subheader("3D terrain")
    try:
        show_html(terrain_view(str(site["dem"]), name, site["lat"], site["lon"]), height=600)
    except Exception as e:
        st.warning(f"Couldn't build the 3D view for this site: {e}")
else:
    st.info("No DEM for this site: terrain treated as flat.")
