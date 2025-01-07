# Imports
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import mpld3
from mpld3 import plugins
import plotly.express as px
import plotly.graph_objects as go
import ipywidgets as widgets
from ipywidgets import Dropdown, Output
from IPython.display import display, clear_output
import pymannkendall as mk
import folium
import branca


############################################################################################

# Function to characterize drought events when the SPI (1 or 3) falls below -1.0 

############################################################################################


def characterize_drought_events(spi_results_df, spi_threshold=-1.0):
    """
    Characterize drought events based on SPI values for each region (admin2_name), time scale, and SPI scale.

    Parameters:
    spi_results_df (pd.DataFrame): Input DataFrame with SPI values for different regions and time scales.
    spi_threshold (float): Threshold for defining a drought event (default is -1.0 for moderate drought).

    Returns:
    pd.DataFrame: Output DataFrame containing drought event details for each region, SPI scale, and time scale.
    """
    drought_events = []

    for column in spi_results_df.columns:
        # Extract admin2_name, SPI scale, and time scale
        parts = column.split('_')
        admin2_name = '_'.join(parts[:-2])  # All parts except the last two
        spi_scale = int(parts[-2])  # Second-to-last part is the SPI scale
        time_scale = parts[-1]  # Last part is the time scale (e.g., "month")

        spi_series = spi_results_df[column].dropna()
        spi_series = spi_series.sort_index()

        in_drought = False
        start_date = None
        severity = 0
        drought_event_count = 0

        for date, spi_value in spi_series.items():
            if spi_value < spi_threshold:
                if not in_drought:
                    in_drought = True
                    start_date = date
                    severity = spi_value
                    drought_event_count += 1
                else:
                    severity += spi_value
            else:
                if in_drought:
                    in_drought = False
                    end_date = date
                    # Calculate duration using year-month differences
                    duration = (
                        pd.Period(end_date, freq='M') - pd.Period(start_date, freq='M')
                    ).n  # Extract the number of months
                    intensity = -severity / duration if duration > 0 else 0  # Ensure intensity is positive
                    drought_events.append({
                        'admin2_name': admin2_name,
                        'spi_scale': spi_scale,
                        'time_scale': time_scale,
                        'Drought Event': drought_event_count,
                        'Drought Duration (months)': duration,
                        'Drought Severity': severity,
                        'Drought Intensity': intensity,
                        'Drought Start': start_date,
                        'Drought End': end_date
                    })

        if in_drought:
            end_date = spi_series.index[-1]
            duration = (
                pd.Period(end_date, freq='M') - pd.Period(start_date, freq='M')
            ).n  # Extract the number of months
            intensity = -severity / duration if duration > 0 else 0  # Ensure intensity is positive
            drought_events.append({
                'admin2_name': admin2_name,
                'spi_scale': spi_scale,
                'time_scale': time_scale,
                'Drought Event': drought_event_count,
                'Drought Duration (months)': duration,
                'Drought Severity': severity,
                'Drought Intensity': intensity,
                'Drought Start': start_date,
                'Drought End': end_date
            })

    return pd.DataFrame(drought_events)


############################################################################################

'''
Creates histogram of the drought duration, severity, and intensity for each admin2 zone
for each SPI (1 or 3) scale 
'''

############################################################################################


def plot_interactive_histogram_plotly(drought_events_df):
    """
    Creates an interactive histogram or density plot using Plotly for selected drought characteristics.

    Parameters:
    - drought_events_df (pd.DataFrame): The DataFrame containing drought events and their characteristics.
    """
    # Dropdown options
    admin2_name_options = drought_events_df['admin2_name'].unique().tolist()
    variable_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']
    spi_options = drought_events_df['spi_scale'].unique().tolist()

    # Create initial selections
    initial_admin2 = admin2_name_options[0]
    initial_variable = variable_options[0]
    initial_spi = spi_options[0]

    # Filter DataFrame for initial selections
    filtered_df = drought_events_df[
        (drought_events_df['admin2_name'] == initial_admin2) &
        (drought_events_df['spi_scale'] == initial_spi)
    ]

    fig = go.Figure()

    # Add initial histogram trace
    fig.add_trace(
        go.Histogram(
            x=filtered_df[initial_variable],
            nbinsx=20,
            marker=dict(color='skyblue', line=dict(color='black', width=1)),
            name=f"{initial_admin2} - {initial_variable} (SPI{initial_spi})"
        )
    )

    # Add layout
    fig.update_layout(
        title=dict(
            text=f"Distribution of {initial_variable} for {initial_admin2} (SPI{initial_spi})",
            x=0.5,  # Center the title horizontally
            y=0.95,  # Slightly above the default position
            font=dict(size=20)  # Adjust title font size
        ),
        xaxis_title=initial_variable,
        yaxis_title='Frequency',
        bargap=0.2,
        template='plotly_white',
        updatemenus=[
            # Dropdown for Admin2 Name
            {
                "buttons": [
                    {
                        "method": "update",
                        "label": admin2_name,
                        "args": [
                            {"x": [drought_events_df[
                                (drought_events_df['admin2_name'] == admin2_name) &
                                (drought_events_df['spi_scale'] == initial_spi)
                            ][initial_variable]]},
                            {"title": f"Distribution of {initial_variable} for {admin2_name} (SPI{initial_spi})"}
                        ]
                    }
                    for admin2_name in admin2_name_options
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.1,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top"
            },
            # Dropdown for SPI Scale
            {
                "buttons": [
                    {
                        "method": "update",
                        "label": f"SPI{spi}",
                        "args": [
                            {"x": [drought_events_df[
                                (drought_events_df['admin2_name'] == initial_admin2) &
                                (drought_events_df['spi_scale'] == spi)
                            ][initial_variable]]},
                            {"title": f"Distribution of {initial_variable} for {initial_admin2} (SPI{spi})"}
                        ]
                    }
                    for spi in spi_options
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.3,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top"
            },
            # Dropdown for Variable
            {
                "buttons": [
                    {
                        "method": "update",
                        "label": variable,
                        "args": [
                            {"x": [drought_events_df[
                                (drought_events_df['admin2_name'] == initial_admin2) &
                                (drought_events_df['spi_scale'] == initial_spi)
                            ][variable]]},
                            {"title": f"Distribution of {variable} for {initial_admin2} (SPI{initial_spi})",
                             "xaxis.title": variable}
                        ]
                    }
                    for variable in variable_options
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.5,
                "y": 1.15,
                "xanchor": "left",
                "yanchor": "top"
            }
        ]
    )

    # Show the plot
    fig.show()

    
    
############################################################################################

# Drought Frequency Functions 

############################################################################################


# 1. Get Drought Event Frequency for admin2
def get_drought_event_frequency(df):
    """
    Computes the drought event frequency grouped by admin2_name and spi_scale.

    Parameters:
    - df (GeoDataFrame): Input GeoDataFrame containing 'admin2_name', 'spi_scale', 'Drought Event', and 'geometry'.

    Returns:
    - GeoDataFrame: A GeoDataFrame with 'admin2_name', 'spi_scale', 'Drought Event Frequency', and 'geometry',
      ensuring the CRS is set to EPSG:4326.
    """
    # Group data to compute the frequency
    frequency_df = (
        df.groupby(['admin2_name', 'spi_scale'])
        .agg({'Drought Event': 'nunique', 'geometry': 'first'})
        .reset_index()
        .rename(columns={'Drought Event': 'Drought Event Frequency'})
    )
    
    # Convert to GeoDataFrame and ensure CRS
    frequency_gdf = gpd.GeoDataFrame(frequency_df, geometry='geometry')
    
    # Check if CRS is set, otherwise set it
    if frequency_gdf.crs is None:
        frequency_gdf.set_crs("EPSG:4326", inplace=True)
    else:
        frequency_gdf.to_crs("EPSG:4326", inplace=True)

    return frequency_gdf

# 2. Filter Admin2 Zones by Cluster
def get_admin2_zones_by_cluster(df, cluster_type, cluster_value, spi_scale):
    filtered_df = df[
        (df[cluster_type] == cluster_value) & (df['spi_scale'] == spi_scale)
    ]
    frequency_df = (
        filtered_df.groupby(['admin2_name', 'spi_scale'])
        .agg({'Drought Event': 'nunique', 'geometry': 'first'})
        .reset_index()
        .rename(columns={'Drought Event': 'Drought Event Frequency'})
    )
    return gpd.GeoDataFrame(frequency_df, geometry='geometry')

# 3. Drought Event Histogram
def drought_event_histogram(filtered_df, spi_scale, cluster_type="admin2"):
    # Dynamically choose x-axis column
    x_column = "admin2_name"

    # Create bar plot
    fig = px.bar(
        filtered_df,
        x=x_column,
        y="Drought Event Frequency",
        title=f"Drought Event Frequency by {x_column.capitalize()} ({spi_scale})",
        labels={
            x_column: x_column.capitalize(),
            "Drought Event Frequency": "Frequency",
        },
        color="Drought Event Frequency",
        color_continuous_scale="Blues",
    )

    # Display the figure
    fig.show()

# 4. Interactive Drought Analysis Tool
def interactive_drought_analysis_tool(df, aggregation_level):
    if aggregation_level not in ["admin2", "cluster"]:
        raise ValueError("Invalid aggregation_level. Must be 'admin2' or 'cluster'.")

    spi_options = df['spi_scale'].unique().tolist()
    spi_dropdown = Dropdown(
        options=[f"SPI_{int(spi)}" for spi in spi_options],
        description="Select SPI Scale:",
        style={'description_width': 'initial'}
    )

    cluster_type_dropdown = None
    cluster_dropdown = None
    if aggregation_level == "cluster":
        cluster_type_dropdown = Dropdown(
            options=["cluster", "hierarchical_cluster"],
            description="Select Cluster Type:",
            style={'description_width': 'initial'}
        )
        cluster_dropdown = Dropdown(
            options=[],
            description="Select Cluster:",
            style={'description_width': 'initial'}
        )

    def update_clusters(change=None):
        selected_cluster_type = cluster_type_dropdown.value
        if selected_cluster_type:
            cluster_options = sorted(df[selected_cluster_type].unique().tolist())
            cluster_dropdown.options = cluster_options

    def update_visualization(change=None):
        clear_output(wait=True)
        display(spi_dropdown)
        if aggregation_level == "cluster":
            display(cluster_type_dropdown, cluster_dropdown)

        selected_spi = int(spi_dropdown.value.split("_")[1])

        if aggregation_level == "admin2":
            filtered_df = df[df['spi_scale'] == selected_spi]
            if filtered_df.empty:
                print(f"No data available for SPI_{selected_spi}.")
                return
            frequency_df = get_drought_event_frequency(filtered_df)

        elif aggregation_level == "cluster":
            selected_cluster_type = cluster_type_dropdown.value
            selected_cluster = cluster_dropdown.value
            if not selected_cluster_type or not selected_cluster:
                print("Please select both a cluster type and a cluster.")
                return
            frequency_df = get_admin2_zones_by_cluster(
                df, selected_cluster_type, selected_cluster, selected_spi
            )

        # Generate the histogram
        drought_event_histogram(frequency_df, f"SPI_{selected_spi}", cluster_type=aggregation_level)

    # Attach observers
    spi_dropdown.observe(update_visualization, names="value")
    if aggregation_level == "cluster":
        cluster_type_dropdown.observe(update_clusters, names="value")
        cluster_dropdown.observe(update_visualization, names="value")

    # Initial display
    display(spi_dropdown)
    if aggregation_level == "cluster":
        display(cluster_type_dropdown, cluster_dropdown)


############################################################################################

# Drought Frequency Map Functions

############################################################################################


def map_drought_frequency_with_spi_scale(
    drought_frequency_df, 
    spi_scale,
    cluster_boundaries_df=None, 
    cluster_type=None, 
    region_column="admin2_name"
):
    """
    Create a map for a specific SPI scale, showing drought frequency by region,
    with optional cluster boundaries.

    Parameters:
    - drought_frequency_df (GeoDataFrame): GeoDataFrame containing drought frequencies.
    - spi_scale (int): The SPI scale to filter the data (e.g., 1 or 3).
    - cluster_boundaries_df (GeoDataFrame): GeoDataFrame with cluster boundaries (optional).
    - cluster_type (str): 'kmeans' or 'hierarchical' to specify the cluster type (optional).
    - region_column (str): Column name representing regions (default: "admin2_name").
    """
    # Filter the GeoDataFrame for the selected SPI scale
    filtered_df = drought_frequency_df[drought_frequency_df["spi_scale"] == spi_scale]

    # Create the base map
    m = folium.Map(location=[-15.416667, 28.283333], zoom_start=6)

    # Define color scale for drought frequency
    min_freq = filtered_df["Drought Event Frequency"].min()
    max_freq = filtered_df["Drought Event Frequency"].max()
    color_scale = branca.colormap.LinearColormap(
        colors=["#f7fbff", "#6baed6", "#08306b"],  # Light to dark blue
        vmin=min_freq,
        vmax=max_freq,
        caption=f"Drought Event Frequency (SPI {spi_scale})",
    )

    # Add drought frequency regions with tooltips
    for _, row in filtered_df.iterrows():
        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature, freq=row["Drought Event Frequency"]: {
                "fillColor": color_scale(freq),
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.7,
            },
            tooltip=folium.Tooltip(
                f"<b>Region:</b> {row[region_column]}<br>"
                f"<b>Drought Event Frequency (SPI {spi_scale}):</b> {row['Drought Event Frequency']}"
            ),
        ).add_to(m)

    # Add cluster boundaries if provided
    if cluster_boundaries_df is not None:
        boundary_color = "red" if cluster_type == "hierarchical" else "green"
        cluster_id_column = "cluster" if cluster_type == "kmeans" else "hierarchical_cluster"

        for _, row in cluster_boundaries_df.iterrows():
            folium.GeoJson(
                row["geometry"],
                style_function=lambda x: {
                    "fillColor": "none",
                    "color": boundary_color,
                    "weight": 3,  # Thicker boundaries
                    "fillOpacity": 0,
                },
                tooltip=folium.Tooltip(
                    f"<b>Cluster Type:</b> {cluster_type.capitalize()}<br>"
                    f"<b>Cluster ID:</b> {row[cluster_id_column]}"
                ),
            ).add_to(m)

    # Add the color scale to the map
    color_scale.add_to(m)

    return m

############################################################################################

# Boxplot of drought characteristics for each admin2 zone (can change SPI scale)

############################################################################################

def interactive_drought_characteristics_by_spi(df):
    """
    Create an interactive Plotly box plot for drought characteristics,
    with dropdown menus for SPI scale and characteristics.

    Parameters:
    df (pd.DataFrame): The DataFrame containing drought characteristics data.

    Returns:
    None: Displays the interactive dropdown and plot.
    """
    # Dropdown options for drought characteristics
    characteristic_options = ['Drought Intensity', 'Drought Severity', 'Drought Duration (months)']

    # Dropdown options for SPI scale
    spi_options = sorted(df['spi_scale'].unique().tolist())
    spi_dropdown_options = [f"SPI_{int(spi)}" for spi in spi_options]

    # Create dropdown widgets
    characteristic_dropdown = widgets.Dropdown(
        options=characteristic_options,
        description="Select Characteristic:",
        style={'description_width': 'initial'}
    )
    spi_dropdown = widgets.Dropdown(
        options=spi_dropdown_options,
        description="Select SPI Scale:",
        style={'description_width': 'initial'}
    )

    # Function to update the plot
    def update_plot(change=None):
        clear_output(wait=True)  # Clear the current output

        # Display the dropdowns again
        display(spi_dropdown, characteristic_dropdown)

        # Get the selected characteristic and SPI scale
        selected_characteristic = characteristic_dropdown.value
        selected_spi = int(spi_dropdown.value.split("_")[1])

        # Filter data for the selected SPI scale
        filtered_df = df[df['spi_scale'] == selected_spi].copy()

        if selected_characteristic not in filtered_df.columns:
            print(f"Characteristic '{selected_characteristic}' is not available in the DataFrame.")
            return

        if filtered_df.empty:
            print(f"No data available for SPI_{selected_spi}.")
            return

        # Round the selected characteristic values to the nearest thousandth
        filtered_df[selected_characteristic] = filtered_df[selected_characteristic].round(3)

        # Create the Plotly box plot
        fig = px.box(
            filtered_df,
            x='admin2_name',
            y=selected_characteristic,
            title=f'{selected_characteristic} by Admin2 Level (SPI_{selected_spi})',
            labels={'admin2_name': 'Admin2 Level', selected_characteristic: selected_characteristic},
            color_discrete_sequence=['rgba(31, 119, 180, 0.8)']  # Consistent blue color
        )

        # Update layout for better visualization
        fig.update_layout(
            xaxis=dict(
                title="Admin2 Level",
                tickangle=45,
                automargin=True,  # Adjust margins dynamically
                tickmode='linear',  # Show all x-axis labels linearly
            ),
            yaxis=dict(title=selected_characteristic),
            title_x=0.5,  # Center the title
            plot_bgcolor='rgba(240, 240, 240, 0.9)',  # Light background
            margin=dict(t=50, b=150),  # Adjust margins for readability
            width=1400,  # Wider chart for horizontal scrolling
            height=600,  # Adjusted height for better readability
        )

        # Show the plot
        fig.show()

    # Attach the update function to both dropdowns
    characteristic_dropdown.observe(update_plot, names="value")
    spi_dropdown.observe(update_plot, names="value")

    # Display the dropdowns
    display(spi_dropdown, characteristic_dropdown)

    # Trigger the initial plot
    update_plot()

############################################################################################

'''

Scatter plot between either combination of drought duration, drought severity, and drought intensity
for any given drought to help understand correlation

TODO: add in drought start and end date 

'''
############################################################################################
    
def interactive_correlation_analysis_plotly(df):
    """
    Create an interactive Plotly scatter plot for drought characteristics,
    with dropdown menus for SPI scale and x, y characteristics.

    Parameters:
    df (pd.DataFrame): The DataFrame containing drought characteristics data.

    Returns:
    None: Displays the interactive dropdown and plot.
    """
    # Dropdown options for drought characteristics
    characteristic_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']
    
    # Dropdown options for SPI scale
    spi_options = sorted(df['spi_scale'].unique().tolist())
    spi_dropdown_options = [f"SPI_{int(spi)}" for spi in spi_options]

    # Create dropdown widgets
    x_variable_dropdown = widgets.Dropdown(
        options=characteristic_options,
        description="Select X Variable:",
        style={'description_width': 'initial'}
    )
    y_variable_dropdown = widgets.Dropdown(
        options=characteristic_options,
        description="Select Y Variable:",
        style={'description_width': 'initial'}
    )
    spi_dropdown = widgets.Dropdown(
        options=spi_dropdown_options,
        description="Select SPI Scale:",
        style={'description_width': 'initial'}
    )

    # Function to update the plot
    def update_plot(change=None):
        clear_output(wait=True)  # Clear the current output

        # Display the dropdowns again
        display(spi_dropdown, x_variable_dropdown, y_variable_dropdown)

        # Get the selected SPI scale and variables
        selected_spi = int(spi_dropdown.value.split("_")[1])
        selected_x = x_variable_dropdown.value
        selected_y = y_variable_dropdown.value

        # Filter data for the selected SPI scale
        filtered_df = df[df['spi_scale'] == selected_spi].copy()

        # Round values to the nearest thousandth
        filtered_df[selected_x] = filtered_df[selected_x].round(3)
        filtered_df[selected_y] = filtered_df[selected_y].round(3)

        # Check if the selected variables are in the filtered DataFrame
        if selected_x not in filtered_df.columns or selected_y not in filtered_df.columns:
            print(f"One or both selected characteristics are not available in the DataFrame.")
            return

        if filtered_df.empty:
            print(f"No data available for SPI_{selected_spi}.")
            return

        # Create the Plotly scatter plot
        fig = px.scatter(
            filtered_df,
            x=selected_x,
            y=selected_y,
            color='admin2_name',  # Use 'admin2_name' for coloring
            title=f'{selected_y} vs {selected_x} (SPI_{selected_spi})',
            labels={selected_x: selected_x, selected_y: selected_y},
            hover_data=['admin2_name'],  # Add 'admin2_name' to hover info
            opacity=0.7,  # Adjust point transparency for better visibility
            color_discrete_sequence=px.colors.qualitative.T10  # Use a qualitative color palette
        )

        # Customize layout for better visualization
        fig.update_layout(
            xaxis_title=selected_x,
            yaxis_title=selected_y,
            title_x=0.5,  # Center the title
            margin=dict(t=50, b=100),  # Adjust margins for readability
            legend_title="Admin2 Name"
        )

        # Show the plot
        fig.show()

    # Attach the update function to dropdowns
    x_variable_dropdown.observe(update_plot, names="value")
    y_variable_dropdown.observe(update_plot, names="value")
    spi_dropdown.observe(update_plot, names="value")

    # Display the dropdowns
    display(spi_dropdown, x_variable_dropdown, y_variable_dropdown)

    # Trigger the initial plot
    update_plot()


############################################################################################

'''

Summary statistics of SPI1 and SPI3 drought metrics for same admin2 zone

'''

############################################################################################


def interactive_drought_analysis_by_paired_region(df):
    """
    Create an interactive bar chart comparing SPI 1 and SPI 3 drought characteristics for the same regions,
    with dropdown menus for selecting characteristics and aggregation methods.

    Parameters:
    df (pd.DataFrame): The DataFrame containing drought characteristics data.

    Returns:
    None: Displays the interactive dropdown and plot.
    """
    characteristic_options = ['Drought Intensity', 'Drought Severity', 'Drought Duration (months)']
    aggregation_options = ['Mean', 'Median', 'Max']

    spi_scales = [1, 3]
    if not set(spi_scales).issubset(df['spi_scale'].unique()):
        print(f"SPI scales {spi_scales} not available in the data.")
        return

    characteristic_dropdown = widgets.Dropdown(
        options=characteristic_options,
        description="Select Characteristic:",
        style={'description_width': 'initial'}
    )
    aggregation_dropdown = widgets.Dropdown(
        options=aggregation_options,
        description="Select Aggregation:",
        style={'description_width': 'initial'}
    )

    def update_plot(change=None):
        clear_output(wait=True)
        display(characteristic_dropdown, aggregation_dropdown)

        selected_characteristic = characteristic_dropdown.value
        selected_aggregation = aggregation_dropdown.value.lower()

        if selected_characteristic not in df.columns:
            print(f"Characteristic '{selected_characteristic}' is not available in the DataFrame.")
            return

        filtered_df = df[df['spi_scale'].isin(spi_scales)]

        if selected_aggregation == 'max':
            max_df = (
                filtered_df.loc[
                    filtered_df.groupby(['admin2_name', 'spi_scale'])[selected_characteristic].idxmax()
                ][['admin2_name', 'spi_scale', selected_characteristic, 'Drought Start', 'Drought End']]
            )

            pivot_df = (
                max_df.pivot(index='admin2_name', columns='spi_scale', values=selected_characteristic)
                .reset_index()
                .rename(columns={1: 'SPI_1', 3: 'SPI_3'})
            )
            pivot_df['SPI_1'] = pivot_df['SPI_1'].round(3)
            pivot_df['SPI_3'] = pivot_df['SPI_3'].round(3)

            hover_data = (
                max_df.pivot(index='admin2_name', columns='spi_scale', values=['Drought Start', 'Drought End'])
                .reset_index()
            )
            hover_data.columns = ['admin2_name'] + [
                f"{col[1]} {col[0]}" for col in hover_data.columns if col[0] != 'admin2_name'
            ]

            melted_df = pivot_df.melt(id_vars='admin2_name', var_name='SPI Scale', value_name=selected_characteristic)
            melted_df = melted_df.merge(hover_data, on='admin2_name', how='left')

            melted_df['Drought Start'] = melted_df.apply(
                lambda row: row['1 Drought Start'] if row['SPI Scale'] == 'SPI_1' else row['3 Drought Start'], axis=1
            )
            melted_df['Drought End'] = melted_df.apply(
                lambda row: row['1 Drought End'] if row['SPI Scale'] == 'SPI_1' else row['3 Drought End'], axis=1
            )
        else:
            grouped_df = (
                filtered_df.groupby(['admin2_name', 'spi_scale'])[selected_characteristic]
                .agg(selected_aggregation)
                .reset_index()
                .pivot(index='admin2_name', columns='spi_scale', values=selected_characteristic)
                .reset_index()
                .rename(columns={1: 'SPI_1', 3: 'SPI_3'})
            )
            grouped_df['SPI_1'] = grouped_df['SPI_1'].round(3)
            grouped_df['SPI_3'] = grouped_df['SPI_3'].round(3)
            melted_df = grouped_df.melt(id_vars='admin2_name', var_name='SPI Scale', value_name=selected_characteristic)

        hover_info = None
        if selected_aggregation == 'max':
            hover_info = {
                'SPI Scale': False,
                selected_characteristic: True,
                'Drought Start': True,
                'Drought End': True,
            }

        fig = px.bar(
            melted_df,
            x='admin2_name',
            y=selected_characteristic,
            color='SPI Scale',
            barmode='group',
            title=f'{selected_characteristic} Comparison for SPI 1 and SPI 3 ({selected_aggregation.capitalize()})',
            labels={'admin2_name': 'Region', selected_characteristic: selected_characteristic},
            color_discrete_map={'SPI_1': 'blue', 'SPI_3': 'orange'},
            hover_data=hover_info if selected_aggregation == 'max' else None
        )

        fig.update_layout(
            xaxis=dict(title="Region", tickangle=45, automargin=True, tickmode='linear'),
            yaxis=dict(title=f"{selected_aggregation.capitalize()} {selected_characteristic}"),
            title_x=0.5,
            plot_bgcolor='rgba(240, 240, 240, 0.9)',
            margin=dict(t=50, b=150),
            width=1200,
            height=600,
        )

        fig.show()

    characteristic_dropdown.observe(update_plot, names="value")
    aggregation_dropdown.observe(update_plot, names="value")
    display(characteristic_dropdown, aggregation_dropdown)
    update_plot()
    

############################################################################################

'''

Temporal heat map function, but may delete 

'''

############################################################################################

    
'''

def interactive_temporal_heatmap_2year(df):
    """
    Create an interactive temporal heatmap for drought characteristics,
    with dropdown menus for SPI scale and characteristics, grouped by 2-year blocks.

    Parameters:
    df (pd.DataFrame): The DataFrame containing drought characteristics data.

    Returns:
    None: Displays the interactive dropdown and plot.
    """
    # Dropdown options for drought characteristics
    characteristic_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']
    
    # Dropdown options for SPI scale
    spi_options = sorted(df['spi_scale'].unique().tolist())
    spi_dropdown_options = [f"SPI_{int(spi)}" for spi in spi_options]

    # Create dropdown widgets
    characteristic_dropdown = widgets.Dropdown(
        options=characteristic_options,
        description="Select Characteristic:",
        style={'description_width': 'initial'}
    )
    spi_dropdown = widgets.Dropdown(
        options=spi_dropdown_options,
        description="Select SPI Scale:",
        style={'description_width': 'initial'}
    )

    # Function to update the plot
    def update_plot(change=None):
        clear_output(wait=True)  # Clear the current output

        # Display the dropdowns again
        display(spi_dropdown, characteristic_dropdown)

        # Get the selected characteristic and SPI scale
        selected_characteristic = characteristic_dropdown.value
        selected_spi = int(spi_dropdown.value.split("_")[1])

        # Filter data for the selected SPI scale
        filtered_df = df[df['spi_scale'] == selected_spi].copy()

        if selected_characteristic not in filtered_df.columns:
            print(f"Characteristic '{selected_characteristic}' is not available in the DataFrame.")
            return

        if filtered_df.empty:
            print(f"No data available for SPI_{selected_spi}.")
            return

        # Convert 'Drought Start' to datetime and extract 2-year blocks
        filtered_df['Drought Start'] = pd.to_datetime(filtered_df['Drought Start'], errors='coerce')
        filtered_df['2-Year Block'] = (
            (filtered_df['Drought Start'].dt.year // 2) * 2
        ).astype(str) + " - " + (
            ((filtered_df['Drought Start'].dt.year // 2) * 2 + 1).astype(str)
        )

        # Create a pivot table with 'admin2_name' as the index, '2-Year Block' as columns
        heatmap_data = filtered_df.pivot_table(
            index='admin2_name',
            columns='2-Year Block',
            values=selected_characteristic,
            aggfunc='sum'  # Compute the sum
        )

        # Convert the pivot table into a long-format DataFrame for Plotly
        heatmap_data_long = heatmap_data.reset_index().melt(
            id_vars='admin2_name',
            var_name='2-Year Block',
            value_name=selected_characteristic
        )

        # Select the appropriate color scale
        if selected_characteristic in ['Drought Severity', 'Drought Intensity']:
            color_scale = 'YlOrRd_r'  # Reverse the scale for Severity and Intensity
        else:
            color_scale = 'YlOrRd'

        # Plot the heatmap using Plotly Express
        fig = px.density_heatmap(
            heatmap_data_long,
            x='2-Year Block',
            y='admin2_name',
            z=selected_characteristic,
            color_continuous_scale=color_scale,
            title=f'Temporal Heatmap of {selected_characteristic} Across Regions (SPI_{selected_spi})',
            labels={'2-Year Block': 'Time (2-Year Block)', 'admin2_name': 'Admin2 Name', selected_characteristic: selected_characteristic}
        )

        # Update layout for better visualization
        fig.update_layout(
            xaxis=dict(
                title='Time (2-Year Block)',
                automargin=True,  # Adjust margins dynamically
            ),
            yaxis=dict(
                title='Admin2 Name'
            ),
            coloraxis_colorbar=dict(title=selected_characteristic),
            margin=dict(t=50, l=50, r=50, b=100),
            height=600,  # Adjusted height for better readability
            dragmode='pan',  # Enable panning for horizontal scrolling
        )

        # Show the plot
        fig.show()

    # Attach the update function to both dropdowns
    characteristic_dropdown.observe(update_plot, names="value")
    spi_dropdown.observe(update_plot, names="value")

    # Display the dropdowns
    display(spi_dropdown, characteristic_dropdown)

    # Trigger the initial plot
    update_plot()
'''    
 
############################################################################################

'''

Plots six different maps: Average drought, severity, and intensity for SPI1 and SPI3

-This function is used for the initial analysis, and than for the clustering analysis, where
cluster boundaries (either k-means or hierarchical) or passed in

'''

############################################################################################


def map_drought_characteristics_by_spi(drought_gdf, cluster_boundaries_df=None):
    """
    Plots geospatial maps for drought characteristics averaged for each admin2 region,
    with consistent color scales across all characteristics. Optionally overlays cluster boundaries.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing the drought and geospatial data.
    - cluster_boundaries_df (GeoDataFrame, optional): GeoDataFrame containing cluster boundaries (e.g., k-means or hierarchical).
      If None, no additional boundaries will be overlaid.
    """
    # Define the characteristics, SPI scales, and their color scale limits
    drought_characteristics = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']
    spi_scales = [1, 3]
    color_scale_limits = {
        'Drought Duration (months)': (0, 7),
        'Drought Severity': (-6, 0),
        'Drought Intensity': (0, 2),  # Same scale, same color as duration
    }

    # Set up the figure
    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(18, 10))
    fig.subplots_adjust(hspace=0.2, wspace=0.3)  # Adjust spacing

    for i, spi_scale in enumerate(spi_scales):
        # Filter for the current SPI scale
        filtered_gdf = drought_gdf[drought_gdf['spi_scale'] == spi_scale].copy()

        # Calculate means for Severity, Duration, and Intensity
        averaged_gdf = (
            filtered_gdf.groupby('admin2_name')[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']]
            .mean()  # Calculate means
            .reset_index()
            .merge(drought_gdf[['admin2_name', 'geometry']].drop_duplicates(), on='admin2_name')
        )

        # Ensure the resulting GeoDataFrame retains geospatial data
        averaged_gdf = gpd.GeoDataFrame(averaged_gdf, geometry='geometry')

        for j, characteristic in enumerate(drought_characteristics):
            ax = axes[i, j]

            # Get manual min and max for the characteristic
            vmin, vmax = color_scale_limits[characteristic]

            # Use the same colormap for Duration and Intensity
            if characteristic in ['Drought Duration (months)', 'Drought Intensity']:
                cmap = 'YlOrRd'  # Consistent colormap
            else:
                cmap = 'YlOrRd_r'  # Reversed colormap for Severity

            # Plot the drought characteristic map
            averaged_gdf.plot(
                column=characteristic,
                cmap=cmap,
                linewidth=0.8,
                ax=ax,
                edgecolor='black',
                legend=True,
                legend_kwds={'shrink': 0.6},
                vmin=vmin,
                vmax=vmax  # Use manual color scale
            )

            # If cluster boundaries are provided, overlay them
            if cluster_boundaries_df is not None:
                cluster_boundaries_df.plot(
                    ax=ax,
                    color='none',  # Transparent fill
                    edgecolor='blue',  # Blue borders for clusters
                    linewidth=1.5,  # Thicker lines for clarity
                )

            # Customize title and axis
            ax.set_title(f"Average {characteristic} (SPI {spi_scale})", fontsize=12)
            ax.axis('off')

    # Display the maps
    plt.suptitle("Geospatial Maps of Average Drought Characteristics by SPI Scale", fontsize=16)
    plt.show()

    
############################################################################################

# Mann-Kendall test functions

############################################################################################


def perform_trend_analysis(spi_series, time_scale):
    """
    Perform Mann-Kendall test and Sen's Slope Estimation for the given SPI series.

    Parameters:
    spi_series (pd.Series): Series of SPI values.
    time_scale (str): Time scale (e.g., '1_month', '3_month').

    Returns:
    dict: Dictionary containing trend, p-value, and Sen's slope.
    """
    spi_series = spi_series.dropna()

    # Perform Mann-Kendall Trend Test
    mk_result = mk.original_test(spi_series)

    return {
        'time_scale': time_scale,
        'trend': mk_result.trend,
        'p_value': mk_result.p,
        'sen_slope': mk_result.slope
    }

def analyze_trends(spi_results_df):
    """
    Perform trend analysis on all SPI series in the DataFrame.

    Parameters:
    spi_results_df (pd.DataFrame): DataFrame with SPI series for multiple regions and time scales.

    Returns:
    pd.DataFrame: DataFrame with trend analysis results for each region and time scale.
    """
    trend_analysis_results = {}

    for column in spi_results_df.columns:
        time_scale = column.split('_')[-1]
        spi_series = spi_results_df[column]
        trend_analysis_results[column] = perform_trend_analysis(spi_series, time_scale)

    return pd.DataFrame(trend_analysis_results).T

def visualize_trends_with_plotly(trend_analysis_df):
    """
    Visualize trends with an interactive Plotly table, color-coded by trend type.

    Parameters:
    trend_analysis_df (pd.DataFrame): DataFrame with trend analysis results, containing
                                      columns ['time_scale', 'trend', 'p_value', 'sen_slope'].
    """
    # Define color mapping for trends
    color_mapping = {
        'increasing': 'rgba(102, 194, 165, 0.8)',  # Green for increasing trends
        'decreasing': 'rgba(252, 141, 98, 0.8)',  # Red for decreasing trends
        'no trend': 'rgba(211, 211, 211, 0.8)'    # Grey for no trend
    }

    # Add a color column based on the trend
    trend_analysis_df['color'] = trend_analysis_df['trend'].map(color_mapping)

    # Ensure numeric columns are correctly formatted
    trend_analysis_df['p_value'] = pd.to_numeric(trend_analysis_df['p_value'], errors='coerce')
    trend_analysis_df['sen_slope'] = pd.to_numeric(trend_analysis_df['sen_slope'], errors='coerce')

    # Replace NaN values with placeholder text
    trend_analysis_df['p_value'] = trend_analysis_df['p_value'].fillna("N/A")
    trend_analysis_df['sen_slope'] = trend_analysis_df['sen_slope'].fillna("N/A")

    # If numeric, round the values
    trend_analysis_df['p_value'] = trend_analysis_df['p_value'].apply(lambda x: round(x, 3) if isinstance(x, (int, float)) else x)
    trend_analysis_df['sen_slope'] = trend_analysis_df['sen_slope'].apply(lambda x: round(x, 3) if isinstance(x, (int, float)) else x)

    # Format the index to display as "Admin Zone (Time Scale)"
    trend_analysis_df = trend_analysis_df.reset_index()
    trend_analysis_df['index'] = trend_analysis_df['index'].apply(
        lambda x: f"{x.split('_')[0]} ({x.split('_')[1].replace('month', 'month')})"
    )

    # Create the table using Plotly
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Admin Zone-Time Scale", "Trend", "p-value", "Sen's Slope"],
                align='left',
                font=dict(size=14, color='white'),
                fill_color='black'
            ),
            cells=dict(
                values=[
                    trend_analysis_df['index'],  # Admin Zone-Time Scale (formatted index)
                    trend_analysis_df['trend'],  # Trend
                    trend_analysis_df['p_value'],  # p-value
                    trend_analysis_df['sen_slope']  # Sen's Slope
                ],
                align='left',
                fill_color=[
                    trend_analysis_df['color'],  # Row colors based on trend
                    trend_analysis_df['color'],  # Row colors based on trend
                    trend_analysis_df['color'],  # Row colors based on trend
                    trend_analysis_df['color']   # Row colors based on trend
                ],
                font=dict(size=12)
            )
        )
    ])

    # Update layout
    fig.update_layout(
        title="Trend Analysis Results",
        title_x=0.5,
        margin=dict(l=20, r=20, t=60, b=20),
        height=600
    )

    # Show the interactive table
    fig.show()



############################################################################################

'''

Drought Percentage Heat Maps by Cluster 

-Shows heatmeaps for each cluster (k-means or hiearchical) and the percentage of admin2 zones
that are experiencing a drought in a particular month

'''

############################################################################################




def create_hover_heatmap_with_custom_colors(df, title="Interactive Heatmap", ylabel="Hierarchical Cluster", index_col="hierarchical_cluster"):
    """
    Create an interactive heatmap with styled hover tooltips and a custom color scheme.
    
    Parameters:
    - df (pd.DataFrame): The DataFrame containing clustering information and drought percentages.
    - title (str): Title of the heatmap.
    - ylabel (str): Label for the y-axis.
    - index_col (str): The column name to set as the index.
    
    Returns:
    - HTML (str): The HTML string of the heatmap.
    """
    # Drop unnecessary columns like 'total_regions'
    if 'total_regions' in df.columns:
        df = df.drop(columns=['total_regions'])

    # Ensure the specified column is the index
    if index_col not in df.columns:
        raise KeyError(f"Column '{index_col}' not found in the DataFrame.")

    df = df.set_index(index_col)

    # Create the heatmap with a custom color map
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        df, 
        ax=ax, 
        cmap="OrRd",  # Light orange to red color scheme
        cbar_kws={'label': '% of Regions in Drought'}
    )

    # Generate hover labels with styling
    labels = []
    for y in range(df.shape[0]):
        for x in range(df.shape[1]):
            value = df.iloc[y, x]
            label = f"""
            <div style="background-color: white; border: 1px solid black; padding: 5px; border-radius: 5px;">
                <strong>Cluster:</strong> {df.index[y]}<br>
                <strong>Year-Month:</strong> {df.columns[x]}<br>
                <strong>Drought %:</strong> {value:.2f}
            </div>
            """
            labels.append(label)

    # Attach the tooltips to the heatmap
    tooltip = plugins.PointHTMLTooltip(ax.collections[0], labels, voffset=10, hoffset=10)
    plugins.connect(fig, tooltip)

    # Add titles and labels
    plt.title(title, fontsize=16)
    plt.xlabel("Year-Month", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)

    # Return the HTML string
    return mpld3.fig_to_html(fig)





'''

# TODO: move these to top of script
from ipyleaflet import Map, GeoJSON, LayersControl
from ipywidgets import IntSlider, VBox, Label
import json

def create_time_slider_map_with_boundaries(spi_gdf, cluster_boundaries, title="Time Slider Map"):
    """
    Create a time slider map using ipyleaflet with added cluster boundaries.

    Parameters:
    - spi_gdf (GeoDataFrame): Input GeoDataFrame (e.g., zambia_spi_1_df or zambia_spi_3_df) with 'year_month' and 'indicator' columns.
    - cluster_boundaries (GeoDataFrame): GeoDataFrame containing the cluster boundaries (e.g., hierarchical or regular clusters).
    - title (str): Title for the map display.

    Returns:
    - VBox: A widget containing the map, slider, and title label.
    """
    # Step 1: Reproject GeoDataFrames to WGS84 (EPSG:4326)
    spi_gdf = spi_gdf.to_crs(epsg=4326)
    cluster_boundaries = cluster_boundaries.to_crs(epsg=4326)

    # Ensure 'year_month' is converted to a string
    spi_gdf['year_month'] = spi_gdf['year_month'].astype(str)

    # Step 2: Prepare GeoJSON layers for each time step
    geojson_dict = {}
    all_dates = spi_gdf['year_month'].unique()

    for date in all_dates:
        # Filter data for the specific date
        gdf_date = spi_gdf[spi_gdf['year_month'] == date]
        
        # Convert to GeoJSON and add a custom style for each feature
        geojson_data = json.loads(gdf_date.to_json())
        for feature in geojson_data["features"]:
            feature["properties"]["style"] = {
                "color": "black",
                "fillColor": "red" if feature["properties"]["indicator"] == 1 else "green",
                "fillOpacity": 0.7,
                "weight": 1,
            }
        geojson_dict[date] = geojson_data

    # Step 3: Create the ipyleaflet map
    m = Map(center=(-15, 30), zoom=6)

    # Step 4: Add GeoJSON layers for SPI data
    geojson_layers = {}
    for date, geojson_data in geojson_dict.items():
        geojson_layer = GeoJSON(data=geojson_data)
        geojson_layers[date] = geojson_layer

    # Step 5: Add cluster boundaries layer
    cluster_geojson = json.loads(cluster_boundaries.to_json())
    for feature in cluster_geojson["features"]:
        feature["properties"]["style"] = {
            "color": "blue",  # Boundary color
            "weight": 3,      # Thicker border
            "fillOpacity": 0, # Transparent fill
        }
    cluster_boundaries_layer = GeoJSON(data=cluster_geojson)

    m.add_layer(cluster_boundaries_layer)  # Add the boundaries layer to the map

    # Step 6: Add a slider to toggle layers
    slider = IntSlider(
        value=0,
        min=0,
        max=len(all_dates) - 1,
        step=1,
        description="Time",
        continuous_update=False
    )

    label = Label(value=f"{title}: Showing {all_dates[0]}")

    def update_map(change):
        # Clear existing layers
        for layer in geojson_layers.values():
            if layer in m.layers:
                m.remove_layer(layer)
        
        # Add the selected layer
        selected_date = all_dates[slider.value]
        m.add_layer(geojson_layers[selected_date])
        label.value = f"{title}: Showing {selected_date}"

    slider.observe(update_map, names="value")

    # Step 7: Display the map with slider
    update_map(None)  # Initialize with the first layer
    return VBox([m, slider, label])


''' 
    
