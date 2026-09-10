# InfoViz — US Leading Causes of Death

An interactive Streamlit dashboard for exploring the leading causes of death in
the United States from **1999 to 2017**, using the CDC/NCHS public dataset.
It offers four linked views: two choropleth maps, a time series with a fitted
trend line, and a per-year breakdown by cause.

The dataset downloads itself on first launch, so the only setup is installing
four Python packages.

## Quick start

```bash
git clone https://github.com/happyc0der/InfoViz.git
```

```bash
cd InfoViz && pip install -r requirements.txt
```

```bash
streamlit run streamlit_app.py
```

Streamlit opens <http://localhost:8501> automatically. The first run fetches
~800 KB from the CDC and caches it next to the script; every run after that is
offline and instant.

Using a virtual environment is recommended:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## The four views

Pick one from the **"Choose a visualization"** dropdown at the top.

### 1. State-Wise Geospatial

A choropleth of the US shaded by the **raw number of deaths**, with dropdowns
for year and cause. Hovering a state shows its exact count.

Because this maps raw counts rather than rates, it largely tracks population —
California, Texas, Florida and New York are the darkest for almost every cause.
For a population-adjusted comparison, use view 4.

### 2. Time Series Regression

A line chart of nationwide deaths per year for a chosen cause, with a dashed
red linear-regression line over it. Useful for seeing whether a cause is
trending up or down over the 19-year window — deaths from Alzheimer's disease
nearly tripled between 1999 and 2017, for instance, while stroke deaths fell
by about 13%.

Totals are summed across the 50 states plus DC.

### 3. Year wise Pie Chart

Each cause's **share of all deaths** in a selected year, labelled with its
percentage and shaded by cause. The `All causes` rollup row is excluded so the
slices sum to exactly 100%.

### 4. Safest States Year Wise

A choropleth shaded by **age-adjusted death rate** (deaths per 100,000,
standardized to a common age distribution). Because it corrects for the fact
that some states simply have older populations, this is the view that supports
an honest state-to-state comparison. **Darker green means a lower death rate**,
i.e. safer.

## The data

Source: [NCHS — Leading Causes of Death: United States][src] (dataset
`bi63-dtpu` on the CDC open data portal), a public-domain US government
dataset. 10,868 rows covering 10 leading causes plus an `All causes` rollup,
for all 50 states, DC, and a national total, from 1999 to 2017.

| Column | Meaning |
| --- | --- |
| `Year` | 1999–2017 |
| `113 Cause Name` | Full ICD-10 cause name with code ranges |
| `Cause Name` | Short cause label used throughout the dashboard |
| `State` | State name, `District of Columbia`, or `United States` |
| `Deaths` | Number of deaths |
| `Age-adjusted Death Rate` | Deaths per 100,000, age-standardized |

Two things to know when working with this data:

- **The `United States` rows are a national total, not another state.** They
  already contain the sum of all the state rows, so any aggregate across states
  must exclude them or every death gets counted twice.
- **`Cause Name == "All causes"` is a rollup**, not one of the ten causes, so it
  must be excluded from any breakdown that is supposed to sum to 100%.

`streamlit_app.py` handles both, but they are easy traps if you extend it.

[src]: https://data.cdc.gov/NCHS/NCHS-Leading-Causes-of-Death-United-States/bi63-dtpu

### Getting the data manually

The app downloads the CSV for you. To supply it yourself — for an offline or
air-gapped machine — download it and place it beside `streamlit_app.py` with
this exact filename:

```bash
curl -L -o "NCHS_-_Leading_Causes_of_Death__United_States.csv" "https://data.cdc.gov/api/views/bi63-dtpu/rows.csv?accessType=DOWNLOAD"
```

The file is gitignored, since it is a reproducible download rather than source.

## How it works

The whole dashboard is one file, `streamlit_app.py`, laid out as:

| Part | Role |
| --- | --- |
| `load_data()` | Downloads the CSV on first run, then reads from the local cache |
| `state_level()` | Drops the national rows and attaches FIPS codes for the map join |
| `deaths_by_cause_year()` | Totals per cause per year, plus each cause's share |
| `STATE_FIPS` | Maps all 51 state names to the FIPS ids used by the TopoJSON |
| `if/elif` on `viz_type` | One branch per view, each building an Altair chart |

Charts are built with [Altair](https://altair-viz.github.io/) and rendered
through `st.altair_chart`. The maps join the data onto Vega's `us_10m`
TopoJSON via `transform_lookup` on the FIPS id, projected with `albersUsa`.

All three data functions are wrapped in `@st.cache_data`, so changing a
dropdown re-renders the chart without re-parsing the CSV.

## Requirements

Python 3.8+ and the four packages in `requirements.txt`: `streamlit`,
`pandas`, `altair`, `vega-datasets`. Verified on Python 3.14 with
Streamlit 1.63, pandas 3.0, and Altair 6.

> **Note:** earlier versions of this project asked you to install `geopandas`.
> It was never actually used and is no longer required — you can safely
> uninstall it if you installed it for this project.

## Troubleshooting

**The map is blank or all one color.** The map data is fetched from Vega's CDN
at render time, so it needs a working internet connection.

**`FileNotFoundError` for the CSV.** The first-run download failed, most likely
offline or behind a proxy. Fetch the file manually with the `curl` command
above.

**Port 8501 already in use.** Run on another port:

```bash
streamlit run streamlit_app.py --server.port 8502
```

**Stale data after editing.** Streamlit caches aggressively — press `C` in the
browser, or "Clear cache" in the ☰ menu.

## License

Released under the [MIT License](LICENSE). The underlying NCHS dataset is a
US government work in the public domain.
