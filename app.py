import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

###############################################################################
# 1. DATA LOADING  (cached so repeated filter changes feel instantaneous)
###############################################################################
@st.cache_data
def load_data(csv_path: str = "life_expectancy.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Clean some column names just in case
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

df = load_data()

###############################################################################
# 2. SIDEBAR – GLOBAL FILTERS
###############################################################################
st.sidebar.title("🔍 Filters")

# Year slider (single‑select for the document’s charts, default=2015)
min_year, max_year = int(df.year.min()), int(df.year.max())
year = st.sidebar.slider("Year", min_year, max_year, 2015)

# Development status filter
status_options = df.status.unique().tolist()
status_sel = st.sidebar.multiselect("Development status", status_options, status_options)

# Country filter (optional multi‑select)
all_countries = df.country.unique().tolist()
country_sel = st.sidebar.multiselect("Country (optional)", all_countries)

# Filter the dataframe
mask = (df.year == year) & (df.status.isin(status_sel))
if country_sel:
    mask &= df.country.isin(country_sel)
df_year = df[mask]

###############################################################################
# 3. KPI CARDS
###############################################################################
st.title("🌍 Global Life‑Expectancy Dashboard")
st.caption("Interactive analytics board (Streamlit + Plotly)")

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric("Average Life‑Expectancy (yrs)", f"{df_year.life_expectancy.mean():.1f}")

with kpi_cols[1]:
    best_country = df_year.loc[df_year.life_expectancy.idxmax(), "country"]
    best_val = df_year.life_expectancy.max()
    st.metric("Highest Country", f"{best_val:.1f}", best_country)

with kpi_cols[2]:
    worst_country = df_year.loc[df_year.life_expectancy.idxmin(), "country"]
    worst_val = df_year.life_expectancy.min()
    st.metric("Lowest Country", f"{worst_val:.1f}", worst_country)

with kpi_cols[3]:
    gdp_mean = df_year.gdp.mean() / 1_000  # ‘000 USD for readability
    st.metric("Avg GDP per Capita\n(×$1 000)", f"{gdp_mean:.1f}")

st.divider()

###############################################################################
# 4. CHARTS (organised in tabs)
###############################################################################
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Top‑10 Countries", "Status Box‑plot", "GDP Scatter", "Trend (2000‑15)", "Schooling Scatter"]
)

# --- Tab 1 – Top‑10 bar ------------------------------------------------------
with tab1:
    st.subheader(f"🏅 Top‑10 Countries by Life‑Expectancy – {year}")
    top10 = (
        df[df.year == year]
        .nlargest(10, "life_expectancy")
        .sort_values("life_expectancy")
    )
    fig = px.bar(
        top10,
        x="life_expectancy",
        y="country",
        orientation="h",
        color="life_expectancy",
        color_continuous_scale="Blues",
        labels={"life_expectancy": "Years", "country": ""},
    )
    fig.update_layout(height=500, yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 2 – Box & Whisker ---------------------------------------------------
with tab2:
    st.subheader(f"📦 Life‑Expectancy by Development Status – {year}")
    fig = px.box(
        df[df.year == year],
        x="status",
        y="life_expectancy",
        color="status",
        points="all",
        labels={"life_expectancy": "Years", "status": ""},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 3 – GDP Scatter -----------------------------------------------------
with tab3:
    st.subheader(f"💰 GDP vs Life‑Expectancy – {year}")
    fig = px.scatter(
        df[df.year == year],
        x="gdp",
        y="life_expectancy",
        color="status",
        hover_name="country",
        size="population",
        log_x=True,
        labels={"gdp": "GDP per Capita (log‑scale USD)", "life_expectancy": "Years"},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 4 – 2000‑2015 Trend -------------------------------------------------
with tab4:
    st.subheader("📈 Global Trend 2000‑2015 (Developed vs Developing)")
    trend_df = (
        df[df.status.isin(status_sel)]
        .groupby(["year", "status"], as_index=False)["life_expectancy"]
        .mean()
    )
    fig = px.line(
        trend_df,
        x="year",
        y="life_expectancy",
        color="status",
        markers=True,
        labels={"life_expectancy": "Avg Life‑Expectancy (yrs)", "year": ""},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 5 – Schooling vs Life‑Expectancy ------------------------------------
with tab5:
    st.subheader(f"🎓 Schooling vs Life‑Expectancy – {year}")
    fig = px.scatter(
        df[df.year == year],
        x="schooling",
        y="life_expectancy",
        trendline="ols",
        color="status",
        hover_name="country",
        labels={"schooling": "Average Years of Schooling", "life_expectancy": "Years"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
with st.expander("About this dashboard"):
    st.markdown(
        """
*Data source:* `life_expectancy.csv` (WHO & World‑Bank compiled).  
Charts reproduced from the documentation you supplied and re‑implemented with Plotly for full interactivity inside Streamlit.
"""
    )
