# --------------------------------------------
# Life‑Expectancy Storyboard – Streamlit 1.x
# tabs + info accordions
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

# ---------- Theme ----------
THEME_COLORS = ["#006d77", "#ff595e"]  # high‑contrast teal & tomato

# ---------- Data ----------
DATA_PATH = Path(__file__).parent / "life_expectancy.csv"
df = pd.read_csv(DATA_PATH)

coef = np.polyfit(np.log1p(df["gdp"]), df["life_expectancy"], 1)
df["pred_le"] = coef[0] * np.log1p(df["gdp"]) + coef[1]
df["residual_le"] = df["life_expectancy"] - df["pred_le"]

YEARS, STATUSES, COUNTRIES = (
    sorted(df["year"].unique()),
    df["status"].unique(),
    sorted(df["country"].unique())
)

# ---------- Sidebar ----------
st.sidebar.header("🎛️ Filters")
year_range = st.sidebar.slider(
    "Year range", int(min(YEARS)), int(max(YEARS)),
    (int(min(YEARS)), int(max(YEARS)))
)
status_sel = st.sidebar.multiselect("Country status", STATUSES, STATUSES)
country_sel = st.sidebar.multiselect("Countries (optional)", COUNTRIES)

df_filt = df.query(
    "@year_range[0] <= year <= @year_range[1] and status in @status_sel"
)
if country_sel:
    df_filt = df_filt[df_filt["country"].isin(country_sel)]

# ---------- KPI row ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Life Expectancy", f"{df_filt['life_expectancy'].mean():.1f} yrs")
col2.metric("Median GDP / capita", f"${df_filt['gdp'].median():,.0f}")
gap = (
    df_filt.groupby("status")["life_expectancy"].mean().diff().iloc[-1]
    if len(status_sel) == 2 else np.nan
)
col3.metric("Gap Dev–Dev", f"{gap:+.1f} yrs" if not np.isnan(gap) else "–")
col4.metric("Countries in view", f"{df_filt['country'].nunique()}")

st.markdown("---")

# ---------- Tabs ----------
tabs = st.tabs([
    "Income ↔ Longevity", "Education ↔ Longevity", "Schooling Residual",
    "BMI Residual", "Alcohol", "Vaccination", "Time Trend",
    "Leaders / Laggards"
])

# ---- Helper to append expander text ----
def add_expander(tab_container, summary_text):
    with tab_container.expander("What does this show?"):
        st.write(summary_text)

# 1️⃣ Income vs Longevity -----------------
with tabs[0]:
    fig = px.scatter(
        df_filt, x="gdp", y="life_expectancy",
        color="status", color_discrete_sequence=THEME_COLORS,
        opacity=0.35, template="plotly_white",
        labels={
            "gdp": "GDP per capita (USD, current)",
            "life_expectancy": "Life Expectancy (years)"
        },
        trendline="lowess", trendline_scope="overall"
    )
    fig.update_traces(marker=dict(size=6))
    fig.update_layout(yaxis_range=[35, 90], legend_title="Status")
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "The LOWESS curve reveals the classic Preston‑style saturation: "
        "longevity rises steeply with income up to about $10 k, then gains taper."
    )

# 2️⃣ Education vs Longevity --------------
with tabs[1]:
    fig = px.scatter(
        df_filt, x="schooling", y="life_expectancy",
        color="status", color_discrete_sequence=THEME_COLORS,
        opacity=0.35, template="plotly_white",
        labels={
            "schooling": "Average Years of Schooling",
            "life_expectancy": "Life Expectancy (years)"
        }
    )
    m, b, *_ = stats.linregress(df_filt["schooling"],
                                df_filt["life_expectancy"])
    x_line = np.linspace(df_filt["schooling"].min(),
                         df_filt["schooling"].max(), 100)
    fig.add_scatter(x=x_line, y=m * x_line + b,
                    mode="lines", name="Trend",
                    line=dict(color="black", width=2))
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "Each extra year of schooling correlates with ≈ 2.3 additional "
        "years of life expectancy, highlighting education as a key lever."
    )

# 3️⃣ Schooling vs Residual ---------------
with tabs[2]:
    fig = px.scatter(
        df_filt, x="schooling", y="residual_le",
        color="status", color_discrete_sequence=THEME_COLORS,
        opacity=0.35, template="plotly_white",
        labels={
            "schooling": "Years of Schooling",
            "residual_le": "Residual Life Expectancy (yrs)"
        }
    )
    fig.add_hline(0, line_dash="dash", line_color="black")
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "Positive residuals mean a country outperforms the GDP‑only model. "
        "Higher schooling shifts nations above zero, showing education "
        "delivers a health dividend even after accounting for income."
    )

# 4️⃣ BMI vs Residual ---------------------
with tabs[3]:
    fig = px.scatter(
        df_filt, x="bmi", y="residual_le",
        color="status", color_discrete_sequence=THEME_COLORS,
        opacity=0.35, template="plotly_white",
        labels={
            "bmi": "Average BMI",
            "residual_le": "Residual Life Expectancy (yrs)"
        }
    )
    fig.add_hline(0, line_dash="dash", line_color="black")
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "Both under‑nutrition (low BMI) and obesity (very high BMI) sit below "
        "the zero line, underscoring the importance of balanced nutrition."
    )

# 5️⃣ Alcohol -----------------------------
with tabs[4]:
    fig = px.scatter(
        df_filt, x="alcohol", y="life_expectancy",
        color="status", color_discrete_sequence=THEME_COLORS,
        opacity=0.35, template="plotly_white",
        labels={
            "alcohol": "Litres of Pure Alcohol per Adult",
            "life_expectancy": "Life Expectancy (years)"
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "The upward pattern is driven by wealth: richer countries both drink "
        "more and live longer. Income, not alcohol, explains the apparent link."
    )

# 6️⃣ Vaccination -------------------------
with tabs[5]:
    vacc = df_filt[df_filt["diphtheria"] >= 20]
    fig = px.scatter(
        vacc, x="diphtheria", y="life_expectancy",
        color="status", color_discrete_sequence=THEME_COLORS,
        opacity=0.35, template="plotly_white",
        labels={
            "diphtheria": "DTP3 Immunisation Coverage (%)",
            "life_expectancy": "Life Expectancy (years)"
        },
        trendline="lowess", trendline_scope="overall",
        trendline_color_override="black"
    )
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "Once coverage exceeds ~60 %, life expectancy climbs sharply and "
        "plateaus around 75 – 80 years, showing vaccines are a prerequisite "
        "for high longevity."
    )

# 7️⃣ Time Trend --------------------------
with tabs[6]:
    trend = (
        df_filt.groupby(["year", "status"])["life_expectancy"]
        .mean().reset_index()
    )
    fig = px.line(
        trend, x="year", y="life_expectancy",
        color="status", color_discrete_sequence=THEME_COLORS,
        markers=True, template="plotly_white",
        labels={
            "year": "Year",
            "life_expectancy": "Mean Life Expectancy (years)"
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    add_expander(
        st,
        "Both groups gained ≈ 4–5 years from 2000 to 2015, yet a "
        "12‑year gap persists between developed and developing countries."
    )

# 8️⃣ Leaders & Laggards ------------------
with tabs[7]:
    latest = df_filt[df_filt["year"] == year_range[1]]
    top10 = latest.nlargest(10, "life_expectancy")\
                  [["country", "life_expectancy"]]\
                  .set_index("country")
    bot10 = latest.nsmallest(10, "life_expectancy")\
                  [["country", "life_expectancy"]]\
                  .set_index("country")
    col_top, col_bot = st.columns(2)
    col_top.markdown("#### 🏆 Top 10")
    col_top.dataframe(top10, height=340)
    col_bot.markdown("#### 🚨 Bottom 10")
    col_bot.dataframe(bot10, height=340)
    add_expander(
        st,
        "Numeric tables reveal leaders clustering in the mid‑80 s, "
        "while laggards struggle to reach 60 years – a stark illustration "
        "of global inequality."
    )
