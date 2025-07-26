import chainlit as cl
from chainlit.input_widget import Slider, Select, Tags
from chainlit.element import Plotly, Markdown
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

DATA_PATH = Path(__file__).parent / "life_expectancy.csv"

@cl.cache
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df

def get_status_filter_vals(df):
    # User-facing options: Both, Developed, Developing
    opts = sorted(df.status.unique())
    return ["Both"] + opts

def filter_df(df, year, status, countries):
    mask = df.year == year
    if status != "Both":
        mask &= (df.status == status)
    if countries:
        mask &= df.country.isin(countries)
    return df[mask]

async def render_dashboard(filters: dict):
    df = cl.user_session.get("df")
    year = filters["year"]
    status_sel = filters["status"]
    country_sel = filters["countries"]

    df_year = filter_df(df, year, status_sel, country_sel)

    # --- KPIs ---
    kpi_rows = []
    if len(df_year) > 0:
        avg_le = df_year.life_expectancy.mean()
        best = df_year.loc[df_year.life_expectancy.idxmax()]
        worst = df_year.loc[df_year.life_expectancy.idxmin()]
        avg_gdp = df_year.gdp.mean() / 1_000
        kpi_rows = [
            ["**Average Life‑Expectancy (yrs)**", f"{avg_le:.1f}"],
            ["**Highest Country**", f"{best.country.title()} ({best.life_expectancy:.1f} yrs)"],
            ["**Lowest Country**", f"{worst.country.title()} ({worst.life_expectancy:.1f} yrs)"],
            ["**Avg GDP per Capita (×$1 000 USD)**", f"{avg_gdp:.1f}"],
        ]
    else:
        kpi_rows = [
            ["No data for these filters", ""]
        ]
    kpi_md = (
        f"**🌍 Global Life‑Expectancy Dashboard – {year}**\n\n"
        "| Metric | Value |\n"
        "|--------|-------|\n" +
        "\n".join([f"| {a} | {b} |" for a, b in kpi_rows])
    )

    # --- CHARTS ---
    figs = []
    if len(df_year) > 0:
        # 1. Top‑10 bar
        top10 = df_year.nlargest(10, "life_expectancy").sort_values("life_expectancy")
        figs.append(
            px.bar(
                top10,
                x="life_expectancy",
                y="country",
                orientation="h",
                color="life_expectancy",
                color_continuous_scale="Blues",
                labels={"life_expectancy": "Years", "country": ""},
                title=f"🏅 Top‑10 Countries by Life‑Expectancy — {year}",
            ).update_layout(height=400)
        )
        # 2. Status Box‑plot
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
        # 3. GDP Scatter
        figs.append(
            px.scatter(
                df_year,
                x="gdp",
                y="life_expectancy",
                color="status",
                hover_name="country",
                size="population" if "population" in df_year.columns else None,
                log_x=True,
                labels={"gdp": "GDP per Capita (log‑scale USD)", "life_expectancy": "Years"},
                title=f"💰 GDP vs Life‑Expectancy — {year}",
            ).update_layout(height=450)
        )
        # 4. 2000‑2015 Trend
        # Use all data for this chart
        sel_statuses = (
            df.status.unique().tolist()
            if status_sel == "Both" else [status_sel]
        )
        trend_df = (
            df[df.status.isin(sel_statuses)]
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
        # 5. Schooling Scatter
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

    # --- SEND DASHBOARD ---
    elements = [Markdown(kpi_md)] + [Plotly(name=fig.layout.title.text, figure=fig) for fig in figs]
    await cl.Message(content=None, elements=elements).send()

@cl.on_chat_start
async def start():
    df = load_data()
    cl.user_session.set("df", df)
    years = sorted(df.year.unique())
    status_opts = get_status_filter_vals(df)
    country_opts = sorted(df.country.unique().tolist())

    settings = await cl.ChatSettings(
        label="🔍 Filters",
        inputs=[
            Slider(
                id="year",
                label="Year",
                min=int(years[0]),
                max=int(years[-1]),
                initial=int(years[-1]),
                step=1,
            ),
            Select(
                id="status",
                label="Development Status",
                values=status_opts,
                initial_index=0,
            ),
            Tags(
                id="countries",
                label="Country (optional)",
                initial=[],
                options=country_opts
            ),
        ],
    ).send()

    cl.user_session.set("filters", settings)
    await render_dashboard(settings)

@cl.on_settings_update
async def update(settings: dict):
    cl.user_session.set("filters", settings)
    await render_dashboard(settings)

if __name__ == "__main__":
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "chainlit", "run", __file__])
