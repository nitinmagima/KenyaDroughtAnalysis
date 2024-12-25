import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ipywidgets import interact, Dropdown, fixed


# Function to characterize drought events
def characterize_drought_events(spi_results_df, spi_threshold=-1.0):
    """
    Characterize drought events based on SPI values for each region (admin2_name) and time scale.

    Parameters:
    spi_results_df (pd.DataFrame): Input DataFrame with SPI values for different regions and time scales.
    spi_threshold (float): Threshold for defining a drought event (default is -1.0 for moderate drought).

    Returns:
    pd.DataFrame: Output DataFrame containing drought event details for each region and time scale.
    """
    drought_events = []

    for column in spi_results_df.columns:
        admin2_name, time_scale = column.rsplit('_', 1)
        spi_series = spi_results_df[column].dropna()

        spi_scale = int(admin2_name.split('_')[-1])
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
                    duration = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days // 30
                    intensity = severity / duration if duration > 0 else 0
                    drought_events.append({
                        'admin2_name': admin2_name,
                        'time_scale': time_scale,
                        'spi_scale': spi_scale,
                        'Drought Event': drought_event_count,
                        'Drought Duration (months)': duration,
                        'Drought Severity': severity,
                        'Drought Intensity': intensity,
                        'Drought Start': start_date,
                        'Drought End': end_date
                    })

        if in_drought:
            end_date = spi_series.index[-1]
            duration = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days // 30
            intensity = severity / duration if duration > 0 else 0
            drought_events.append({
                'admin2_name': admin2_name,
                'time_scale': time_scale,
                'spi_scale': spi_scale,
                'Drought Event': drought_event_count,
                'Drought Duration (months)': duration,
                'Drought Severity': severity,
                'Drought Intensity': intensity,
                'Drought Start': start_date,
                'Drought End': end_date
            })

    return pd.DataFrame(drought_events)


# Function to plot interactive histograms
def plot_interactive_histogram(admin2_name, variable, df):
    """
    Plots an interactive histogram or density plot for a selected drought characteristic.

    Parameters:
    - admin2_name (str): Selected admin2_name (administrative unit).
    - variable (str): The drought characteristic to plot (e.g., 'Drought Duration (months)', 'Drought Severity', 'Drought Intensity').
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    """
    # Filter data based on user selections
    filtered_df = df[df['admin2_name'] == admin2_name]

    # Check if filtered data is not empty
    if filtered_df.empty:
        print("No data available for the selected filters.")
        return

    # Plot the histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(filtered_df[variable], bins=20, kde=True, color='skyblue', edgecolor='black')
    plt.title(f"Distribution of {variable} for {admin2_name}")
    plt.xlabel(variable)
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Function to setup interactive histogram visualization
def setup_interactive_histogram(drought_events_df):
    """
    Sets up the interactive dropdown widgets for histogram plotting.

    Parameters:
    - drought_events_df (pd.DataFrame): The DataFrame containing drought events and their characteristics.
    """
    # Dropdown options
    admin2_name_options = drought_events_df['admin2_name'].unique().tolist()
    variable_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']

    # Create dropdown widgets
    admin2_name_dropdown = Dropdown(
        options=admin2_name_options, 
        description='Admin2 Name:', 
        style={'description_width': 'initial'}
    )
    variable_dropdown = Dropdown(
        options=variable_options, 
        description='Variable:', 
        style={'description_width': 'initial'}
    )

    # Create interactive dropdown widgets for selecting admin2_name and variable
    interact(
        plot_interactive_histogram,
        admin2_name=admin2_name_dropdown,
        variable=variable_dropdown,
        df=fixed(drought_events_df)  # Pass the DataFrame as a fixed value
    )


    
import plotly.express as px
from ipywidgets import interact, Dropdown, Checkbox, fixed

def plot_drought_event_frequency_plotly(df, dimension, sort_by_height):
    """
    Interactive bar chart for drought event frequency using Plotly.

    Parameters:
    - df (pd.DataFrame): DataFrame containing drought characteristics data.
    - dimension (str): The dimension to group by ('admin2_name', 'spi_scale').
    - sort_by_height (bool): Whether to sort the bars based on frequency.
    """
    # Check if the selected dimension is in the DataFrame
    if dimension not in df.columns:
        print(f"Dimension '{dimension}' is not available in the DataFrame.")
        return

    # Group by the selected dimension to calculate the frequency of drought events
    drought_freq = df.groupby(dimension)['Drought Event'].nunique().reset_index()
    drought_freq = drought_freq.rename(columns={'Drought Event': 'Drought Event Frequency'})

    # Sort values if specified
    if sort_by_height:
        drought_freq = drought_freq.sort_values(by='Drought Event Frequency', ascending=False)

    # Create the bar chart with Plotly
    fig = px.bar(
        drought_freq,
        x=dimension,
        y='Drought Event Frequency',
        title=f'Frequency of Drought Events by {dimension.capitalize()}',
        labels={dimension: dimension.capitalize(), 'Drought Event Frequency': 'Frequency'},
        color='Drought Event Frequency',  # Use color to enhance the visual
        color_continuous_scale='Blues',
    )

    # Update layout for better spacing and appearance
    fig.update_layout(
        xaxis_tickangle=45,
        xaxis_title=dimension.capitalize(),
        yaxis_title="Drought Event Frequency",
        title_x=0.5,  # Center the title
        margin=dict(t=50, b=100),
        coloraxis_colorbar=dict(title="Frequency"),
    )

    # Show the interactive plot
    fig.show()


def setup_interactive_frequency_plot(df):
    """
    Sets up the interactive drought event frequency plot using Plotly.

    Parameters:
    - df (pd.DataFrame): DataFrame containing drought characteristics data.
    """
    # Dropdown options for dimensions
    dimension_options = ['admin2_name', 'spi_scale']

    # Create interactive widgets
    interact(
        plot_drought_event_frequency_plotly,
        df=fixed(df),
        dimension=Dropdown(
            options=dimension_options,
            description='Select Dimension:',
            style={'description_width': 'initial'}
        ),
        sort_by_height=Checkbox(
            value=False,
            description='Sort by Height',
            style={'description_width': 'initial'}
        )
    )
    
    
    
import plotly.express as px
from ipywidgets import interact, Dropdown, fixed

def plot_drought_characteristics_plotly(df, characteristic):
    """
    Plots a boxplot to compare drought characteristics across admin2 levels using Plotly Express.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    - characteristic (str): The drought characteristic to plot ('Drought Intensity', 'Drought Severity', 'Drought Duration (months)').
    """
    # Check if the selected characteristic is in the DataFrame
    if characteristic not in df.columns:
        print(f"Characteristic '{characteristic}' is not available in the DataFrame.")
        return

    # Create the Plotly Express boxplot
    fig = px.box(
        df,
        x='admin2_name',
        y=characteristic,
        title=f'Boxplot of {characteristic} by Admin2 Level',
        labels={'admin2_name': 'Admin2 Level', characteristic: characteristic},
        color_discrete_sequence=['rgba(31, 119, 180, 0.8)'],  # Consistent blue color
    )

    # Customize layout for better visualization
    fig.update_layout(
        xaxis_title="Admin2 Level",
        yaxis_title=characteristic,
        xaxis_tickangle=45,  # Rotate x-axis labels for better readability
        title_x=0.5,  # Center the title
        plot_bgcolor='rgba(240, 240, 240, 0.9)',  # Light background
        margin=dict(t=50, b=150),  # Adjust margins for readability
        showlegend=False  # No legend needed for a single color
    )

    # Show the interactive plot
    fig.show()


def setup_interactive_drought_characteristics_plot(df):
    """
    Sets up the interactive dropdown widgets for comparing drought characteristics.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    """
    # Dropdown options for characteristics
    characteristic_options = ['Drought Intensity', 'Drought Severity', 'Drought Duration (months)']

    # Create interactive dropdown widget for selecting characteristic
    interact(
        plot_drought_characteristics_plotly,
        df=fixed(df),
        characteristic=Dropdown(
            options=characteristic_options,
            description='Select Characteristic:',
            style={'description_width': 'initial'}
        )
    )


    
import plotly.express as px
from ipywidgets import interact, Dropdown, fixed

def plot_correlation_analysis_plotly(df, x_variable, y_variable):
    """
    Plots an interactive scatter plot to analyze the correlation between two selected drought characteristics.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    - x_variable (str): The x-axis drought characteristic to plot.
    - y_variable (str): The y-axis drought characteristic to plot.
    """
    # Check if the selected variables are in the DataFrame
    if x_variable not in df.columns or y_variable not in df.columns:
        print(f"One or both selected characteristics are not available in the DataFrame.")
        return

    # Create the scatter plot using Plotly Express
    fig = px.scatter(
        df,
        x=x_variable,
        y=y_variable,
        color='admin2_name',  # Use 'admin2_name' for coloring
        title=f'Scatter Plot of {y_variable} vs {x_variable}',
        labels={x_variable: x_variable, y_variable: y_variable},
        hover_data=['admin2_name'],  # Add 'admin2_name' to hover info
        opacity=0.7,  # Adjust point transparency for better visibility
        color_discrete_sequence=px.colors.qualitative.T10  # Use a qualitative color palette
    )

    # Customize layout for better visualization
    fig.update_layout(
        xaxis_title=x_variable,
        yaxis_title=y_variable,
        title_x=0.5,  # Center the title
        margin=dict(t=50, b=100),  # Adjust margins for readability
        legend_title="Admin2 Name"
    )

    # Show the interactive plot
    fig.show()


def setup_interactive_correlation_analysis_plot(df):
    """
    Sets up the interactive dropdown widgets for correlation analysis.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    """
    # Dropdown options for characteristics
    correlation_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']

    # Create interactive dropdown widgets for selecting x and y variables
    interact(
        plot_correlation_analysis_plotly,
        df=fixed(df),
        x_variable=Dropdown(
            options=correlation_options,
            description='Select X Variable:',
            style={'description_width': 'initial'}
        ),
        y_variable=Dropdown(
            options=correlation_options,
            description='Select Y Variable:',
            style={'description_width': 'initial'}
        )
    )
    
    

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ipywidgets import interact, Dropdown, fixed

def plot_drought_analysis_custom(df, characteristic):
    """
    Custom grouped bar chart comparing drought characteristics by admin2_name and SPI scale.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    - characteristic (str): The drought characteristic to plot (e.g., 'Drought Duration', 'Drought Severity', 'Drought Intensity').
    """
    # Ensure spi_scale is numeric
    df['spi_scale'] = pd.to_numeric(df['spi_scale'], errors='coerce')

    # Check if the selected characteristic is in the DataFrame
    if characteristic not in df.columns:
        print(f"The selected characteristic '{characteristic}' is not available in the DataFrame.")
        return

    # Group the DataFrame by 'admin2_name' and 'spi_scale', and calculate the mean for the selected characteristic
    grouped_df = df.groupby(['admin2_name', 'spi_scale'])[characteristic].mean().reset_index()

    # Create a plotly figure
    fig = go.Figure()

    # Add bars for each SPI scale
    for spi_value in grouped_df['spi_scale'].unique():
        spi_data = grouped_df[grouped_df['spi_scale'] == spi_value]
        fig.add_trace(go.Bar(
            x=spi_data['admin2_name'],
            y=spi_data[characteristic],
            name=f"SPI Scale {int(spi_value)}",
            marker=dict(color=spi_value, coloraxis="coloraxis")
        ))

    # Update layout for the figure
    fig.update_layout(
        title=f"Comparison of {characteristic} by Admin2 Name and SPI Scale",
        xaxis_title="Admin2 Name",
        yaxis_title=f"Mean {characteristic}",
        xaxis_tickangle=45,
        barmode='group',
        coloraxis=dict(
            colorscale="Viridis",
            colorbar=dict(title="SPI Scale")
        ),
        margin=dict(t=50, b=150)
    )

    # Show the plot
    fig.show()


def setup_interactive_drought_analysis_custom(df):
    """
    Sets up the interactive dropdown widget for drought analysis.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    """
    # Dropdown options for drought characteristics
    characteristic_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']

    # Create an interactive dropdown widget for selecting the characteristic
    interact(
        plot_drought_analysis_custom,
        df=fixed(df),
        characteristic=Dropdown(
            options=characteristic_options,
            description='Select Characteristic:',
            style={'description_width': 'initial'}
        )
    )
    
    
    
import pandas as pd
import plotly.express as px
from ipywidgets import interact, Dropdown, fixed

def plot_temporal_heatmap_with_spi(df, characteristic, spi_scale):
    """
    Plots a temporal heatmap to analyze drought characteristics over time across regions using Plotly,
    filtered by SPI scale.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    - characteristic (str): The drought characteristic to plot (e.g., 'Drought Severity', 'Drought Duration (months)', 'Drought Intensity').
    - spi_scale (int): The selected SPI scale to filter the data.
    """
    # Ensure the chosen characteristic is in the DataFrame
    if characteristic not in df.columns:
        print(f"Characteristic '{characteristic}' is not available in the DataFrame.")
        return

    # Filter the DataFrame by the selected SPI scale
    df_filtered = df[df['spi_scale'] == spi_scale].copy()  # Use `.copy()` to avoid SettingWithCopyWarning

    # Convert 'Drought Start' to datetime and extract month-year for better granularity
    df_filtered['Drought Start'] = pd.to_datetime(df_filtered['Drought Start'], errors='coerce')
    df_filtered['Month-Year'] = df_filtered['Drought Start'].dt.to_period('M').astype(str)

    # Create a pivot table with 'admin2_name' as the index, 'Month-Year' as columns, and the chosen characteristic as values
    heatmap_data = df_filtered.pivot_table(index='admin2_name', columns='Month-Year', values=characteristic, aggfunc='mean')

    # Convert the pivot table into a long-format DataFrame for Plotly
    heatmap_data_long = heatmap_data.reset_index().melt(id_vars='admin2_name', var_name='Month-Year', value_name=characteristic)

    # Select the appropriate color scale
    if characteristic in ['Drought Severity', 'Drought Intensity']:
        color_scale = 'YlOrRd_r'  # Reverse the scale for Severity and Intensity
    else:
        color_scale = 'YlOrRd'

    # Plot the heatmap using Plotly Express
    fig = px.density_heatmap(
        heatmap_data_long,
        x='Month-Year',
        y='admin2_name',
        z=characteristic,
        color_continuous_scale=color_scale,
        title=f'Temporal Heatmap of {characteristic} Across Regions (SPI Scale {spi_scale})',
        labels={'Month-Year': 'Time (Month-Year)', 'admin2_name': 'Admin2 Name', characteristic: characteristic}
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_tickangle=45,
        xaxis_title='Time (Month-Year)',
        yaxis_title='Admin2 Name',
        coloraxis_colorbar=dict(title=characteristic),
        margin=dict(t=50, l=50, r=50, b=100),
        height=600
    )

    # Show the plot
    fig.show()

def setup_interactive_heatmap_with_spi(df):
    """
    Sets up the interactive widget for the temporal heatmap with SPI scale selection.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought characteristics data.
    """
    # Dropdown options for drought characteristics
    characteristic_options = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']

    # Dropdown options for SPI scale
    spi_scale_options = sorted(df['spi_scale'].unique().tolist())

    # Use `interact` to create an interactive heatmap based on the selected characteristic and SPI scale
    interact(
        plot_temporal_heatmap_with_spi,
        df=fixed(df),
        characteristic=Dropdown(
            options=characteristic_options,
            description='Select Characteristic:',
            style={'description_width': 'initial'}
        ),
        spi_scale=Dropdown(
            options=spi_scale_options,
            description='Select SPI Scale:',
            style={'description_width': 'initial'}
        )
    )


    
import matplotlib.pyplot as plt
from ipywidgets import interact, Dropdown

def plot_geospatial_drought_map_static(drought_gdf, characteristic):
    """
    Plots a static geospatial map showing the selected drought characteristic.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing the drought and geospatial data.
    - characteristic (str): The drought characteristic to plot (e.g., 'Drought Duration', 'Drought Severity', 'Drought Intensity').
    """
    # Check if the characteristic exists in the GeoDataFrame
    if characteristic not in drought_gdf.columns:
        print(f"Error: The column '{characteristic}' does not exist in the GeoDataFrame.")
        return

    # Set the color map conditionally
    if characteristic == 'Drought Duration (months)':
        cmap = 'YlOrRd'  # Default color map for Drought Duration
    else:
        cmap = 'YlOrRd_r'  # Reversed color map for Severity and Intensity

    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot the GeoDataFrame
    drought_gdf.plot(
        column=characteristic,  # Column to be visualized
        cmap=cmap,              # Conditional color map
        linewidth=0.8,          # Line width for boundaries
        ax=ax,                  # Axis to plot on
        edgecolor='black',      # Edge color
        legend=True             # Include a legend
    )

    # Customize the title and remove axis
    plt.title(f'{characteristic} by Administrative Unit', fontsize=15)
    plt.axis('off')

    # Display the map
    plt.show()


def setup_interactive_geospatial_plot(drought_gdf):
    """
    Sets up an interactive widget for plotting geospatial drought maps.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing the drought and geospatial data.
    """
    # Get the available characteristics for plotting
    available_characteristics = ['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']

    # Use interact to create an interactive dropdown for the selected characteristic
    interact(
        plot_geospatial_drought_map_static,
        drought_gdf=fixed(drought_gdf),
        characteristic=Dropdown(
            options=available_characteristics,
            description='Characteristic:',
            style={'description_width': 'initial'}
        )
    )
    
    

import pandas as pd
from ipywidgets import interact, Dropdown, fixed
import pymannkendall as mk  # Ensure this library is installed

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

def categorize_trends(trend_analysis_df):
    """
    Categorize regions into increasing, decreasing, and no trends.

    Parameters:
    trend_analysis_df (pd.DataFrame): DataFrame containing trend analysis results.

    Returns:
    tuple: Three lists for increasing, decreasing, and no trends.
    """
    increasing_trends = trend_analysis_df[trend_analysis_df['trend'] == 'increasing'].index.tolist()
    decreasing_trends = trend_analysis_df[trend_analysis_df['trend'] == 'decreasing'].index.tolist()
    no_trend = trend_analysis_df[trend_analysis_df['trend'] == 'no trend'].index.tolist()
    return increasing_trends, decreasing_trends, no_trend

def setup_interactive_trend_explorer(trend_analysis_df):
    """
    Sets up an interactive widget to explore regions based on trend categories.

    Parameters:
    trend_analysis_df (pd.DataFrame): DataFrame with trend analysis results.
    """
    increasing_trends, decreasing_trends, no_trend = categorize_trends(trend_analysis_df)

    def list_trend_regions(category):
        """
        List regions based on selected trend category.

        Parameters:
        - category (str): Trend category ('Increasing', 'Decreasing', 'No Trend').
        """
        if category == "Increasing":
            regions = increasing_trends
        elif category == "Decreasing":
            regions = decreasing_trends
        elif category == "No Trend":
            regions = no_trend
        else:
            print(f"Invalid category: {category}")
            return

        # Display the regions
        if regions:
            print(f"Regions with {category.lower()} trend:")
            for region in regions:
                print(region)
        else:
            print(f"No regions found for {category.lower()} trend.")

    # Interactive dropdown
    interact(
        list_trend_regions,
        category=Dropdown(
            options=["Increasing", "Decreasing", "No Trend"],
            description="Select Trend:",
            style={'description_width': 'initial'}
        )
    )

    