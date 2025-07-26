import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

@st.cache_data
def load_data():
    df = pd.read_csv("life_expectancy.csv")          # <- repo file name
    df.columns = df.columns.str.strip()              # remove trailing spaces
    df["VaccinationCoverage"] = df[["Hepatitis B", "Polio", "Diphtheria"]].mean(1)
    df["log_GDP"] = np.log10(df["GDP"] + 1)
    return df

df = load_data()

# ---------- SIDEBAR FILTERS ----------
st.sidebar.header("Filters")

status_sel   = st.sidebar.multiselect("Country status", df["Status"].unique(), default=list(df["Status"].unique()))
year_sel     = st.sidebar.slider("Year", int(df.Year.min()), int(df.Year.max()), (2000, 2015))
country_sel  = st.sidebar.multiselect("Countries", sorted(df.Country.unique()), default=[])
gdp_sel      = st.sidebar.slider("GDP per capita (USD)", float(df.GDP.min()), float(df.GDP.max()), (float(df.GDP.min()), float(df.GDP.max())))
hexp_sel     = st.sidebar.slider("Health‑spend (% GDP)", float(df["percentage expenditure"].min()),
                                 float(df["percentage expenditure"].max()),
                                 (float(df["percentage expenditure"].min()),
                                  float(df["percentage expenditure"].max())))

mask = (
    df.Status.isin(status_sel)
    & df.Year.between(*year_sel)
    & df.GDP.between(*gdp_sel)
    & df["percentage expenditure"].between(*hexp_sel)
)

if country_sel:
    mask &= df.Country.isin(country_sel)

data = df[mask]

# ---------- LAYOUT ----------
st.title("🌍  Life‑Expectancy Explorer (2000 – 2015)")

def scatter(x, y, tooltip, title):
    return (
        alt.Chart(data)
        .mark_circle(opacity=0.4)
        .encode(
            x=x, y=y,
            size=alt.Size("Schooling", legend=None, scale=alt.Scale(range=[10,300])),
            tooltip=tooltip,
        )
        .interactive()
        .properties(height=350, title=title)
    )

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(scatter("log_GDP", "Life expectancy", ["Country", "Year"], "GDP vs Life expectancy") )
    st.altair_chart(scatter("Schooling", "Life expectancy", ["Country", "Year"], "Schooling vs Life expectancy"))

with col2:
    st.altair_chart(scatter("BMI", "Life expectancy", ["Country", "Year"], "BMI vs Life expectancy"))
    st.altair_chart(scatter("Alcohol", "Life expectancy", ["Country", "Year"], "Alcohol vs Life expectancy") )

st.altair_chart(
    scatter("VaccinationCoverage", "Life expectancy", ["Country", "Year"], "Vaccination coverage vs Life expectancy")
)

# ----- Trend line -----
trend = (
    data.groupby(["Year", "Status"])["Life expectancy"].mean().reset_index()
)
line = (
    alt.Chart(trend)
    .mark_line(point=True)
    .encode(x="Year:O", y="Life expectancy", color="Status")
    .properties(height=350, title="Average life expectancy over time")
)
st.altair_chart(line)

# ----- Top / Bottom tables -----
latest = data[data.Year == data.Year.max()]
top10    = latest.groupby("Country")["Life expectancy"].mean().nlargest(10)
bottom10 = latest.groupby("Country")["Life expectancy"].mean().nsmallest(10)

col1, col2 = st.columns(2)
col1.subheader("Top 10 countries")
col1.dataframe(top10.round(1))
col2.subheader("Bottom 10 countries")
col2.dataframe(bottom10.round(1))

st.caption("Bubble size ∝ schooling years · Data: WHO, UN, World Bank (2000‑2015)")

