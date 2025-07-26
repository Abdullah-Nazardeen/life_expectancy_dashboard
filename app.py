import chainlit as cl
from chainlit.input_widget import Slider, Multiselect, Tags
from chainlit.element import Plotly, Markdown
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ───────────────── DATA LOADING ─────────────────
DATA_PATH = Path(__file__).parent / "life_expectancy.csv"

@cl.cache
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    # match your Streamlit cleaning
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df

# ───────────────── RENDERER ────────────────────
async def render_dashboard(filters: dict):
    df = cl.user_session.get("df")
    year = filters["year"]
    status_sel = filters["status"]
    country_sel = filters["countries"]

    # Filter for selected year/status/countries
    mask = (df.year == year) & (df.status.isin(status_sel))
    if country_sel:
        mask &= df.country.isin(country_sel)
    df_year = df[mask]

    # ── KPI METRICS ──
    avg_le = df_year.life_expectancy.mean()
    best = df_year.loc[df_year.life_expectancy.idxmax()]
    worst = df_year.loc[df_year.life_expectancy.idxmin()]
    avg_gdp = df_year.gdp.mean() / 1_000

    kpi_md = f"""
**🌍 Global Life‑Expectancy Dashboard – {year}**

| Metric                                   | Value                        |
|-----------------------------------------:|:-----------------------------|
| **Average Life‑Expectancy (yrs)**        | {avg_le:.1f}                 |
| **Highest Country**                      | {best.country.title()} ({best.life_expectancy:.1f} yrs) |
| **Lowest Country**                       | {worst.country.title()} ({worst.life_expectancy:.1f} yrs) |
| **Avg GDP per Capita (×$1 000 USD)**     | {avg_gdp:.1f}                |
"""
    # ── CHARTS ──
    figs = []

    # 1️⃣ Top‑10 bar
    top10 = df_year.nlargest(10, "life_expectancy").sort_values("life_expectancy")
    figs.append(
        px.bar(
            top10,
            x="life_expectancy",
            y="country",
            orientation="h",
            color="life_expectancy",
            labels={"life_expectancy": "Years", "country": ""},
            title=f"🏅 Top‑10 Countries by Life‑Expectancy — {year}",
        ).update_layout(height=400)
    )

    # 2️⃣ Status Box‑plot
    figs.append(
        px.box(
            df_year,
            x="status",
            y="life_expectancy",
            color="status",
            points="all",
            labels={"life_expectancy": "Years", "status": ""},
            title=f"📦 Life‑Expectancy by Development Status — {year}",
        ).update_layout(height=400)
    )

    # 3️⃣ GDP Scatter
    figs.append(
        px.scatter(
            df_year,
            x="gdp",
            y="life_expectancy",
            color="status",
            hover_name="country",
            size="population",
            log_x=True,
            labels={"gdp": "GDP per Capita (log‑scale USD)", "life_expectancy": "Years"},
            title=f"💰 GDP vs Life‑Expectancy — {year}",
        ).update_layout(height=450)
    )

    # 4️⃣ 2000‑2015 Trend
    trend_df = (
        df[df.status.isin(status_sel)]
        .groupby(["year", "status"], as_index=False)["life_expectancy"]
        .mean()
    )
    figs.append(
        px.line(
            trend_df,
            x="year",
            y="life_expectancy",
            color="status",
            markers=True,
            labels={"life_expectancy": "Avg Life‑Expectancy (yrs)", "year": ""},
            title="📈 Global Trend 2000‑2015 (Developed vs Developing)",
        ).update_layout(height=400)
    )

    # 5️⃣ Schooling Scatter
    figs.append(
        px.scatter(
            df_year,
            x="schooling",
            y="life_expectancy",
            trendline="ols",
            color="status",
            hover_name="country",
            labels={"schooling": "Avg Years of Schooling", "life_expectancy": "Years"},
            title=f"🎓 Schooling vs Life‑Expectancy — {year}",
        ).update_layout(height=450)
    )

    # ── SEND MESSAGE ──
    elements = [Markdown(kpi_md)] + [Plotly(name=fig.layout.title.text, figure=fig) for fig in figs]
    await cl.Message(content=None, elements=elements).send()

# ───────────────── LIFECYCLE HOOKS ─────────────────
@cl.on_chat_start
async def start():
    df = load_data()
    cl.user_session.set("df", df)

    # prepare filter options
    years = sorted(df.year.unique())
    status_opts = sorted(df.status.unique().tolist())
    country_opts = sorted(df.country.unique().tolist())

    # open the settings pane (cog‑icon)
    settings = await cl.ChatSettings(
        label="🔍 Filters",
        inputs=[
            Slider(id="year", label="Year", min=int(min(years)), max=int(max(years)), initial=int(max(years)), step=1),
            Multiselect(id="status", label="Development Status", options=status_opts, initial=status_opts),
            Tags(id="countries", label="Country (optional)", initial=[]),
        ],
    ).send()

    cl.user_session.set("filters", settings)
    await render_dashboard(settings)

@cl.on_settings_update
async def update(settings: dict):
    cl.user_session.set("filters", settings)
    await render_dashboard(settings)

# ───────────────── CLI ENTRY ─────────────────
if __name__ == "__main__":
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "chainlit", "run", __file__])
