import chainlit as cl
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

DATA_PATH = Path(__file__).parent / "Life Expectancy Data.csv"

# -----------------------------------------------------------
# 1.  LOAD & PREPARE DATA
# -----------------------------------------------------------
@cl.cache  # cached across app lifetime
def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    # Add convenience columns
    df["log_gdp"] = np.log1p(df["GDP"])
    # simple Preston‑curve residual for later use
    mask = df[["log_gdp", "Life expectancy"]].notna().all(axis=1)
    m, b = np.polyfit(df.loc[mask, "log_gdp"], df.loc[mask, "Life expectancy"], 1)
    df["LE_residual"] = df["Life expectancy"] - (m * df["log_gdp"] + b)
    return df


# -----------------------------------------------------------
# 2.  FILTER UTILITIES
# -----------------------------------------------------------
def apply_filters(df, ui_values):
    """Return a filtered dataframe based on UI selections."""
    st = ui_values["status"]
    ct = ui_values["countries"]
    gdp_lo, gdp_hi = ui_values["gdp_range"]
    hexp_lo, hexp_hi = ui_values["hexp_range"]

    sel = pd.Series(True, index=df.index)
    if st != "Both":
        sel &= df["Status"] == st
    if ct:
        sel &= df["Country"].isin(ct)
    sel &= df["GDP"].between(gdp_lo, gdp_hi)
    sel &= df["percentage expenditure"].between(hexp_lo, hexp_hi)

    return df[sel]


# -----------------------------------------------------------
# 3.  CHART BUILDERS
# -----------------------------------------------------------
def chart_gdp(df):
    return px.scatter(
        df,
        x="GDP",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        log_x=True,
        trendline="ols",
        title="GDP vs Life‑Expectancy",
    )


def chart_schooling(df):
    return px.scatter(
        df,
        x="Schooling",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="Schooling vs Life‑Expectancy",
    )


def chart_bmi(df):
    return px.scatter(
        df,
        x="BMI",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="BMI vs Life‑Expectancy",
    )


def chart_alcohol(df):
    return px.scatter(
        df,
        x="Alcohol",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="Alcohol Consumption vs Life‑Expectancy",
    )


def chart_vax(df):
    return px.scatter(
        df,
        x="Hepatitis B",
        y="Life expectancy",
        color="Status",
        hover_name="Country",
        title="Hep‑B Vaccination vs Life‑Expectancy",
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
        title="Developed vs Developing: 2000‑2015 Trend",
    )


def chart_bar_10(df, top=True):
    last = df[df["Year"] == df["Year"].max()]
    last = last.dropna(subset=["Life expectancy"])
    use = last.nlargest(10, "Life expectancy") if top else last.nsmallest(10, "Life expectancy")
    title = "Top 10 (Highest) Life‑Expectancy" if top else "Bottom 10 (Lowest) Life‑Expectancy"
    return px.bar(use, x="Country", y="Life expectancy", title=title)


# -----------------------------------------------------------
# 4.  UI LAYOUT & EVENT LOOP
# -----------------------------------------------------------
@cl.on_chat_start
def start():
    df = load_data()
    cl.user_session.set("df", df)  # stash for later callbacks

    # ---------- SIDEBAR FILTERS ----------
    with cl.sidebar:
        cl.html("<h3 style='margin-bottom:0'>Filters</h3>", unsafe_allow_html=True)

        status = cl.ui.select(
            label="Country Status",
            options=["Both", "Developed", "Developing"],
            value="Both",
            key="status",
        )

        country_opts = sorted(df["Country"].unique().tolist())
        countries = cl.ui.multiselect(
            label="Country (leave empty = all)",
            options=country_opts,
            key="countries",
        )

        gdp_slider = cl.ui.range_slider(
            label="GDP per Capita (USD)",
            min=float(df["GDP"].min()),
            max=float(df["GDP"].max()),
            value=(float(df["GDP"].min()), float(df["GDP"].max())),
            step=1000.0,
            key="gdp_range",
        )

        hexp_slider = cl.ui.range_slider(
            label="Health Expenditure % of GDP",
            min=float(df["percentage expenditure"].min()),
            max=float(df["percentage expenditure"].max()),
            value=(float(df["percentage expenditure"].min()), float(df["percentage expenditure"].max())),
            step=0.1,
            key="hexp_range",
        )

    # cache starting UI values
    cl.user_session.set(
        "ui_values",
        {
            "status": status.value,
            "countries": countries.value,
            "gdp_range": gdp_slider.value,
            "hexp_range": hexp_slider.value,
        },
    )

    # ---------- INITIAL DASHBOARD ----------
    refresh_dashboard()


@cl.on_ui_event
def ui_event(event):
    """Update stored UI selections then refresh charts."""
    if event.metadata and event.metadata.get("key") in (
        "status",
        "countries",
        "gdp_range",
        "hexp_range",
    ):
        ui_vals = cl.user_session.get("ui_values")
        ui_vals[event.metadata["key"]] = event.value
        cl.user_session.set("ui_values", ui_vals)
        refresh_dashboard()


def refresh_dashboard():
    df = cl.user_session.get("df")
    ui_vals = cl.user_session.get("ui_values")
    fdf = apply_filters(df, ui_vals)

    cl.message.update_content("📊 **Dashboard refreshed!**\nFilters applied to "
                              f"{len(fdf):,} data points.\n")

    # Clear old visuals
    cl.message.clear_elements()

    # Add plots (the order tells the “story” top‑to‑bottom like Power BI)
    plots = [
        chart_gdp(fdf),
        chart_schooling(fdf),
        chart_bmi(fdf),
        chart_alcohol(fdf),
        chart_vax(fdf),
        chart_trend(fdf),
        chart_bar_10(fdf, top=True),
        chart_bar_10(fdf, top=False),
    ]
    for p in plots:
        cl.message.add_plotly(p)

    cl.message.send()


# -----------------------------------------------------------
# CLI ENTRY (optional, lets you run `python app.py` too)
# -----------------------------------------------------------
if __name__ == "__main__":
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "chainlit", "run", __file__])
