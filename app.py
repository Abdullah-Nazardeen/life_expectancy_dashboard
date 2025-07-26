# --------------------------------------------
# Life‑Expectancy Storyboard – Streamlit 1.x
# --------------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
from pathlib import Path

st.set_page_config(
    page_title="Global Life‑Expectancy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Load & prepare data ----------
DATA_PATH = Path(__file__).parent / "life_expectancy.csv"
df = pd.read_csv(DATA_PATH)

# Baseline GDP → life‑expectancy model (for residuals & KPI)
g_coef = np.polyfit(np.log1p(df["gdp"]), df["life_expectancy"], 1)
df["pred_le"] = g_coef[0] * np.log1p(df["gdp"]) + g_coef[1]
df["residual_le"] = df["life_expectancy"] - df["pred_le"]

YEARS = sorted(df["year"].unique())
COUNTRIES = sorted(df["country"].unique())
STATUSES = df["status"].unique()

# ---------- Sidebar filters ----------
st.sidebar.header("🎛️ Filters")
year_range = st.sidebar.slider(
    "Year range", int(min(YEARS)), int(max(YEARS)),
    (int(min(YEARS)), int(max(YEARS))), step=1
)
status_sel = st.sidebar.multiselect(
    "Country status", STATUSES, default=list(STATUSES)
)
country_sel = st.sidebar.multiselect(
    "Select countries (optional)", COUNTRIES
)

df_filt = df.query(
    " @year_range[0] <= year <= @year_range[1] "
    " and status in @status_sel "
)
if country_sel:
    df_filt = df_filt[df_filt["country"].isin(country_sel)]

# ---------- KPI row ----------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
avg_le = df_filt["life_expectancy"].mean()
avg_gdp = df_filt["gdp"].median()
gap_le = (
    df_filt.groupby("status")["life_expectancy"].mean().diff().iloc[-1]
    if len(status_sel) == 2 else np.nan
)
num_countries = df_filt["country"].nunique()

kpi1.metric("Avg Life Expectancy", f"{avg_le:,.1f} yrs")
kpi2.metric("Median GDP / capita", f"${avg_gdp:,.0f}")
kpi3.metric("Gap Developed – Developing",
            f"{gap_le:+.1f} yrs" if not np.isnan(gap_le) else "–")
kpi4.metric("Countries in view", f"{num_countries}")

st.markdown("---")

# ---------- 1. GDP vs Life Expectancy ----------
st.subheader("Income and Longevity")
fig_inc = px.scatter(
    df_filt,
    x="gdp", y="life_expectancy",
    color="status", opacity=0.35,
    template="plotly_white",
    labels={"gdp": "GDP per capita (USD)",
            "life_expectancy": "Life Expectancy (years)"},
    trendline="lowess", trendline_color_override="black"
)
fig_inc.update_traces(marker=dict(size=6))
fig_inc.update_layout(yaxis=dict(range=[35, 90]))
st.plotly_chart(fig_inc, use_container_width=True)

# ---------- 2. Schooling vs Life Expectancy ----------
st.subheader("Education and Longevity")
fig_sch = px.scatter(
    df_filt, x="schooling", y="life_expectancy",
    color="status", opacity=0.35, template="plotly_white",
    labels={"schooling": "Average years of schooling"}
)
# add regression line
slope, intercept, *_ = stats.linregress(df_filt["schooling"],
                                        df_filt["life_expectancy"])
x_line = np.linspace(df_filt["schooling"].min(),
                     df_filt["schooling"].max(), 100)
fig_sch.add_scatter(x=x_line, y=slope * x_line + intercept,
                    mode="lines", name="Trend",
                    line=dict(color="black", width=2))
fig_sch.update_traces(marker=dict(size=6), selector=dict(mode="markers"))
st.plotly_chart(fig_sch, use_container_width=True)

# ---------- 3. Schooling vs Residuals ----------
with st.expander("Does education help beyond income?"):
    fig_res = px.scatter(
        df_filt, x="schooling", y="residual_le",
        color="status", opacity=0.35, template="plotly_white",
        labels={"schooling": "Years of schooling",
                "residual_le": "Residual life expectancy (yrs)"}
    )
    fig_res.add_hline(0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_res, use_container_width=True)

# ---------- 4. BMI vs Residual Life Expectancy ----------
st.subheader("BMI and Longevity (net of income)")
fig_bmi = px.scatter(
    df_filt, x="bmi", y="residual_le",
    color="status", opacity=0.35, template="plotly_white",
    labels={"bmi": "Average BMI",
            "residual_le": "Residual life expectancy (yrs)"}
)
fig_bmi.add_hline(0, line_dash="dash", line_color="black")
st.plotly_chart(fig_bmi, use_container_width=True)

# ---------- 5. Alcohol vs Life Expectancy ----------
with st.expander("Alcohol Consumption"):
    fig_alc = px.scatter(
        df_filt, x="alcohol", y="life_expectancy",
        color="status", opacity=0.35, template="plotly_white",
        labels={"alcohol": "L pure alcohol / adult"}
    )
    st.plotly_chart(fig_alc, use_container_width=True)

# ---------- 6. Vaccination vs Life Expectancy ----------
st.subheader("Vaccination Coverage and Longevity (≥ 20 %)")
vacc = df_filt[df_filt["diphtheria"] >= 20]
fig_vac = px.scatter(
    vacc, x="diphtheria", y="life_expectancy",
    color="status", opacity=0.35, template="plotly_white",
    labels={"diphtheria": "DTP3 immunisation (%)"}
)
st.plotly_chart(fig_vac, use_container_width=True)

# ---------- 7. Trend over time ----------
st.subheader("2000 – 2015 Progress")
trend = (
    df_filt.groupby(["year", "status"])["life_expectancy"]
    .mean().reset_index()
)
fig_trend = px.line(
    trend, x="year", y="life_expectancy",
    color="status", markers=True, template="plotly_white",
    labels={"life_expectancy": "Life Expectancy (years)"}
)
st.plotly_chart(fig_trend, use_container_width=True)

# ---------- 8. Top & Bottom 10 Countries ----------
st.subheader(f"Leaders and Laggards in {int(year_range[1])}")
latest = df_filt[df_filt["year"] == year_range[1]]
top10 = latest.nlargest(10, "life_expectancy")[["country", "life_expectancy"]]
bot10 = latest.nsmallest(10, "life_expectancy")[["country", "life_expectancy"]]

col_top, col_bot = st.columns(2)
with col_top:
    st.markdown("##### 🏆 Top 10")
    st.dataframe(top10.set_index("country"), height=320)
with col_bot:
    st.markdown("##### 🚨 Bottom 10")
    st.dataframe(bot10.set_index("country"), height=320)

st.caption("Colours: muted teal & soft tomato ensure good contrast on projectors.")
