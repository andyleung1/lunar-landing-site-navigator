# theme.py
# Dark navy look with blue accents: rounded outlined panels, small-caps
# title, uppercase section headers. Colours also set in .streamlit/config.toml.

import streamlit as st

BLUE = "#2f6fed"
GREY = "#6b7185"
LIGHT_BLUE = "#7fa8ff"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600&display=swap');

:root {
  --bg: #0e1018;
  --panel: #161a27;
  --line: #343a4f;
  --text: #c9cdd8;
  --muted: #6b7185;
  --blue: #2f6fed;
  --navy: #1d3a7a;
}

html, body, [class*="css"], .stApp, .stMarkdown, input, select, textarea, button {
  font-family: 'Open Sans', sans-serif !important;
}

/* Title: small caps, thin, second word in blue */
.lunar-title {
  text-align: center;
  font-variant: small-caps;
  font-weight: 300;
  font-size: 2.1rem;
  letter-spacing: 0.06em;
  color: #e3e6ee;
  margin: 0.2rem 0 0.1rem;
}
.lunar-title span { color: var(--blue); }
.lunar-sub {
  text-align: center;
  color: var(--muted);
  font-size: 0.85rem;
  margin-bottom: 1.2rem;
}

/* Section headers: uppercase blue with underline, like a tab */
h3 {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.95rem !important;
  font-weight: 600 !important;
  color: var(--blue) !important;
  border-bottom: 2px solid var(--blue);
  display: inline-block;
  padding-bottom: 0.15rem !important;
  margin-top: 1.2rem !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--panel);
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] [data-testid="stForm"] {
  border: none;
  padding: 0;
}

/* Every input sits in a rounded outlined box */
[data-testid="stSidebar"] [data-testid="stSelectbox"],
[data-testid="stSidebar"] [data-testid="stDateInput"],
[data-testid="stSidebar"] [data-testid="stNumberInput"],
[data-testid="stSidebar"] [data-testid="stSlider"] {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.45rem 0.8rem 0.55rem;
  background: var(--bg);
}
[data-testid="stWidgetLabel"] p {
  color: var(--muted) !important;
  font-size: 0.78rem !important;
}
[data-baseweb="select"] > div,
[data-baseweb="input"],
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
  background: transparent !important;
  border-color: transparent !important;
}

/* Pill buttons */
.stButton button, [data-testid="stFormSubmitButton"] button {
  background: var(--navy) !important;
  border: 1px solid var(--navy) !important;
  color: #e3e6ee !important;
  border-radius: 999px !important;
  padding: 0.35rem 1.6rem !important;
  display: block;
  margin: 0.4rem auto 0;
}
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
  background: var(--blue) !important;
  border-color: var(--blue) !important;
}

/* Metrics as outlined cards */
[data-testid="stMetric"] {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.6rem 1rem;
  background: var(--panel);
}
[data-testid="stMetricLabel"] p {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem !important;
  color: var(--muted) !important;
}
[data-testid="stMetricValue"] { color: #e3e6ee; font-weight: 300; }

/* Charts and iframes in the same outlined panels */
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"], iframe {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.5rem;
  background: var(--panel);
}

/* Captions and alerts */
[data-testid="stCaptionContainer"] { color: var(--muted) !important; }
[data-testid="stAlert"] { border-radius: 12px; }
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def title(first, second, subtitle=""):
    """Small-caps title with the second part in blue."""
    st.markdown(f'<div class="lunar-title">{first} <span>{second}</span></div>',
                unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="lunar-sub">{subtitle}</div>', unsafe_allow_html=True)
