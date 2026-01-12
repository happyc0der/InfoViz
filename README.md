# InfoViz
Small visualization project showcasing the various causes of death in USA on a dashboard from early 2000s to late 2010s
# US Leading Causes of Death Dashboard

An interactive Streamlit dashboard for visualizing leading causes of death in the United States from 1999-2017, featuring geospatial maps, time series analysis, and comparative visualizations.

## Features

- **State-Wise Geospatial View**: Interactive choropleth map showing deaths by state for selected year and cause
- **Time Series Regression**: Year-over-year trends with regression lines for each cause of death
- **Year-wise Pie Chart**: Proportional distribution of deaths across different causes
- **Safest States Analysis**: Age-adjusted death rate comparison across states

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### 1. Clone or Download the Code

Save the provided Python code as `dashboard.py` in a new directory.

### 2. Install Required Dependencies

Open your terminal and navigate to the project directory, then run:

```bash
pip install streamlit pandas altair geopandas vega-datasets
```

### 3. Running the Code

Open the project folder and run the followig:

```bash
streamlit run streamlit_app.py
```
