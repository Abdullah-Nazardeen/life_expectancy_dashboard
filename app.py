# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="centered", page_title="Life Expectancy Demo")

# ──────────────────────────────────────────────
# 1. Load data (CSV placed in same repo)
# ──────────────────────────────────────────────
df = pd.read_csv("life_expectancy.csv")

# ──────────────────────────────────────────────
# 2. Scatter – GDP vs Life Expectancy (latest year)
# ──────────────────────────────────────────────
latest_year = int(df["year"].max())
latest = df[df["year"] == latest_year]

st.subheader(f"GDP vs Life Expectancy – {latest_year}")
scatter = px.scatter(
    latest,
    x="gdp",
    y="life_expectancy",
    hover_name="country",
    opacity=0.6,
    labels={"gdp": "GDP per capita (USD)", "life_expectancy": "Life Expectancy (yrs)"},
)
st.plotly_chart(scatter, use_container_width=True)

# ──────────────────────────────────────────────
# 3. Line – Global average life expectancy trend
# ──────────────────────────────────────────────
trend = (
    df.groupby("year")["life_expectancy"]
    .mean()
    .reset_index(name="avg_life_expectancy")
)

st.subheader("Global Average Life Expectancy Trend")
line = px.line(
    trend,
    x="year",
    y="avg_life_expectancy",
    markers=True,
    labels={"avg_life_expectancy": "Avg Life Expectancy (yrs)"},
)
st.plotly_chart(line, use_container_width=True)

# (Optional) show raw data
with st.expander("🔍  Inspect dataset"):
    st.dataframe(df.head())
