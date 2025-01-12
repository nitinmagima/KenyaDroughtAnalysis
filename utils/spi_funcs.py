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


def plot_spi_fixed_layout(spi_results_df):
    """
    Plot the Standardized Precipitation Index (SPI) using plotly.express,
    with a dropdown menu to switch between regions and time scales.
    Properly fixes layout issues with clear spacing and alignment.

    Parameters:
    spi_results_df (pd.DataFrame): DataFrame containing SPI results.
    """
    # Prepare the dropdown options
    dropdown_options = []
    for region_time_scale in spi_results_df.columns:
        spi_series = spi_results_df[region_time_scale].dropna()
        spi_data = spi_series.reset_index()
        spi_data.columns = ["date", "spi"]
        
        # Create a trace for each region/time scale
        dropdown_options.append(
            go.Scatter(
                x=spi_data["date"],
                y=spi_data["spi"],
                name=region_time_scale,
                mode="lines"
            )
        )
    
    # Create the initial figure with the first region/time scale
    fig = go.Figure(data=[dropdown_options[0]])

    # Add reference lines for drought categories
    fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Neutral (SPI=0)", annotation_position="top left")
    fig.add_hline(y=-1, line_dash="dash", line_color="orange", annotation_text="Mild Drought (SPI=-1)", annotation_position="top left")
    fig.add_hline(y=-1.5, line_dash="dash", line_color="red", annotation_text="Moderate Drought (SPI=-1.5)", annotation_position="top left")
    fig.add_hline(y=-2, line_dash="dash", line_color="darkred", annotation_text="Severe Drought (SPI=-2)", annotation_position="top left")

    # Add a dropdown menu for switching between regions/time scales
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "method": "update",
                        "label": region_time_scale,
                        "args": [{"y": [spi_results_df[region_time_scale].dropna().values]}]
                    }
                    for region_time_scale in spi_results_df.columns
                ],
                "direction": "down",
                "x": 0.21,  # Center the dropdown
                "y": 1.2,  # Place dropdown below the title
                "showactive": True
            }
        ],
        title=dict(
            text="Standardized Precipitation Index (SPI)",
            x=0.5,  # Center the title
            y=0.9  # Adjust title position for spacing
        ),
        xaxis_title="Date",
        yaxis_title="SPI Value",
        hovermode="x unified",
        margin=dict(t=120, b=180),  # Adjust spacing for dropdown and labels
        annotations=[
            dict(
                text=(
                    "<b>SPI Categories:</b><br>"
                    "<span style='color:black;'>Neutral (SPI=0)</span><br>"
                    "<span style='color:orange;'>Mild Drought (SPI=-1)</span><br>"
                    "<span style='color:red;'>Moderate Drought (SPI=-1.5)</span><br>"
                    "<span style='color:darkred;'>Severe Drought (SPI=-2)</span>"
                ),
                xref="paper",
                yref="paper",
                x=0,
                y=-0.6,  # Position labels clearly below the plot
                showarrow=False,
                font=dict(size=12),
                align="center"
            )
        ]
    )

    # Show the plot
    fig.show()


def plot_spi_plotly_with_dropdown_and_labels(spi_results_df):
    """
    Plot the Standardized Precipitation Index (SPI) using plotly.express,
    with a dropdown menu to switch between regions and time scales.
    Includes drought category labels displayed below the plot.

    Parameters:
    spi_results_df (pd.DataFrame): DataFrame containing SPI results.
    """
    # Prepare the dropdown options
    dropdown_options = []
    for region_time_scale in spi_results_df.columns:
        spi_series = spi_results_df[region_time_scale].dropna()
        spi_data = spi_series.reset_index()
        spi_data.columns = ["date", "spi"]
        
        # Create a trace for each region/time scale
        dropdown_options.append(
            go.Scatter(
                x=spi_data["date"],
                y=spi_data["spi"],
                name=region_time_scale,
                mode="lines"
            )
        )
    
    # Create the initial figure with the first region/time scale
    fig = go.Figure(data=[dropdown_options[0]])

    # Add reference lines for drought categories
    fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Neutral (SPI=0)")
    fig.add_hline(y=-1, line_dash="dash", line_color="orange", annotation_text="Mild Drought (SPI=-1)")
    fig.add_hline(y=-1.5, line_dash="dash", line_color="red", annotation_text="Moderate Drought (SPI=-1.5)")
    fig.add_hline(y=-2, line_dash="dash", line_color="darkred", annotation_text="Severe Drought (SPI=-2)")

    # Add a dropdown menu for switching between regions/time scales
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "method": "update",
                        "label": region_time_scale,
                        "args": [{"y": [spi_results_df[region_time_scale].dropna().values]}]
                    }
                    for region_time_scale in spi_results_df.columns
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.1,
                "y": 1.15
            }
        ],
        title="Standardized Precipitation Index (SPI)",
        xaxis_title="Date",
        yaxis_title="SPI Value",
        hovermode="x unified",
        margin=dict(t=50, b=150),  # Add space for the labels
        annotations=[
            dict(
                text="<b>SPI Categories:</b><br>"
                     "<span style='color:black;'>Neutral (SPI=0)</span><br>"
                     "<span style='color:orange;'>Mild Drought (SPI=-1)</span><br>"
                     "<span style='color:red;'>Moderate Drought (SPI=-1.5)</span><br>"
                     "<span style='color:darkred;'>Severe Drought (SPI=-2)</span>",
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.4,
                showarrow=False,
                font=dict(size=12),
                align="center"
            )
        ]
    )

    # Show the plot
    fig.show()

