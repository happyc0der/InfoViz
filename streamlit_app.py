
import altair as alt
import pandas as pd
import geopandas as gpd
import streamlit as st
alt.data_transformers.disable_max_rows()
from vega_datasets import data
states = alt.topo_feature(data.us_10m.url, feature='states')
death_db = pd.read_csv('NCHS_-_Leading_Causes_of_Death__United_States.csv')
state_fips = {
    'Alabama': 1, 'Alaska': 2, 'Arizona': 4, 'Arkansas': 5,
    'California': 6, 'Colorado': 8, 'Connecticut': 9, 'Delaware': 10,
    'District of Columbia': 11, 'Florida': 12, 'Georgia': 13, 
    'Hawaii': 15, 'Idaho': 16, 'Illinois': 17, 'Indiana': 18,
    'Iowa': 19, 'Kansas': 20, 'Kentucky': 21, 'Louisiana': 22,
    'Maine': 23, 'Maryland': 24, 'Massachusetts': 25, 'Michigan': 26,
    'Minnesota': 27, 'Mississippi': 28, 'Missouri': 29, 'Montana': 30,
    'Nebraska': 31, 'Nevada': 32, 'New Hampshire': 33, 'New Jersey': 34,
    'New Mexico': 35, 'New York': 36, 'North Carolina': 37,
    'North Dakota': 38, 'Ohio': 39, 'Oklahoma': 40, 'Oregon': 41,
    'Pennsylvania': 42, 'Rhode Island': 44, 'South Carolina': 45,
    'South Dakota': 46, 'Tennessee': 47, 'Texas': 48, 'Utah': 49,
    'Vermont': 50, 'Virginia': 51, 'Washington': 53, 'West Virginia': 54,
    'Wisconsin': 55, 'Wyoming': 56
}


death_by_state = death_db[death_db['State'] != 'United States']
viz_type = st.selectbox(
    'Choose a visualization:',
    ['State-Wise Geospatial', 'Time Series Regression', 'Year wise Pie Chart','Safest States Year Wise']
)
if viz_type == 'State-Wise Geospatial':
    
    death_by_state['id'] = death_by_state['State'].map(state_fips)
    # Create dropdowns using Streamlit widgets
    selected_year = st.selectbox("Select Year", sorted(death_by_state['Year'].unique()))
    selected_cause = st.selectbox("Select Cause of Death", sorted(death_by_state['Cause Name'].unique()))

    # Filter your DataFrame dynamically
    filtered_df = death_by_state[
        (death_by_state['Year'] == selected_year) &
        (death_by_state['Cause Name'] == selected_cause)
    ]

    # Create the chart with filtered data
    chart = alt.Chart(states).mark_geoshape(
        stroke='white',
        strokeWidth=1
    ).encode(
        color=alt.Color('Deaths:Q', scale=alt.Scale(scheme='reds'), title='Deaths'),
        tooltip=['State:N', 'Deaths:Q', 'Cause Name:N', 'Year:N']
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(filtered_df, 'id', ['Deaths', 'State', 'Cause Name', 'Year'])
    ).project(type='albersUsa').properties(
        width=800,
        height=500,
        title=f'Deaths from {selected_cause} in {selected_year}'
    )

    st.altair_chart(chart)
elif viz_type == 'Time Series Regression':
    
    selected_cause = st.selectbox(
    "Select Cause of Death",
    options=sorted(death_by_state['Cause Name'].unique()))
    filtered_data = death_by_state[death_by_state['Cause Name'] == selected_cause]

    # First create aggregated data
    filtered_data = filtered_data.assign(
        total_deaths=filtered_data.groupby('Year')['Deaths'].transform('sum')
    )

    # Create base chart
    base = alt.Chart(filtered_data)

    # Create main line with points
    line = base.mark_line(
        point=True,
        strokeWidth=3
    ).encode(
        x=alt.X('Year:O',
            title='Year',
            axis=alt.Axis(
                labelFontSize=14,
                titleFontSize=16,
                tickSize=8,
                labelAngle=0,
                grid=True
            )
        ),
        y=alt.Y('total_deaths:Q',
            title='Total Deaths',
            axis=alt.Axis(
                labelFontSize=14,
                titleFontSize=16,
                tickSize=8,
                grid=False,
                labelOverlap=False
            )
        ),
        color=alt.value('steelblue'),
        tooltip=[
            alt.Tooltip('Year:O', title='Year'),
            alt.Tooltip('total_deaths:Q', title='Total Deaths', format=','),
            alt.Tooltip('Cause Name:N', title='Cause of Death')
        ]
    )

    # Add regression line with legend
    regression = base.transform_regression(
        'Year', 'total_deaths'
    ).mark_line(
        strokeDash=[5,5],
        strokeWidth=3
    ).encode(
        x='Year:O',
        y='total_deaths:Q',
        color=alt.value('red'),
        strokeDash=alt.value([5,5]),
        tooltip=['Year:O', 'total_deaths:Q']
    ).properties(
        title='Trend Line'
    )

    # Add legend configuration
    chart = (line + regression).properties(
        width="container",
        height=500,
        title=f'Year-wise Deaths for {selected_cause}'
    ).configure_title(
        fontSize=20,
        font='Arial',
        anchor='middle',
        color='White'
    ).configure_legend(
        orient='bottom-right',
        title=None,
        labelFontSize=12,
        symbolStrokeWidth=2
    )

    st.altair_chart(chart, use_container_width=True)
    
elif viz_type == 'Year wise Pie Chart':
    death_by_state = death_db.copy()
    death_by_state = death_by_state[death_by_state['Cause Name'] != 'All causes']
    # group by cause name and year
    death_by_state = death_by_state.groupby(['Cause Name', 'Year']).sum().reset_index()
    death_by_state["Fraction"] = death_by_state.groupby("Year")["Deaths"].apply(lambda x: x / x.sum() )
    # in the fraction column, only keep 2 decimal places

    # Create base chart with selection
    year_selector = alt.binding_select(
        options=sorted(death_by_state['Year'].unique()),
        name='Select Year'
    )

    selection = alt.selection_single(
        fields=['Year'],
        bind=year_selector,
        value=[{'Year': 2017}]
    )

    # Create the pie chart with selection filter
    base = alt.Chart(death_by_state).transform_filter(
        selection
    ).mark_arc().encode(
        theta='Deaths:Q',
        color='Cause Name:N',
        tooltip=[
            alt.Tooltip('Year:O', title='Year'),
            alt.Tooltip('Fraction:Q', title='Percentage', format='.1%'),  # Shows as 45.7%
            alt.Tooltip('Cause Name:N', title='Cause of Death')
        ]
    ).properties(
        title=alt.TitleParams(
            text='Deaths by Cause in the US',
        ),
        width=650,
        height=650
    )

    # Add percentage labels
    labels = base.transform_aggregate(
        total='sum(Deaths)',
        groupby=['Cause Name']
    ).transform_calculate(
        percentage="datum.Deaths / datum.total * 100"
    ).encode(
        text=alt.Text('percentage:Q', format='.1f')
    )

    # Combine chart with selection
    final_chart = (base + labels).add_selection(selection)
    final_chart = final_chart.configure_mark(
        strokeOpacity=0,
        strokeWidth=0
    )
    st.altair_chart(final_chart)

else:
    death_by_state = death_db.copy()
    death_by_state = death_by_state[death_by_state['Cause Name'] == 'All causes']
    death_by_state = death_by_state[death_by_state['State'] != 'United States']
    selected_year = st.selectbox("Select Year", sorted(death_by_state['Year'].unique()))
    filtered_data = death_by_state[death_by_state['Year'] == selected_year]
    filtered_data['id'] = filtered_data['State'].apply(lambda x: state_fips[x])
    # Create the chart with filtered data
    # Create the chart
    chart = alt.Chart(states).mark_geoshape(
        stroke='white',
        strokeWidth=1
    ).encode(
        color=alt.Color(
            'Age-adjusted Death Rate:Q',
            scale=alt.Scale(
                scheme='darkgreen',
                reverse=False,  # Reverse the color scheme
                domain=[
                    filtered_data['Age-adjusted Death Rate'].min(),
                    filtered_data['Age-adjusted Death Rate'].max()
                ],
                type='sqrt'
            ),
            title='Death Rate'
        ),
        tooltip=[
            alt.Tooltip('State:N', title='State'),
            alt.Tooltip('Age-adjusted Death Rate:Q', title='Death Rate'),
            alt.Tooltip('Year:O', title='Year')
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(filtered_data, 'id', [
            'State', 
            'Age-adjusted Death Rate',
            'Year'
        ])
    ).project(
        type='albersUsa'
    ).properties(
        width=800,
        height=500,
        title=f'Age-Adjusted Death Rates by State ({selected_year})'
    )
    

    final_chart = chart
    st.altair_chart(final_chart)
