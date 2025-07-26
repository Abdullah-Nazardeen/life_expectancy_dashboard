# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

@st.cache_data
def load_data() -> pd.DataFrame:
    # 1) Load the file by its exact name
    try:
        df = pd.read_csv("life_expectancy.csv")
    except FileNotFoundError:
        st.error("❌ Could not find 'Life Expectancy Data.csv' in this folder.")
        st.stop()

    # 2) Strip ALL leading/trailing spaces from every header
    df.columns = df.columns.str.strip()

    # 3) Rename the life‑expectancy column for ease of use
    if "Life expectancy" in df.columns:
        df.rename(columns={"Life expectancy": "LifeExp"}, inplace=True)
    else:
        st.error("❌ Expected a column called 'Life expectancy ' (with trailing space) in the raw CSV.")
        st.stop()

    # 4) Verify that our core fields now exist exactly
    essential = {"GDP", "Schooling", "LifeExp", "BMI", "Alcohol", "Status", "Year"}
    missing = essential - set(df.columns)
    if missing:
        st.error(f"❌ Still missing columns after cleanup: {', '.join(missing)}")
        st.stop()

    # 5) Safe derivations
    df["VaccinationCoverage"] = df[["Hepatitis B", "Polio", "Diphtheria"]].mean(axis=1)
    df["log_GDP"] = np.log10(df["GDP"].clip(lower=0) + 1)

    return df

# Load & clean
df = load_data()

# ---------------------- Sidebar filters ----------------------
st.sidebar.header("Filters")
status_opt = st.sidebar.multiselect("Status", df.Status.unique(), default=list(df.Status.unique()))
year_min, year_max = st.sidebar.slider("Year range",
                                       int(df.Year.min()), int(df.Year.max()),
                                       (2000, 2015))
country_opt = st.sidebar.multiselect("Countries", df.Country.unique())
gdp_min, gdp_max = st.sidebar.slider("GDP per capita",
                                     float(df.GDP.min()), float(df.GDP.max()),
                                     (float(df.GDP.min()), float(df.GDP.max())))
hexp_min, hexp_max = st.sidebar.slider("Health‑spend (% GDP)",
                                       float(df["percentage expenditure"].min()),
                                       float(df["percentage expenditure"].max()),
                                       (float(df["percentage expenditure"].min()),
                                        float(df["percentage expenditure"].max())))

mask = (
    df.Status.isin(status_opt)
    & df.Year.between(year_min, year_max)
    & df.GDP.between(gdp_min, gdp_max)
    & df["percentage expenditure"].between(hexp_min, hexp_max)
)
if country_opt:
    mask &= df.Country.isin(country_opt)
data = df.loc[mask]

# ---------------------- Plotting helper ----------------------
def bubble(x, y, title):
    return (
        alt.Chart(data)
        .mark_circle(opacity=0.5)
        .encode(
            x=x,
            y=y,
            size=alt.Size("Schooling", legend=None, scale=alt.Scale(range=[10,300])),
            tooltip=["Country", "Year", "GDP", "LifeExp"]
        )
        .properties(width=350, height=300, title=title)
        .interactive()
    )

# ---------------------- Build the dashboard ----------------------
st.title("🌍 Life Expectancy Dashboard")

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(bubble("log_GDP", "LifeExp", "GDP vs Life Expectancy"))
    st.altair_chart(bubble("Schooling", "LifeExp", "Schooling vs Life Expectancy"))
with col2:
    st.altair_chart(bubble("BMI", "LifeExp", "BMI vs Life Expectancy"))
    st.altair_chart(bubble("Alcohol", "LifeExp", "Alcohol vs Life Expectancy"))

st.altair_chart(bubble("VaccinationCoverage", "LifeExp",
                       "Vaccination Coverage vs Life Expectancy"))

# Time trend
trend = (data.groupby(["Year", "Status"])["LifeExp"].mean().reset_index())
st.altair_chart(
    alt.Chart(trend)
    .mark_line(point=True)
    .encode(x="Year:O", y="LifeExp", color="Status")
    .properties(height=300, title="Life Expectancy Over Time")
)

# Top / bottom tables
latest_year = data.Year.max()
latest = data[data.Year == latest_year]
top10 = latest.groupby("Country")["LifeExp"].mean().nlargest(10)
bot10 = latest.groupby("Country")["LifeExp"].mean().nsmallest(10)

c1, c2 = st.columns(2)
c1.subheader(f"🏆 Top 10 – {latest_year}")
c1.dataframe(top10.round(1))
c2.subheader(f"🔻 Bottom 10 – {latest_year}")
c2.dataframe(bot10.round(1))

st.caption("🔹 Bubble size ∝ Schooling years · Data: WHO/UN (2000–2015)")
