import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gamma, probplot, kstest
import ipywidgets as widgets
from ipywidgets import Dropdown, interact
import plotly.graph_objects as go
import geopandas as gpd
from IPython.display import display, clear_output
import folium


def interactive_precip_histogram(dataframe, group_column, value_column):
    """
    Create an interactive Plotly dropdown histogram for precipitation data grouped by a specific column.

    Parameters:
    dataframe (pd.DataFrame): The DataFrame containing the data.
    group_column (str): The column name to group by (e.g., 'admin2_name' or 'admin1_name').
    value_column (str): The column containing precipitation values.

    Returns:
    None: Displays the Plotly figure with a dropdown menu.
    """

    # Get unique groups from the specified group column
    unique_groups = dataframe[group_column].unique()

    # Initialize the figure
    fig = go.Figure()

    # Step 1: Add a histogram for each group
    for i, group in enumerate(unique_groups):
        group_data = dataframe[dataframe[group_column] == group]
        fig.add_trace(
            go.Histogram(
                x=group_data[value_column],
                name=group,
                visible=(i == 0),  # Only the first trace is visible by default
                marker=dict(
                    color="rgba(135, 206, 250, 0.6)",  # Light blue fill
                    line=dict(color="black", width=1.5)  # Black edge
                ),
                hovertemplate=f"Range: %{{x}} mm<br>Count: %{{y}}<extra></extra>"
            )
        )

    # Step 2: Create dropdown buttons
    buttons = []
    for i, group in enumerate(unique_groups):
        buttons.append(
            dict(
                label=group,
                method="update",
                args=[
                    {"visible": [j == i for j in range(len(unique_groups))]},  # Update visibility
                    {"title": f"{group} Rain Season"}  # Update title
                ]
            )
        )

    # Step 3: Configure layout and dropdown menu
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,  # Default to the first group
                buttons=buttons
            )
        ],
        title=f"Precipitation Histogram ({unique_groups[0]})",
        xaxis=dict(title="Precipitation (mm)", gridcolor="lightgrey"),
        yaxis=dict(title="Frequency", gridcolor="lightgrey"),
        barmode="overlay",
        plot_bgcolor="white"  # White background
    )

    # Display the plot
    fig.show()


def perform_ks_test(zambia_rain_df):
    """
    Perform Kolmogorov-Smirnov test for each admin2_name in the dataset.

    Parameters:
    zambia_rain_df (GeoDataFrame): The GeoDataFrame containing precipitation data and geometries.

    Returns:
    GeoDataFrame: A GeoDataFrame with columns ['admin2_name', 'p_value', 'status', 'geometry'].
    """
    results = []

    # Loop through each admin2_name
    for admin2_name in zambia_rain_df['admin2_name'].unique():
        # Get the precipitation data for the current admin2_name
        data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]['precipitation'].dropna()

        # Skip if there's not enough data
        if len(data) < 2:
            continue

        # Fit a gamma distribution to the data
        shape, loc, scale = gamma.fit(data, floc=0)  # floc=0 ensures non-negative values

        # Perform Kolmogorov-Smirnov test
        _, p_value = kstest(data, gamma(shape, loc, scale).cdf)

        # Categorize the result based on p-value
        status = "Passed" if p_value > 0.05 else "Failed"

        # Get the geometry for this region
        geometry = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name].iloc[0]['geometry']

        # Append to results
        results.append({
            "admin2_name": admin2_name,
            "p_value": p_value,
            "status": status,
            "geometry": geometry
        })

    # Convert results to a GeoDataFrame
    results_gdf = gpd.GeoDataFrame(results, geometry="geometry")
    return results_gdf

    
def generate_interactive_table(results_df):
    """
    Generate an interactive Plotly table for passing and failing areas.
    
    Parameters:
    results_df (GeoDataFrame): GeoDataFrame with KS test results containing columns ['admin2_name', 'p_value', 'status'].

    Returns:
    None: Displays an interactive Plotly table.
    """
    # Split into passing and failing areas
    passing_admin2_names = results_df[results_df['status'] == "Passed"]\
        .apply(lambda x: f"{x['admin2_name']} (p={x['p_value']:.4f})", axis=1).tolist()
    failing_admin2_names = results_df[results_df['status'] == "Failed"]\
        .apply(lambda x: f"{x['admin2_name']} (p={x['p_value']:.4f})", axis=1).tolist()

    # Create a Plotly table
    fig = go.Figure()

    # Add passing areas as the first table
    fig.add_trace(
        go.Table(
            header=dict(values=["Passing Admin2 Areas"], align="left", font=dict(size=12, color="white"), fill_color="green"),
            cells=dict(values=[passing_admin2_names], align="left", font=dict(size=10), fill_color="lightgreen"),
            visible=True  # Default visible
        )
    )

    # Add failing areas as the second table
    fig.add_trace(
        go.Table(
            header=dict(values=["Failing Admin2 Areas"], align="left", font=dict(size=12, color="white"), fill_color="red"),
            cells=dict(values=[failing_admin2_names], align="left", font=dict(size=10), fill_color="lightpink"),
            visible=False  # Initially hidden
        )
    )

    # Add dropdown menu to toggle between passing and failing areas
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(
                        label="Passing Areas",
                        method="update",
                        args=[{"visible": [True, False]},  # Show passing, hide failing
                              {"title": "Admin2 Areas Passing the KS Test"}]
                    ),
                    dict(
                        label="Failing Areas",
                        method="update",
                        args=[{"visible": [False, True]},  # Show failing, hide passing
                              {"title": "Admin2 Areas Failing the KS Test"}]
                    )
                ],
                direction="down",
                showactive=True
            )
        ],
        title="Admin2 KS Test Results",
    )

    # Show the figure
    fig.show()

    
def map_ks_test_results(results_gdf):
    """
    Create an interactive map to visualize the KS test results.
    
    Parameters:
    results_gdf (GeoDataFrame): GeoDataFrame containing columns ['admin2_name', 'p_value', 'status', 'geometry'].

    Returns:
    folium.Map: Interactive map with regions colored by test result and hover information.
    """
    # Initialize a folium map centered on Zambia
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6)

    # Add polygons for each region
    for _, row in results_gdf.iterrows():
        # Determine the color based on status
        color = "green" if row["status"] == "Passed" else "red"

        # Add the region polygon to the map
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(f"Name: {row['admin2_name']}<br>P-value: {row['p_value']:.4f}"),
        ).add_to(m)

    return m
    

def create_dynamic_qq_plot(zambia_rain_df):
    """
    Create an interactive Matplotlib QQ plot with a dropdown menu for dynamic updates.

    Parameters:
    zambia_rain_df (pd.DataFrame): The DataFrame containing the data.

    Returns:
    None: Displays the interactive dropdown and plot in a Jupyter Notebook.
    """
    # Extract unique combinations of region and admin2_name
    region_admin2_combinations = zambia_rain_df.groupby(["region", "admin2_name"]).size().index.tolist()

    # Dropdown widget for region-admin2_name selection
    dropdown = widgets.Dropdown(
        options=[f"{region} - {admin2_name}" for region, admin2_name in region_admin2_combinations],
        description="Select Region:",
        style={'description_width': 'initial'}
    )

    # Function to update the plot
    def update_plot(change):
        clear_output(wait=True)  # Clear the current cell output

        # Display the dropdown again after clearing output
        display(dropdown)

        # Parse the selected region and admin2_name
        selected_combination = change["new"]
        region, admin2_name = selected_combination.split(" - ")

        # Filter data for the selected combination
        filtered_df = zambia_rain_df[
            (zambia_rain_df["region"] == region) &
            (zambia_rain_df["admin2_name"] == admin2_name)
        ]

        if filtered_df.empty:
            print("No data available for the selected combination.")
            return

        # Get precipitation data and fit the gamma distribution
        data = filtered_df["precipitation"].dropna()
        shape, loc, scale = gamma.fit(data, floc=0)

        # Generate QQ plot points
        (theoretical_quantiles, ordered_values), _ = probplot(
            data, dist="gamma", sparams=(shape, loc, scale)
        )

        # Create the Matplotlib QQ plot
        plt.figure(figsize=(8, 6))
        plt.scatter(theoretical_quantiles, ordered_values, color="blue", label="QQ Points")
        plt.plot(theoretical_quantiles, theoretical_quantiles, "r--", label="Ideal Fit")
        plt.title(f"QQ Plot to Check Gamma Fit: {admin2_name} ({region})")
        plt.xlabel("Theoretical Quantiles")
        plt.ylabel("Ordered Values")
        plt.legend()
        plt.grid(True)
        plt.show()

    # Attach the update function to the dropdown
    dropdown.observe(update_plot, names="value")

    # Display the dropdown initially
    display(dropdown)

    # Trigger the initial plot
    dropdown.value = dropdown.options[0]  # Ensure the first plot is displayed

    
    
    
    