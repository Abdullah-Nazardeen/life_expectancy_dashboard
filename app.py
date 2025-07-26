# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

DATA_FILE = Path(__file__).with_name("life_expectancy.csv")

# ------------------------------------------------------------------ #
# 1.  Load & sanitise the dataset                                    #
# ------------------------------------------------------------------ #
@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_FILE.exists():
        st.error(f"❌  CSV not found at {DATA_FILE}. "
                 "Commit the file or change DATA_FILE.")
        st.stop()

    df = pd.read_csv(DATA_FILE)

    # Remove all leading / trailing whitespace in headers
    df.columns = df.columns.str.strip()

    # Canonical short names we’ll use everywhere else
    RENAMES = {
        "Life expectancy": "LifeExp",
        "BMI":              "BMI",
        "Hepatitis B":      "HepB",
        "Diphtheria":       "Diphtheria",
        "Polio":            "Polio",
        "GDP":              "GDP",
    }
    df.rename(columns={k: v for k, v in RENAMES.items() if k in df.columns},
              inplace=True)

    # Essential fields check
    essential = {"GDP", "Schooling", "LifeExp", "BMI",
                 "Alcohol", "Status", "Year"}
    missing = essential - set(df.columns)
    if missing:
        st.error(f"❌ Missing expected columns: {', '.join(missing)}")
        st.stop()

    # Derived metrics
    vacc_cols = [c for c in ("HepB", "Polio", "Diphtheria") if c in df.columns]
    df["VaccinationCoverage"] = df[vacc_cols].mean(axis=1, skipna=True)
    df["log_GDP"] = np.log10(df["GDP"].clip(lower=0) + 1)

    return df


df = load_data()

# ------------------------------------------------------------------ #
# 2.  Sidebar filters                                                #
# ------------------------------------------------------------------ #
st.sidebar.header("Filters")
status_opt   = st.sidebar.multiselect("Status", sorted(df.Status.unique()),
                                      default=sorted(df.Status.unique()))
year_range   = st.sidebar.slider("Year range",
                                 int(df.Year.min()), int(df.Year.max()),
                                 (2000, 2015))
countries    = st.sidebar.multiselect("Countries",
                                      sorted(df.Country.unique()))
gdp_range    = st.sidebar.slider("GDP / capita (US$)",
                                 float(df.GDP.min()), float(df.GDP.max()),
                                 (float(df.GDP.min()), float(df.GDP.max())))
hexp_range   = st.sidebar.slider("Health‑spend (% GDP)",
                                 float(df["percentage expenditure"].min()),
                                 float(df["percentage expenditure"].max()),
                                 (float(df["percentage expenditure"].min()),
                                  float(df["percentage expenditure"].max())))

mask = (
    df.Status.isin(status_opt)
    & df.Year.between(*year_range)
    & df.GDP.between(*gdp_range)
    & df["percentage expenditure"].between(*hexp_range)
)
if countries:
    mask &= df.Country.isin(countries)
data = df.loc[mask]

# ------------------------------------------------------------------ #
# 3.  Charts                                                         #
# ------------------------------------------------------------------ #
def bubble(x, y, title):
    return (alt.Chart(data)
            .mark_circle(opacity=0.45)
            .encode(
                x=x, y=y,
                size=alt.Size("Schooling", legend=None,
                              scale=alt.Scale(range=[10, 300])),
                tooltip=["Country", "Year", "GDP", "LifeExp"]
            )
            .properties(width=350, height=300, title=title)
            .interactive())

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(bubble("log_GDP", "LifeExp", "GDP vs Life Expectancy"))
    st.altair_chart(bubble("Schooling", "LifeExp", "Schooling vs Life Expectancy"))
with col2:
    st.altair_chart(bubble("BMI", "LifeExp", "BMI vs Life Expectancy"))
    st.altair_chart(bubble("Alcohol", "LifeExp", "Alcohol vs Life Expectancy"))
st.altair_chart(bubble("VaccinationCoverage", "LifeExp",
                       "Vaccination Coverage vs Life Expectancy"))

trend = (data.groupby(["Year", "Status"])["LifeExp"]
         .mean()
         .reset_index())
st.altair_chart(
    alt.Chart(trend)
    .mark_line(point=True)
    .encode(x="Year:O", y="LifeExp", color="Status")
    .properties(height=350, title="Average Life Expectancy over time")
)

# Top / bottom 10 in the newest available year within the filter
latest_year = data["Year"].max()
latest = data[data.Year == latest_year]
top10 = latest.groupby("Country")["LifeExp"].mean().nlargest(10)
bot10 = latest.groupby("Country")["LifeExp"].mean().nsmallest(10)

c1, c2 = st.columns(2)
c1.subheader(f"Top 10 – {latest_year}")
c1.dataframe(top10.round(1))
c2.subheader(f"Bottom 10 – {latest_year}")
c2.dataframe(bot10.round(1))

st.caption("Bubble size ∝ Schooling years – Data: WHO / UN 2000‑2015")

