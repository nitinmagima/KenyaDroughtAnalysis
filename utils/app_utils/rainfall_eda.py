import geopandas as gpd
import pandas as pd
import folium
from scipy.stats import gamma, kstest, probplot
import plotly.graph_objects as go


def load_data(rain_data_path, boundaries_path):
    """
    Load precipitation data and administrative boundaries, then merge them into a GeoDataFrame.

    Parameters:
    rain_data_path (str): Path to the rainfall data CSV file.
    boundaries_path (str): Path to the GeoJSON file containing admin boundaries.

    Returns:
    gpd.GeoDataFrame: A GeoDataFrame containing the merged rainfall and boundary data.
    """
    # Load rainfall data and boundaries
    zambia_rain_df = pd.read_csv(rain_data_path)
    admin_boundaries = gpd.read_file(boundaries_path)

    # Rename columns to ensure matching keys
    admin_boundaries.rename(columns={"ADM2_NAME": "admin2_name"}, inplace=True)

    # Merge data into a GeoDataFrame
    zambia_rain_df = gpd.GeoDataFrame(zambia_rain_df.merge(admin_boundaries, on="admin2_name"))

    return zambia_rain_df


def interactive_precip_histogram(dataframe, group_column, value_column):
    unique_groups = sorted(dataframe[group_column].unique())
    fig = go.Figure()

    for i, group in enumerate(unique_groups):
        group_data = dataframe[dataframe[group_column] == group]
        fig.add_trace(
            go.Histogram(
                x=group_data[value_column],
                name=group,
                visible=(i == 0),
                marker=dict(color="rgba(135, 206, 250, 0.6)", line=dict(color="black", width=1.5)),
                hovertemplate=f"Range: %{{x}} mm<br>Count: %{{y}}<extra></extra>"
            )
        )

    buttons = []
    for i, group in enumerate(unique_groups):
        buttons.append(
            dict(
                label=group,
                method="update",
                args=[
                    {"visible": [j == i for j in range(len(unique_groups))]},
                    {"title": f"{group} Rain Season"}
                ]
            )
        )

    fig.update_layout(
        updatemenus=[dict(active=0, buttons=buttons)],
        title=f"Precipitation Histogram ({unique_groups[0]})",
        xaxis=dict(title="Precipitation (mm)", gridcolor="lightgrey"),
        yaxis=dict(title="Frequency", gridcolor="lightgrey"),
        barmode="overlay",
        plot_bgcolor="white"
    )
    return fig


def perform_ks_test_table_with_pvalues(zambia_rain_df):
    passing_admin2_names = []
    failing_admin2_names = []

    for admin2_name in zambia_rain_df['admin2_name'].unique():
        data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]['precipitation'].dropna()
        if len(data) < 2:
            continue
        shape, loc, scale = gamma.fit(data, floc=0)
        _, p_value = kstest(data, gamma(shape, loc, scale).cdf)
        formatted_name = f"{admin2_name} (p={p_value:.4f})"
        if p_value > 0.05:
            passing_admin2_names.append(formatted_name)
        else:
            failing_admin2_names.append(formatted_name)

    fig = go.Figure()
    fig.add_trace(
        go.Table(
            header=dict(values=["Passing Admin2 Areas"], align="left", font=dict(size=12, color="white"), fill_color="green"),
            cells=dict(values=[passing_admin2_names], align="left", font=dict(size=10), fill_color="lightgreen"),
            visible=True
        )
    )
    fig.add_trace(
        go.Table(
            header=dict(values=["Failing Admin2 Areas"], align="left", font=dict(size=12, color="white"), fill_color="red"),
            cells=dict(values=[failing_admin2_names], align="left", font=dict(size=10), fill_color="lightpink"),
            visible=False
        )
    )
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(label="Passing Areas", method="update", args=[{"visible": [True, False]}, {"title": "Passing"}]),
                    dict(label="Failing Areas", method="update", args=[{"visible": [False, True]}, {"title": "Failing"}])
                ],
                direction="down",
                showactive=True
            )
        ],
        title="Kolmogorov-Smirnov Test Results",
    )
    return {"passing": len(passing_admin2_names), "failing": len(failing_admin2_names)}, fig


def map_ks_test_results(results_gdf):
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6)
    for _, row in results_gdf.iterrows():
        color = "green" if row["status"] == "Passed" else "red"
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


def create_interactive_qq_plot(zambia_rain_df):
    """
    Create an interactive Plotly QQ plot with a dropdown menu for switching regions.

    Parameters:
    zambia_rain_df (pd.DataFrame): The DataFrame containing the data.

    Returns:
    Plotly Figure object: The QQ plot with dropdown interactivity.
    """
    # Extract unique combinations of region and admin2_name
    region_admin2_combinations = zambia_rain_df.groupby(["region", "admin2_name"]).size().index.tolist()

    # Initialize the Plotly figure
    fig = go.Figure()

    # Generate QQ plots for each region-admin2_name combination
    for region, admin2_name in region_admin2_combinations:
        # Filter data for the selected combination
        filtered_df = zambia_rain_df[
            (zambia_rain_df["region"] == region) &
            (zambia_rain_df["admin2_name"] == admin2_name)
        ]
        data = filtered_df["precipitation"].dropna()

        if data.empty:
            continue

        # Fit the gamma distribution to the data
        shape, loc, scale = gamma.fit(data, floc=0)

        # Generate QQ plot points
        theoretical_quantiles, ordered_values = probplot(
            data, dist="gamma", sparams=(shape, loc, scale)
        )[0]

        # Add a scatter trace for QQ points
        fig.add_trace(
            go.Scatter(
                x=theoretical_quantiles,
                y=ordered_values,
                mode="markers",
                name=f"{region} - {admin2_name}",
                visible=False,  # Initially hidden
                marker=dict(color="blue"),
                hovertemplate="Theoretical: %{x}<br>Ordered: %{y}<extra></extra>"
            )
        )

        # Add a line trace for the ideal fit
        fig.add_trace(
            go.Scatter(
                x=theoretical_quantiles,
                y=theoretical_quantiles,
                mode="lines",
                name=f"Ideal Fit ({region} - {admin2_name})",
                visible=False,  # Initially hidden
                line=dict(color="red", dash="dash"),
            )
        )

    # Create dropdown buttons to toggle visibility of each combination
    dropdown_buttons = []
    for i, (region, admin2_name) in enumerate(region_admin2_combinations):
        dropdown_buttons.append(
            dict(
                label=f"{region} - {admin2_name}",
                method="update",
                args=[
                    {"visible": [j // 2 == i for j in range(len(region_admin2_combinations) * 2)]},
                    {"title": f"QQ Plot to Check Gamma Fit: {admin2_name} ({region})"}
                ]
            )
        )

    # Update layout with dropdown and styling
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=dropdown_buttons,
                direction="down",
                showactive=True,
                x=0.5,
                xanchor="center",
                y=1.15,
                yanchor="top",
            )
        ],
        title="QQ Plot to Check Gamma Fit",
        xaxis=dict(title="Theoretical Quantiles"),
        yaxis=dict(title="Ordered Values"),
        template="plotly_white",
        height=600,
        width=800,
    )

    # Make the first trace visible by default
    if len(fig.data) > 0:
        for j in range(2):
            fig.data[j].visible = True

    return fig







