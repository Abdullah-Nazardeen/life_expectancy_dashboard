import chainlit as cl
from chainlit.input_widget import Select, Slider, Tags
from chainlit.element import Plotly
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

DATA_PATH = Path(__file__).parent / "Life Expectancy Data.csv"


# ────────────────────────────────  DATA  ────────────────────────────────
@cl.cache
def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    # helpers
    df["log_gdp"] = np.log1p(df["GDP"])
    mask = df[["log_gdp", "Life expectancy"]].notna().all(axis=1)
    m, b = np.polyfit(df.loc[mask, "log_gdp"], df.loc[mask, "Life expectancy"], 1)
    df["LE_residual"] = df["Life expectancy"] - (m * df["log_gdp"] + b)
    return df


def apply_filters(df, f):
    sel = pd.Series(True, index=df.index)

    if f["status"] != "Both":
        sel &= df["Status"] == f["status"]

    if f["countries"]:
        sel &= df["Country"].isin(f["countries"])

    sel &= df["GDP"].between(f["min_gdp"], f["max_gdp"])
    sel &= df["percentage expenditure"].between(f["min_hexp"], f["max_hexp"])

    return df[sel]


# ────────────────────────────────  CHARTS  ────────────────────────────────
def chart_gdp(df):
    return px.scatter(
        df,
        x="GDP",
        y="Life expectancy",
        color="Status",
        log_x=True,
        hover_name="Country",
        trendline="ols",
        title="GDP vs Life‑Expectancy",
    )


def chart_schooling(df):
    return px.scatter(
        df,
        x="Schooling",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="Schooling vs Life‑Expectancy",
    )


def chart_bmi(df):
    return px.scatter(
        df,
        x="BMI",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="BMI vs Life‑Expectancy",
    )


def chart_alcohol(df):
    return px.scatter(
        df,
        x="Alcohol",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="Alcohol Consumption vs Life‑Expectancy",
    )


def chart_vax(df):
    return px.scatter(
        df,
        x="Hepatitis B",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="Hep‑B Vaccination vs Life‑Expectancy",
    )


def chart_trend(df):
    trend = (
        df.groupby(["Year", "Status"])["Life expectancy"]
        .mean()
        .reset_index()
        .pivot(index="Year", columns="Status", values="Life expectancy")
        .reset_index()
    )
    return px.line(
        trend,
        x="Year",
        y=trend.columns[1:],
        labels={"value": "Life Expectancy", "variable": "Status"},
        title="Developed vs Developing (2000‑2015)",
    )


def chart_bar_10(df, top=True):
    last = df[df["Year"] == df["Year"].max()].dropna(subset=["Life expectancy"])
    use = last.nlargest(10, "Life expectancy") if top else last.nsmallest(10, "Life expectancy")
    ttl = "Top 10 (Highest) 2015" if top else "Bottom 10 (Lowest) 2015"
    return px.bar(use, x="Country", y="Life expectancy", title=ttl)


# ────────────────────────────────  DASHBOARD  ────────────────────────────────
async def render_dashboard(filters):
    df = cl.user_session.get("df")
    fdf = apply_filters(df, filters)

    figs = [
        chart_gdp(fdf),
        chart_schooling(fdf),
        chart_bmi(fdf),
        chart_alcohol(fdf),
        chart_vax(fdf),
        chart_trend(fdf),
        chart_bar_10(fdf, top=True),
        chart_bar_10(fdf, top=False),
    ]

    elements = [Plotly(name=fig.layout.title.text, figure=fig) for fig in figs]

    await cl.Message(
        content=f"📊 **Dashboard refreshed – {len(fdf):,} rows after filters**",
        elements=elements,
    ).send()


# ────────────────────────────────  LIFE‑CYCLE HOOKS  ─────────────────────────
@cl.on_chat_start
async def start():
    df = load_data()
    cl.user_session.set("df", df)

    max_gdp = int(df["GDP"].max())
    max_hexp = float(df["percentage expenditure"].max())

    initial_filters = {
        "status": "Both",
        "countries": [],
        "min_gdp": 0,
        "max_gdp": max_gdp,
        "min_hexp": 0.0,
        "max_hexp": max_hexp,
    }

    # Build the settings panel (cog‑icon)
    settings = await cl.ChatSettings(
        inputs=[
            Select(
                id="status",
                label="Country Status",
                values=["Both", "Developed", "Developing"],
                initial_index=0,
            ),
            Tags(id="countries", label="Countries (optional)", initial=[]),
            Slider(
                id="min_gdp",
                label="Min GDP per Capita",
                min=0,
                max=max_gdp,
                initial=0,
                step=1_000,
            ),
            Slider(
                id="max_gdp",
                label="Max GDP per Capita",
                min=0,
                max=max_gdp,
                initial=max_gdp,
                step=1_000,
            ),
            Slider(
                id="min_hexp",
                label="Min Health Expenditure % GDP",
                min=0,
                max=max_hexp,
                initial=0,
                step=0.1,
            ),
            Slider(
                id="max_hexp",
                label="Max Health Expenditure % GDP",
                min=0,
                max=max_hexp,
                initial=max_hexp,
                step=0.1,
            ),
        ],
        label="Filters",
    ).send()

    # Store and render
    cl.user_session.set("filters", settings)
    await render_dashboard(settings)


@cl.on_settings_update
async def _update(new_settings: dict):
    cl.user_session.set("filters", new_settings)
    await render_dashboard(new_settings)


# Optional command‑line entry point ➜  python app.py
if __name__ == "__main__":
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "chainlit", "run", __file__])
