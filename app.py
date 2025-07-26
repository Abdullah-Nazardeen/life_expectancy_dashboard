import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('life_expectancy.csv')
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Filters")

# Filter: Status (Developed/Developing)
status_options = df['Status'].dropna().unique().tolist()
status_filter = st.sidebar.multiselect("Country Status", status_options, default=status_options)

# Filter: Country
country_options = df[df['Status'].isin(status_filter)]['Country'].dropna().unique().tolist()
country_filter = st.sidebar.multiselect("Country", country_options, default=country_options)

# Filter: Year
year_min, year_max = int(df['Year'].min()), int(df['Year'].max())
year_filter = st.sidebar.slider("Year", year_min, year_max, (year_min, year_max), 1)

# Filter: GDP
gdp_min, gdp_max = int(df['GDP'].min()), int(df['GDP'].max())
gdp_filter = st.sidebar.slider("GDP per capita (USD)", gdp_min, gdp_max, (gdp_min, gdp_max), 100)

# Filter: Health Expenditure (% of GDP)
if 'percentage expenditure on health' in df.columns.str.lower():
    col_health_exp = [col for col in df.columns if col.lower().startswith('percentage')][0]
else:
    col_health_exp = "percentage expenditure on health"
healthexp_min, healthexp_max = float(df[col_health_exp].min()), float(df[col_health_exp].max())
healthexp_filter = st.sidebar.slider("Health Expenditure (% of GDP)", 
                                     float(healthexp_min), float(healthexp_max),
                                     (float(healthexp_min), float(healthexp_max)), 0.1)

# -- Additional filters --
school_min, school_max = float(df['Schooling'].min()), float(df['Schooling'].max())
school_filter = st.sidebar.slider("Schooling Years", school_min, school_max, (school_min, school_max), 0.5)

bmi_min, bmi_max = float(df['BMI'].min()), float(df['BMI'].max())
bmi_filter = st.sidebar.slider("Average BMI", bmi_min, bmi_max, (bmi_min, bmi_max), 0.5)

# --- FILTER DATASET ---
filtered_df = df[
    (df['Status'].isin(status_filter)) &
    (df['Country'].isin(country_filter)) &
    (df['Year'] >= year_filter[0]) & (df['Year'] <= year_filter[1]) &
    (df['GDP'] >= gdp_filter[0]) & (df['GDP'] <= gdp_filter[1]) &
    (df[col_health_exp] >= healthexp_filter[0]) & (df[col_health_exp] <= healthexp_filter[1]) &
    (df['Schooling'] >= school_filter[0]) & (df['Schooling'] <= school_filter[1]) &
    (df['BMI'] >= bmi_filter[0]) & (df['BMI'] <= bmi_filter[1])
]

# --- TITLE & INTRO ---
st.title("🌍 Life Expectancy Data Explorer")
st.markdown("""
A **data story** on what shapes human longevity around the world.  
*Explore, filter, and interact* with the data to find what drives life expectancy.
""")

# --- STORY FLOW: DASHBOARD SECTIONS ---

# 1. Key Metric Cards
st.subheader("📊 Key Stats")
kpi1 = filtered_df['Life expectancy'].mean()
kpi2 = filtered_df['GDP'].mean()
kpi3 = filtered_df['Schooling'].mean()
kpi4 = filtered_df[col_health_exp].mean()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg. Life Expectancy", f"{kpi1:.2f} yrs")
col2.metric("Avg. GDP per Capita", f"${kpi2:,.0f}")
col3.metric("Avg. Schooling Years", f"{kpi3:.2f}")
col4.metric("Avg. Health Spend %GDP", f"{kpi4:.2f}%")

# 2. GDP vs Life Expectancy
st.markdown("#### 1. GDP vs Life Expectancy")
fig_a = px.scatter(
    filtered_df, x='GDP', y='Life expectancy', 
    color='Status', hover_name='Country', trendline='ols',
    labels={"GDP": "GDP per capita (USD)", "Life expectancy": "Life Expectancy (yrs)"}
)
fig_a.update_xaxes(type='log')
st.plotly_chart(fig_a, use_container_width=True)
st.caption("Life expectancy rises with GDP, but gains flatten after basic needs are met.")

# 3. Schooling Years vs Life Expectancy
st.markdown("#### 2. Schooling vs Life Expectancy")
fig_b = px.scatter(
    filtered_df, x='Schooling', y='Life expectancy',
    color='Status', hover_name='Country', trendline='ols',
    labels={"Schooling": "Avg. Years of Schooling", "Life expectancy": "Life Expectancy (yrs)"}
)
st.plotly_chart(fig_b, use_container_width=True)
st.caption("Each additional year of school brings higher life expectancy.")

# 4. Schooling Effect after GDP (Residuals)
st.markdown("#### 3. Schooling Effect (After GDP controlled)")
if len(filtered_df) > 10:
    filtered_df = filtered_df.copy()
    filtered_df['log_gdp'] = np.log1p(filtered_df['GDP'])
    m, b = np.polyfit(filtered_df['log_gdp'], filtered_df['Life expectancy'], 1)
    filtered_df['residual'] = filtered_df['Life expectancy'] - (m * filtered_df['log_gdp'] + b)
    fig_c = px.scatter(
        filtered_df, x='Schooling', y='residual',
        color='Status', hover_name='Country',
        labels={"Schooling": "Avg. Years of Schooling", "residual": "Life Expectancy Residual (yrs)"}
    )
    fig_c.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig_c, use_container_width=True)
    st.caption("At same GDP, higher schooling still predicts longer lives (positive residuals).")
else:
    st.info("Not enough data for residual analysis. Expand filters to see this chart.")

# 5. BMI vs Life Expectancy
st.markdown("#### 4. BMI vs Life Expectancy")
fig_d = px.scatter(
    filtered_df, x='BMI', y='Life expectancy', color='Status',
    hover_name='Country',
    labels={"BMI": "Average BMI", "Life expectancy": "Life Expectancy (yrs)"}
)
st.plotly_chart(fig_d, use_container_width=True)
st.caption("Life expectancy peaks at moderate BMI, drops at under- or overweight.")

# 6. Alcohol Consumption vs Life Expectancy
st.markdown("#### 5. Alcohol vs Life Expectancy")
fig_e = px.scatter(
    filtered_df, x='Alcohol', y='Life expectancy', color='Status',
    hover_name='Country',
    labels={"Alcohol": "Alcohol Consumption (litres/capita)", "Life expectancy": "Life Expectancy (yrs)"}
)
st.plotly_chart(fig_e, use_container_width=True)
st.caption("Wealthy countries can mask alcohol’s harm, but heavy drinking lowers life expectancy overall.")

# 7. Vaccination vs Life Expectancy
st.markdown("#### 6. Vaccination (Hepatitis-B) vs Life Expectancy")
fig_f = px.scatter(
    filtered_df, x='Hepatitis B', y='Life expectancy', color='Status',
    hover_name='Country',
    labels={"Hepatitis B": "Hepatitis-B Coverage (%)", "Life expectancy": "Life Expectancy (yrs)"}
)
st.plotly_chart(fig_f, use_container_width=True)
st.caption("More childhood vaccination, longer average life.")

# 8. Life Expectancy over Time
st.markdown("#### 7. Life Expectancy Over Time (Developed vs Developing)")
time_df = filtered_df.groupby(['Year', 'Status'])['Life expectancy'].mean().reset_index()
fig_g = px.line(
    time_df, x='Year', y='Life expectancy', color='Status',
    labels={"Life expectancy": "Avg. Life Expectancy (yrs)"}
)
st.plotly_chart(fig_g, use_container_width=True)
st.caption("Developing nations are rapidly catching up to developed ones.")

# 9. Top and Bottom 10 Countries (latest year in filter)
st.markdown("#### 8. Top 10 and Bottom 10 Countries by Life Expectancy")
latest_year = filtered_df['Year'].max()
df_latest = filtered_df[filtered_df['Year'] == latest_year]
top10 = df_latest.nlargest(10, 'Life expectancy')
bot10 = df_latest.nsmallest(10, 'Life expectancy')
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Top 10**")
    st.dataframe(top10[['Country', 'Life expectancy', 'GDP', 'Status']].set_index('Country'))
with col2:
    st.markdown("**Bottom 10**")
    st.dataframe(bot10[['Country', 'Life expectancy', 'GDP', 'Status']].set_index('Country'))

st.caption("See which countries are leading and lagging in longevity.")
