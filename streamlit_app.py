"""US Leading Causes of Death — an interactive Streamlit dashboard.

Visualizes the NCHS "Leading Causes of Death: United States" dataset
(1999-2017) through four views: two choropleth maps, a time series with a
regression trend, and a per-year breakdown by cause.

Run with:  streamlit run streamlit_app.py
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from vega_datasets import data

# The dataset is downloaded on first run and cached next to this file.
DATA_URL = "https://data.cdc.gov/api/views/bi63-dtpu/rows.csv?accessType=DOWNLOAD"
DATA_FILE = Path(__file__).parent / "NCHS_-_Leading_Causes_of_Death__United_States.csv"

# The national totals are stored as their own rows and are already the sum of
# the per-state rows, so they must be excluded from any state-level aggregate.
NATIONAL = "United States"
ALL_CAUSES = "All causes"

# FIPS codes used to join the data onto the TopoJSON state boundaries.
STATE_FIPS = {
    "Alabama": 1, "Alaska": 2, "Arizona": 4, "Arkansas": 5,
    "California": 6, "Colorado": 8, "Connecticut": 9, "Delaware": 10,
    "District of Columbia": 11, "Florida": 12, "Georgia": 13,
    "Hawaii": 15, "Idaho": 16, "Illinois": 17, "Indiana": 18,
    "Iowa": 19, "Kansas": 20, "Kentucky": 21, "Louisiana": 22,
    "Maine": 23, "Maryland": 24, "Massachusetts": 25, "Michigan": 26,
    "Minnesota": 27, "Mississippi": 28, "Missouri": 29, "Montana": 30,
    "Nebraska": 31, "Nevada": 32, "New Hampshire": 33, "New Jersey": 34,
    "New Mexico": 35, "New York": 36, "North Carolina": 37,
    "North Dakota": 38, "Ohio": 39, "Oklahoma": 40, "Oregon": 41,
    "Pennsylvania": 42, "Rhode Island": 44, "South Carolina": 45,
    "South Dakota": 46, "Tennessee": 47, "Texas": 48, "Utah": 49,
    "Vermont": 50, "Virginia": 51, "Washington": 53, "West Virginia": 54,
    "Wisconsin": 55, "Wyoming": 56,
}

st.set_page_config(page_title="US Leading Causes of Death", layout="wide")
alt.data_transformers.enable("default", max_rows=None)


@st.cache_data(show_spinner="Downloading the NCHS dataset…")
def load_data() -> pd.DataFrame:
    """Return the full NCHS dataset, fetching and caching it on first run."""
    if not DATA_FILE.exists():
        pd.read_csv(DATA_URL).to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE)


@st.cache_data
def state_level(df: pd.DataFrame) -> pd.DataFrame:
    """Per-state rows only, with the FIPS id needed for the map join."""
    states = df[df["State"] != NATIONAL].copy()
    states["id"] = states["State"].map(STATE_FIPS)
    return states


@st.cache_data
def deaths_by_cause_year(df: pd.DataFrame) -> pd.DataFrame:
    """Total deaths per cause per year, plus each cause's share of the year.

    Sums only the per-state rows (the national rows would double-count) and
    only the numeric column (summing the text columns would concatenate every
    state name into one enormous string).
    """
    rows = df[(df["State"] != NATIONAL) & (df["Cause Name"] != ALL_CAUSES)]
    totals = rows.groupby(["Cause Name", "Year"], as_index=False)["Deaths"].sum()
    totals["Fraction"] = totals.groupby("Year")["Deaths"].transform(lambda s: s / s.sum())
    return totals


us_states = alt.topo_feature(data.us_10m.url, feature="states")
death_db = load_data()
death_by_state = state_level(death_db)

st.title("US Leading Causes of Death, 1999–2017")

viz_type = st.selectbox(
    "Choose a visualization:",
    [
        "State-Wise Geospatial",
        "Time Series Regression",
        "Year wise Pie Chart",
        "Safest States Year Wise",
    ],
)

if viz_type == "State-Wise Geospatial":
    selected_year = st.selectbox("Select Year", sorted(death_by_state["Year"].unique()))
    selected_cause = st.selectbox(
        "Select Cause of Death", sorted(death_by_state["Cause Name"].unique())
    )

    filtered_df = death_by_state[
        (death_by_state["Year"] == selected_year)
        & (death_by_state["Cause Name"] == selected_cause)
    ]

    chart = (
        alt.Chart(us_states)
        .mark_geoshape(stroke="white", strokeWidth=1)
        .encode(
            color=alt.Color(
                "Deaths:Q", scale=alt.Scale(scheme="reds"), title="Deaths"
            ),
            tooltip=["State:N", "Deaths:Q", "Cause Name:N", "Year:N"],
        )
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                filtered_df, "id", ["Deaths", "State", "Cause Name", "Year"]
            ),
        )
        .project(type="albersUsa")
        .properties(
            width=800,
            height=500,
            title=f"Deaths from {selected_cause} in {selected_year}",
        )
    )

    st.altair_chart(chart)
    st.caption(
        "Raw death counts are not population-adjusted, so the most populous "
        "states dominate. See *Safest States Year Wise* for age-adjusted rates."
    )

elif viz_type == "Time Series Regression":
    selected_cause = st.selectbox(
        "Select Cause of Death", options=sorted(death_by_state["Cause Name"].unique())
    )

    # One row per year, so the line and the regression fit see each year once.
    yearly = (
        death_by_state[death_by_state["Cause Name"] == selected_cause]
        .groupby("Year", as_index=False)["Deaths"]
        .sum()
        .rename(columns={"Deaths": "total_deaths"})
    )

    base = alt.Chart(yearly)

    line = base.mark_line(point=True, strokeWidth=3).encode(
        x=alt.X(
            "Year:O",
            title="Year",
            axis=alt.Axis(labelFontSize=14, titleFontSize=16, tickSize=8,
                          labelAngle=0, grid=True),
        ),
        y=alt.Y(
            "total_deaths:Q",
            title="Total Deaths",
            axis=alt.Axis(labelFontSize=14, titleFontSize=16, tickSize=8,
                          grid=False, labelOverlap=False),
        ),
        color=alt.value("steelblue"),
        tooltip=[
            alt.Tooltip("Year:O", title="Year"),
            alt.Tooltip("total_deaths:Q", title="Total Deaths", format=","),
        ],
    )

    regression = (
        base.transform_regression("Year", "total_deaths")
        .mark_line(strokeDash=[5, 5], strokeWidth=3)
        .encode(x="Year:O", y="total_deaths:Q", color=alt.value("red"))
    )

    chart = (
        (line + regression)
        .properties(height=500, title=f"Year-wise Deaths for {selected_cause}")
        .configure_title(fontSize=20, anchor="middle")
    )

    st.altair_chart(chart, width="stretch")
    st.caption("Solid blue: observed totals. Dashed red: linear trend.")

elif viz_type == "Year wise Pie Chart":
    totals = deaths_by_cause_year(death_db)

    selected_year = st.selectbox(
        "Select Year", sorted(totals["Year"].unique()),
        index=len(totals["Year"].unique()) - 1,
    )
    year_totals = totals[totals["Year"] == selected_year]

    # Shared encodings; the arc and its labels are drawn from the same base so
    # the text lines up with the wedge it describes.
    base = alt.Chart(year_totals).encode(
        theta=alt.Theta("Deaths:Q", stack=True),
        color=alt.Color("Cause Name:N", title="Cause of Death"),
        tooltip=[
            alt.Tooltip("Cause Name:N", title="Cause of Death"),
            alt.Tooltip("Deaths:Q", title="Deaths", format=","),
            alt.Tooltip("Fraction:Q", title="Share", format=".1%"),
        ],
    )

    pie = base.mark_arc(outerRadius=240, stroke=None)
    # Each label inherits its slice's color rather than a hard-coded black or
    # white, so it stays readable in both the light and dark Streamlit themes.
    labels = base.mark_text(radius=275, fontSize=13, fontWeight="bold").encode(
        text=alt.Text("Fraction:Q", format=".1%")
    )

    chart = (pie + labels).properties(
        width=650, height=650,
        title=f"Share of Deaths by Cause, {selected_year}",
    )

    st.altair_chart(chart)
    st.caption("Excludes the 'All causes' rollup so the shares sum to 100%.")

else:
    all_causes = death_by_state[death_by_state["Cause Name"] == ALL_CAUSES]
    selected_year = st.selectbox("Select Year", sorted(all_causes["Year"].unique()))
    filtered_data = all_causes[all_causes["Year"] == selected_year]

    chart = (
        alt.Chart(us_states)
        .mark_geoshape(stroke="white", strokeWidth=1)
        .encode(
            color=alt.Color(
                "Age-adjusted Death Rate:Q",
                scale=alt.Scale(
                    scheme="darkgreen",
                    domain=[
                        filtered_data["Age-adjusted Death Rate"].min(),
                        filtered_data["Age-adjusted Death Rate"].max(),
                    ],
                    type="sqrt",
                ),
                title="Death Rate",
            ),
            tooltip=[
                alt.Tooltip("State:N", title="State"),
                alt.Tooltip("Age-adjusted Death Rate:Q", title="Death Rate"),
                alt.Tooltip("Year:O", title="Year"),
            ],
        )
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                filtered_data, "id", ["State", "Age-adjusted Death Rate", "Year"]
            ),
        )
        .project(type="albersUsa")
        .properties(
            width=800,
            height=500,
            title=f"Age-Adjusted Death Rates by State ({selected_year})",
        )
    )

    st.altair_chart(chart)
    st.caption(
        "Deaths per 100,000, age-adjusted so states with different age "
        "profiles are comparable. Darker green means a lower rate."
    )
