import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gamma, norm
import plotly.express as px
from folium import Choropleth
from branca.colormap import linear
import folium


def calculate_spi(precip_series, scale=1):
    """Calculate Standardized Precipitation Index (SPI) for a given precipitation series."""
    precip_rolling = precip_series.rolling(window=scale).sum().dropna()
    shape, loc, scale_param = gamma.fit(precip_rolling, floc=0)
    gamma_cdf = gamma.cdf(precip_rolling, shape, loc=loc, scale=scale_param)
    spi_values = norm.ppf(gamma_cdf)
    return pd.Series(spi_values, index=precip_rolling.index)


def calculate_spi_for_regions(zambia_rain_df):
    """Calculate 1-month and 3-month SPI for all regions in the dataset."""
    spi_records = []

    admin2_names = zambia_rain_df['admin2_name'].unique()
    for admin2 in admin2_names:
        region_data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2][['date', 'precipitation']]
        region_data.set_index('date', inplace=True)
        region_data = region_data.groupby(region_data.index).mean()

        # Calculate SPI for 1-month and 3-month scales
        for scale in [1, 3]:
            spi_values = calculate_spi(region_data['precipitation'], scale=scale)
            for date, spi_value in spi_values.items():
                spi_records.append({
                    'admin2_name': admin2,
                    'spi_scale': scale,
                    'time_scale': f"{scale}_month",
                    'date': date,
                    'spi_value': spi_value
                })

    return pd.DataFrame(spi_records)


def plot_spi(spi_results_df, region_dropdown, selected_spi_scale):
    """
    Generate a Plotly SPI plot for the selected region and SPI scale.
    """
    # Filter data for the selected region and SPI scale
    filtered_data = spi_results_df[
        (spi_results_df['admin2_name'] == region_dropdown) &
        (spi_results_df['spi_scale'] == selected_spi_scale)
    ]

    if filtered_data.empty:
        raise ValueError(f"No data available for {region_dropdown} with SPI scale {selected_spi_scale}.")

    # Create the figure
    fig = go.Figure()

    # Add the selected SPI data to the plot
    fig.add_trace(
        go.Scatter(
            x=filtered_data['date'],
            y=filtered_data['spi_value'],
            mode="lines",
            name=f"{region_dropdown}_SPI_{selected_spi_scale}",
            line=dict(color="blue"),
        )
    )

    # Add drought category reference lines
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    fig.add_hline(y=-1, line_dash="dash", line_color="orange")
    fig.add_hline(y=-1.5, line_dash="dash", line_color="red")
    fig.add_hline(y=-2, line_dash="dash", line_color="darkred")

    # Configure layout
    fig.update_layout(
        title=f"Standardized Precipitation Index (SPI) for {region_dropdown} (SPI Scale: {selected_spi_scale})",
        xaxis_title="Date",
        yaxis_title="SPI Value",
        height=600,
        margin=dict(l=40, r=40, t=60, b=100),
        template="plotly_white",
    )

    # Add SPI categories as a legend below the plot
    fig.add_annotation(
        text=(
            "<b>SPI Categories:</b> "
            "<span style='color:black'>Neutral (SPI=0)</span>, "
            "<span style='color:orange'>Mild Drought (SPI=-1)</span>, "
            "<span style='color:red'>Moderate Drought (SPI=-1.5)</span>, "
            "<span style='color:darkred'>Severe Drought (SPI=-2)</span>"
        ),
        align="center",
        showarrow=False,
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.2,  # Adjusted for correct positioning below the plot
        bordercolor="black",
        borderwidth=1,
        bgcolor="white",
        font=dict(size=12),
    )

    return fig


def characterize_drought_events(spi_results_df, spi_threshold=-1.0):
    """Characterize drought events based on the restructured SPI DataFrame."""
    drought_events = []

    for region, group in spi_results_df.groupby(['admin2_name', 'spi_scale']):
        admin2_name, spi_scale = region
        group = group.sort_values('date')

        in_drought = False
        start_date = None
        severity = 0
        drought_event_count = 0

        for _, row in group.iterrows():
            spi_value = row['spi_value']
            if spi_value < spi_threshold:
                if not in_drought:
                    in_drought = True
                    start_date = row['date']
                    severity = spi_value
                    drought_event_count += 1
                else:
                    severity += spi_value
            else:
                if in_drought:
                    in_drought = False
                    end_date = row['date']
                    duration = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days // 30
                    intensity = severity / duration if duration > 0 else 0
                    drought_events.append({
                        'admin2_name': admin2_name,
                        'spi_scale': spi_scale,
                        'Drought Event': drought_event_count,
                        'Drought Duration (months)': duration,
                        'Drought Severity': severity,
                        'Drought Intensity': intensity,
                        'Drought Start': start_date,
                        'Drought End': end_date
                    })

    return pd.DataFrame(drought_events)


'''
def interactive_drought_event_frequency_plot(drought_events_df, selected_spi_scale):
    """
    Create a Plotly bar chart for drought event frequencies based on the selected SPI scale.

    Parameters:
    drought_events_df (pd.DataFrame): The DataFrame containing drought event data.
    selected_spi_scale (int): The selected SPI scale.

    Returns:
    fig: A Plotly figure object.
    """
    # Filter data for the selected SPI scale
    filtered_df = (
        drought_events_df[drought_events_df['spi_scale'] == selected_spi_scale]
        .groupby('admin2_name')['Drought Event']
        .nunique()
        .reset_index()
        .rename(columns={'Drought Event': 'Drought Event Frequency'})
    )

    if filtered_df.empty:
        raise ValueError(f"No data available for SPI scale {selected_spi_scale}.")

    # Create the Plotly bar chart
    fig = px.bar(
        filtered_df,
        x='admin2_name',
        y='Drought Event Frequency',
        title=f"Frequency of Drought Events by Admin2 (SPI_{selected_spi_scale})",
        labels={'admin2_name': 'Admin2 Name', 'Drought Event Frequency': 'Frequency'},
        color='Drought Event Frequency',
        color_continuous_scale='Blues',
    )

    # Update layout for cleaner scrolling
    fig.update_layout(
        xaxis=dict(
            title="Admin2 Name",
            tickangle=90,  # Make admin2 names vertical
            automargin=True,
            tickmode='linear',
        ),
        yaxis=dict(title="Drought Event Frequency"),
        title_x=0.5,
        margin=dict(t=100, b=200),
        width=1400,
        height=600,
        dragmode="pan",
    )
    return fig
'''

'''
def create_drought_event_frequency_map(drought_events_df, boundaries_gdf, selected_spi_scale):
    """
    Create a Folium map for visualizing drought event frequencies by admin2 regions.

    Parameters:
    - drought_events_df (pd.DataFrame): DataFrame containing drought event details.
    - boundaries_gdf (gpd.GeoDataFrame): GeoDataFrame containing admin2 boundaries.
    - selected_spi_scale (int): Selected SPI scale for filtering.

    Returns:
    - folium.Map: A Folium map object.
    """
    # Filter the drought events for the selected SPI scale
    filtered_df = (
        drought_events_df[drought_events_df['spi_scale'] == selected_spi_scale]
        .groupby('admin2_name')['Drought Event']
        .nunique()
        .reset_index()
        .rename(columns={'Drought Event': 'Drought Event Frequency'})
    )

    if filtered_df.empty:
        raise ValueError(f"No data available for SPI scale {selected_spi_scale}.")

    # Merge with boundaries to include geometry
    merged_gdf = boundaries_gdf[['admin2_name', 'geometry']].merge(
        filtered_df, on='admin2_name', how='left'
    )

    # Set up the map
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6, tiles="cartodbpositron")

    # Define a color scale
    color_scale = linear.Blues_09.scale(
        merged_gdf['Drought Event Frequency'].min(),
        merged_gdf['Drought Event Frequency'].max()
    )

    # Add regions to the map
    for _, row in merged_gdf.iterrows():
        value = row['Drought Event Frequency']
        color = color_scale(value) if pd.notnull(value) else "gray"
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(
                f"Name: {row['admin2_name']}<br>Event Frequency: {value}" if pd.notnull(value) else "No Data"
            ),
        ).add_to(m)

    # Add the color scale to the map
    color_scale.caption = f"Drought Event Frequency (SPI {selected_spi_scale})"
    color_scale.add_to(m)

    return m
'''

def prepare_drought_event_frequency_data(boundaries_gdf, drought_events_df, selected_spi_scale):
    """
    Prepare data for drought event frequency mapping.

    Parameters:
    - boundaries_gdf (gpd.GeoDataFrame): GeoDataFrame containing admin2 boundaries with geometry.
    - drought_events_df (pd.DataFrame): DataFrame containing drought event details.
    - selected_spi_scale (int): Selected SPI scale to filter the data.

    Returns:
    - gpd.GeoDataFrame: GeoDataFrame containing drought event frequency and geometry.
    """
    # Filter drought events for the selected SPI scale
    filtered_df = (
        drought_events_df[drought_events_df['spi_scale'] == selected_spi_scale]
        .groupby('admin2_name')['Drought Event']
        .nunique()
        .reset_index()
        .rename(columns={'Drought Event': 'event_frequency'})
    )

    if filtered_df.empty:
        raise ValueError(f"No data available for SPI scale {selected_spi_scale}.")

    # Merge event frequency with boundaries (geometry)
    merged_gdf = boundaries_gdf[['admin2_name', 'geometry']].merge(
        filtered_df, on='admin2_name', how='left'
    )

    return merged_gdf


def create_drought_event_frequency_map(prepared_gdf, selected_spi_scale):
    """
    Create a Folium map for visualizing drought event frequencies by admin2 regions.

    Parameters:
    - prepared_gdf (gpd.GeoDataFrame): GeoDataFrame containing drought event frequencies and geometry.
    - selected_spi_scale (int): Selected SPI scale for display in the map caption.

    Returns:
    - folium.Map: A Folium map object.
    """
    # Set up the map
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6, tiles="cartodbpositron")

    # Define a color scale
    color_scale = linear.YlOrRd_09.scale(
        prepared_gdf['event_frequency'].min(),
        prepared_gdf['event_frequency'].max()
    )

    # Add regions to the map
    for _, row in prepared_gdf.iterrows():
        value = row["event_frequency"]
        color = color_scale(value) if pd.notnull(value) else "gray"
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(
                f"Name: {row['admin2_name']}<br>Event Frequency: {value}" if pd.notnull(value) else "No Data"
            ),
        ).add_to(m)

    # Add the color scale to the map
    color_scale.caption = f"Drought Event Frequency (SPI {selected_spi_scale})"
    color_scale.add_to(m)

    return m


def prepare_drought_characteristics_data(drought_events_gdf, selected_spi_scale, selected_characteristic):
    """
    Prepare data for drought characteristics mapping.

    Parameters:
    - drought_events_gdf (gpd.GeoDataFrame): GeoDataFrame containing drought event details and geometry.
    - selected_spi_scale (int): Selected SPI scale for filtering.
    - selected_characteristic (str): Selected drought characteristic to process.

    Returns:
    - gpd.GeoDataFrame: A GeoDataFrame containing the mean values and geometry for mapping.
    """
    # Filter the drought events for the selected SPI scale
    filtered_gdf = drought_events_gdf[drought_events_gdf['spi_scale'] == selected_spi_scale]

    if filtered_gdf.empty:
        raise ValueError(f"No data available for SPI scale {selected_spi_scale}.")

    # Calculate mean values for the selected characteristic
    mean_values = (
        filtered_gdf.groupby('admin2_name')[selected_characteristic]
        .mean()
        .reset_index()
        .rename(columns={selected_characteristic: 'mean_value'})
    )

    # Merge with geometry
    merged_gdf = filtered_gdf[['admin2_name', 'geometry']].drop_duplicates().merge(
        mean_values, on='admin2_name', how='left'
    )

    return merged_gdf



def create_drought_characteristics_map(prepared_gdf, selected_spi_scale, selected_characteristic):
    """
    Create a Folium map for visualizing mean drought characteristics by admin2 regions.

    Parameters:
    - prepared_gdf (gpd.GeoDataFrame): Pre-processed GeoDataFrame containing drought event details and geometry.
    - selected_spi_scale (int): Selected SPI scale for display in the map caption.
    - selected_characteristic (str): Selected drought characteristic to visualize.

    Returns:
    - folium.Map: A Folium map object.
    """
    # Set up the map
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6, tiles="cartodbpositron")

    # Define a color scale
    color_scale = linear.YlOrRd_09.scale(
        prepared_gdf['mean_value'].min(),
        prepared_gdf['mean_value'].max()
    )

    # Add regions to the map
    for _, row in prepared_gdf.iterrows():
        value = row["mean_value"]
        color = color_scale(value) if pd.notnull(value) else "gray"
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(
                f"Name: {row['admin2_name']}<br>Mean {selected_characteristic}: {value:.2f}" if pd.notnull(value) else "No Data"
            ),
        ).add_to(m)

    # Add the color scale to the map
    color_scale.caption = f"Mean {selected_characteristic} (SPI {selected_spi_scale})"
    color_scale.add_to(m)

    return m



def plot_drought_characteristics(df, selected_spi_scale, selected_characteristic):
    """
    Generate a Plotly box plot for drought characteristics by SPI scale.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    - selected_spi_scale (int): The selected SPI scale for filtering.
    - selected_characteristic (str): The drought characteristic to plot.

    Returns:
    - fig: A Plotly figure object.
    """
    # Filter data for the selected SPI scale
    filtered_df = df[df['spi_scale'] == selected_spi_scale]

    if filtered_df.empty:
        raise ValueError(f"No data available for SPI scale {selected_spi_scale}.")

    if selected_characteristic not in filtered_df.columns:
        raise ValueError(f"Characteristic '{selected_characteristic}' is not available in the DataFrame.")

    # Create the Plotly box plot
    fig = px.box(
        filtered_df,
        x='admin2_name',
        y=selected_characteristic,
        title=f'{selected_characteristic} by Admin2 Level (SPI_{selected_spi_scale})',
        labels={'admin2_name': 'Admin2 Level', selected_characteristic: selected_characteristic},
        color_discrete_sequence=['rgba(31, 119, 180, 0.8)']
    )

    # Update layout for better visualization
    fig.update_layout(
        xaxis=dict(
            title="Admin2 Level",
            tickangle=45,
            automargin=True,
            tickmode='linear',
        ),
        yaxis=dict(title=selected_characteristic),
        title_x=0.5,
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        margin=dict(t=50, b=150),
        width=1400,
        height=600,
    )

    return fig


def create_drought_characteristics_map(drought_events_gdf, selected_spi_scale, selected_characteristic):
    """
    Create a Folium map for visualizing mean drought characteristics by admin2 regions.

    Parameters:
    - drought_events_gdf (gpd.GeoDataFrame): GeoDataFrame containing drought event details and geometry.
    - selected_spi_scale (int): Selected SPI scale for filtering.
    - selected_characteristic (str): Selected drought characteristic to visualize.

    Returns:
    - folium.Map: A Folium map object.
    """
    # Filter the drought events for the selected SPI scale
    filtered_gdf = drought_events_gdf[drought_events_gdf['spi_scale'] == selected_spi_scale]

    if filtered_gdf.empty:
        raise ValueError(f"No data available for SPI scale {selected_spi_scale}.")

    # Calculate mean values for the selected characteristic
    mean_values = (
        filtered_gdf.groupby('admin2_name')[selected_characteristic]
        .mean()
        .reset_index()
        .rename(columns={selected_characteristic: 'mean_value'})
    )

    # Merge with geometry
    merged_gdf = filtered_gdf[['admin2_name', 'geometry']].drop_duplicates().merge(
        mean_values, on='admin2_name', how='left'
    )

    # Set up the map
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6, tiles="cartodbpositron")

    # Define a color scale
    color_scale = linear.YlOrRd_09.scale(
        merged_gdf['mean_value'].min(),
        merged_gdf['mean_value'].max()
    )

    # Add regions to the map
    for _, row in merged_gdf.iterrows():
        value = row["mean_value"]
        color = color_scale(value) if pd.notnull(value) else "gray"
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(
                f"Name: {row['admin2_name']}<br>Mean {selected_characteristic}: {value:.2f}" if pd.notnull(value) else "No Data"
            ),
        ).add_to(m)

    # Add the color scale to the map
    color_scale.caption = f"Mean {selected_characteristic} (SPI {selected_spi_scale})"
    color_scale.add_to(m)

    return m


