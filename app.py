import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

@st.cache_data
def load_data() -> pd.DataFrame:
    # --- locate the CSV robustly ---
    possible = [
        Path("Life Expectancy Data.csv"),
        Path("life_expectancy.csv"),
        *Path(".").glob("**/*Life*Expectancy*.csv"),
    ]
    for p in possible:
        if p.exists():
            df = pd.read_csv(p)
            break
    else:
        st.error("❌ CSV file not found. Check the file name.")
        st.stop()

    # --- clean column names ---
    df.columns = df.columns.str.strip()           # drop leading/trailing spaces
    df.rename(columns={"Life expectancy": "LifeExp"}, inplace=True)

    # --- derived fields ---
    vax_cols = {"Hepatitis B", "Polio", "Diphtheria"} & set(df.columns)
    df["VaccinationCoverage"] = df[list(vax_cols)].mean(1, skipna=True)

    df["log_GDP"] = np.log10(df["GDP"].clip(lower=0) + 1)
    return df

df = load_data()

# ------------------------ SIDEBAR FILTERS ------------------------
st.sidebar.header("Filters")
status_sel  = st.sidebar.multiselect("Country status", df["Status"].unique(),
                                     default=list(df["Status"].unique()))
year_sel    = st.sidebar.slider("Year", int(df.Year.min()), int(df.Year.max()),
                                (2000, 2015))
country_sel = st.sidebar.multiselect("Countries", sorted(df.Country.unique()))
gdp_sel = st.sidebar.slider("GDP per capita (US$)",
                            float(df.GDP.min()), float(df.GDP.max()),
                            (float(df.GDP.min()), float(df.GDP.max())))
hexp_sel = st.sidebar.slider("Health‑spend (% GDP)",
                             float(df["percentage expenditure"].min()),
                             float(df["percentage expenditure"].max()),
                             (float(df["percentage expenditure"].min()),
                              float(df["percentage expenditure"].max())))

mask = (
    df.Status.isin(status_sel) &
    df.Year.between(*year_sel) &
    df.GDP.between(*gdp_sel) &
    df["percentage expenditure"].between(*hexp_sel)
)
if country_sel:
    mask &= df.Country.isin(country_sel)
data = df.loc[mask]

# ------------------------ PLOTS ------------------------
def scatter(x, y, title):
    return (alt.Chart(data)
            .mark_circle(opacity=0.45)
            .encode(x=x, y=y,
                    size=alt.Size("Schooling", legend=None,
                                  scale=alt.Scale(range=[10, 300])),
                    tooltip=["Country", "Year", "GDP", "LifeExp"])
            .interactive()
            .properties(width=350, height=300, title=title))

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(scatter("log_GDP", "LifeExp",
                            "GDP vs Life expectancy"))
    st.altair_chart(scatter("Schooling", "LifeExp",
                            "Schooling vs Life expectancy"))
with col2:
    st.altair_chart(scatter("BMI", "LifeExp",
                            "BMI vs Life expectancy"))
    st.altair_chart(scatter("Alcohol", "LifeExp",
                            "Alcohol vs Life expectancy"))
st.altair_chart(scatter("VaccinationCoverage", "LifeExp",
                        "Vaccination coverage vs Life expectancy"))

# Time‑trend
trend = (data.groupby(["Year", "Status"])["LifeExp"]
         .mean()
         .reset_index())
st.altair_chart(
    alt.Chart(trend).mark_line(point=True)
    .encode(x="Year:O", y="LifeExp", color="Status")
    .properties(height=350, title="Average life expectancy over time")
)

# League tables for latest selected year
latest_year = data["Year"].max()
latest = data[data.Year == latest_year]
top10 = latest.groupby("Country")["LifeExp"].mean().nlargest(10)
bot10 = latest.groupby("Country")["LifeExp"].mean().nsmallest(10)

c1, c2 = st.columns(2)
c1.subheader(f"Top 10 (LifeExp) – {latest_year}")
c1.dataframe(top10.round(1))
c2.subheader(f"Bottom 10 (LifeExp) – {latest_year}")
c2.dataframe(bot10.round(1))

st.caption("Bubble size ∝ schooling years · Data source: WHO / UN 2000‑2015")

