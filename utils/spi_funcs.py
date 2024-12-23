import pandas as pd
from scipy.stats import gamma, norm
import matplotlib.pyplot as plt
from ipywidgets import interact, Dropdown, VBox, HTML
import plotly.express as px
import plotly.graph_objects as go


def calculate_spi(precip_series, scale=1):
    """Calculate Standardized Precipitation Index (SPI) for a given precipitation series."""
    precip_rolling = precip_series.rolling(window=scale).sum()
    precip_rolling = precip_rolling.dropna()
    shape, loc, scale_param = gamma.fit(precip_rolling, floc=0)
    gamma_cdf = gamma.cdf(precip_rolling, shape, loc=loc, scale=scale_param)
    spi_values = norm.ppf(gamma_cdf)
    return pd.Series(spi_values, index=precip_rolling.index)


def calculate_spi_for_regions(zambia_rain_df):
    """Calculate 1-month and 3-month SPI for all regions in the dataset."""
    spi_results_df = pd.DataFrame()
    admin2_names = zambia_rain_df['admin2_name'].unique()
    for admin2 in admin2_names:
        admin2_cleaned = admin2.replace(" ", "_").replace("-", "_")
        region_data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2][['date', 'precipitation']]
        region_data.set_index('date', inplace=True)
        region_data = region_data.groupby(region_data.index).mean()
        spi_1_month = calculate_spi(region_data['precipitation'], scale=1)
        spi_1_month.name = f'{admin2_cleaned}_1_month'
        spi_3_month = calculate_spi(region_data['precipitation'], scale=3)
        spi_3_month.name = f'{admin2_cleaned}_3_month'
        region_spi_df = pd.concat([spi_1_month, spi_3_month], axis=1)
        spi_results_df = pd.concat([spi_results_df, region_spi_df], axis=1)
    return spi_results_df


def plot_spi_plotly_with_labels(region_time_scale, spi_results_df):
    """
    Interactive plot for the Standardized Precipitation Index (SPI) using Plotly,
    with updated labels for drought categories displayed below the plot.

    Parameters:
    region_time_scale (str): The selected region and time scale from spi_results_df.
    spi_results_df (pd.DataFrame): DataFrame containing SPI results.
    """
    # Extract the SPI series based on the selected region and time scale
    spi_series = spi_results_df[region_time_scale].dropna()
    spi_data = spi_series.reset_index()  # Reset index for Plotly

    # Rename the columns for clarity
    spi_data.columns = ["date", "spi"]

    # Create the main SPI line plot
    fig = px.line(
        spi_data,
        x="date",
        y="spi",
        title=f"Standardized Precipitation Index (SPI) for {region_time_scale}",
        labels={"date": "Date", "spi": "SPI Value"}
    )

    # Add reference lines for drought categories
    fig.add_hline(y=0, line_dash="dash", line_color="black")  # Neutral
    fig.add_hline(y=-1, line_dash="dash", line_color="orange")  # Mild Drought
    fig.add_hline(y=-1.5, line_dash="dash", line_color="red")  # Moderate Drought
    fig.add_hline(y=-2, line_dash="dash", line_color="darkred")  # Severe Drought

    # Update the layout for interactivity and spacing
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="SPI Value",
        xaxis_tickangle=45,
        legend_title="Legend",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,  # Move legend closer to the plot
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified"
    )

    # Show the plot
    return fig


def setup_interactive_plot_with_labels(spi_results_df):
    """
    Sets up the interactive SPI plot with updated labels for drought categories.

    Parameters:
    spi_results_df (pd.DataFrame): DataFrame containing SPI results.
    """
    interact(
        lambda region_time_scale: VBox([
            go.FigureWidget(plot_spi_plotly_with_labels(region_time_scale, spi_results_df)),
            HTML("""
            <div style="margin-top: 10px; font-size: 14px; line-height: 1.5;">
                <strong>SPI Categories:</strong><br>
                <span style="color: black;">Neutral (SPI=0)</span><br>
                <span style="color: orange;">Mild Drought (SPI=-1)</span><br>
                <span style="color: red;">Moderate Drought (SPI=-1.5)</span><br>
                <span style="color: darkred;">Severe Drought (SPI=-2)</span>
            </div>
            """)
        ]),
        region_time_scale=Dropdown(
            options=spi_results_df.columns.tolist(),
            description='Select Region & Scale:',
            style={'description_width': 'initial'},
        )
    )



