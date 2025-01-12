
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import geopandas as gpd


############################################################################################

'''
Function to merge Zambia's Administrative 2 geometry boundaries with CHIRPS rainfall data
'''

############################################################################################

def merge_admin_boundaries(zambia_rain_df, admin_boundaries):
    """
    Merge admin boundaries with the rainfall dataset, ensuring consistent column names.

    Parameters:
    zambia_rain_df (GeoDataFrame or DataFrame): The DataFrame containing rainfall data.
    admin_boundaries (GeoDataFrame): The GeoDataFrame containing administrative boundaries.

    Returns:
    GeoDataFrame: A merged GeoDataFrame with consistent column names and geometries.
    """
    # Ensure column names are consistent for merging
    admin_boundaries = admin_boundaries.rename(columns={"ADM2_NAME": "admin2_name"})
    
    # Merge the dataframes
    merged_df = admin_boundaries.merge(zambia_rain_df, on="admin2_name", how="inner")
    
    # Convert to GeoDataFrame if the merged result is not already one
    if not isinstance(merged_df, gpd.GeoDataFrame):
        merged_df = gpd.GeoDataFrame(merged_df, geometry='geometry')
    
    return merged_df


############################################################################################

'''

Function to pivot Zambia (or any country) rainfall data so admin2 zones are columns
and months are rows

-Used for preprocessing for PCA and Clustering Analyses

'''

############################################################################################


def preprocess_rain_data(df, admin_col='admin2_name', year_col='year', month_col='month', value_col='precipitation'):
    """
    Preprocesses rainfall data by combining year and month into a single column,
    and pivots the dataset with administrative regions as the index.

    Parameters:
    - df (pd.DataFrame): The input DataFrame containing rainfall data.
    - admin_col (str): The column representing administrative regions (default: 'admin2_name').
    - year_col (str): The column representing years (default: 'year').
    - month_col (str): The column representing months (default: 'month').
    - value_col (str): The column representing the precipitation values (default: 'precipitation').

    Returns:
    - pd.DataFrame: A pivoted DataFrame with 'admin2_name' as index, 'YYYY_MM' as columns, and precipitation as values.
    """
    # Create a copy of the DataFrame to avoid modifying the original
    df_processed = df.copy()

    # Combine year and month into a single column in the format 'YYYY_MM'
    df_processed['year_month'] = df_processed[year_col].astype(str) + '_' + df_processed[month_col].astype(str).str.zfill(2)

    # Drop the original 'year' and 'month' columns
    df_processed.drop(columns=[year_col, month_col], inplace=True)

    # Pivot the dataset: admin2_name as index, year_month as columns, and precipitation as values
    df_pivot = df_processed.pivot(index=admin_col, columns='year_month', values=value_col)

    return df_pivot


############################################################################################

'''

Function to normalize precipitation data

-Used for PCA

'''

############################################################################################


def normalize_precipitation_data(df, feature_range=(0, 1)):
    """
    Normalizes precipitation data using MinMaxScaler.

    Parameters:
    - df (pd.DataFrame): The pivoted DataFrame with precipitation values to be normalized.
    - feature_range (tuple): Desired range of transformed data (default: (0, 1)).

    Returns:
    - pd.DataFrame: A normalized DataFrame with the same structure as the input.
    """
    # Initialize the MinMaxScaler with the specified feature range
    scaler = MinMaxScaler(feature_range=feature_range)

    # Scale the values and retain the original structure
    df_normalized = pd.DataFrame(
        scaler.fit_transform(df),  # Scale the values
        index=df.index,            # Retain the index (e.g., admin2_name)
        columns=df.columns         # Retain the column names (e.g., year_month)
    )

    return df_normalized

############################################################################################

'''

For creating SPI1 and SPI3 drought indicator dataframes

'''

############################################################################################

def preprocess_drought_data(spi_results_df, drought_gdf, spi_threshold=-1.0, spi_scale=None):
    """
    Creates a GeoDataFrame of drought indicators for each admin2_name and year_month,
    with extracted SPI scale, geometry, and cluster information.

    Parameters:
    - spi_results_df (pd.DataFrame): SPI results DataFrame.
    - drought_gdf (GeoDataFrame): GeoDataFrame containing geometry, cluster, and administrative unit information.
    - spi_threshold (float): SPI threshold for defining drought (default is -1.0).
    - spi_scale (int or None): Filter for a specific SPI scale (e.g., 1, 3). If None, includes all scales.

    Returns:
    - GeoDataFrame: GeoDataFrame with drought indicators, geometry, and clusters.
    """
    # Create an empty list to hold the indicator rows
    drought_indicators = []

    for column in spi_results_df.columns:
        # Split the column name to extract admin2_name and SPI scale
        if not column.endswith("_month"):
            continue  # Skip columns that do not match the expected format
        admin2_name, spi_scale_str = column.rsplit('_', 2)[0:2]  # Handle the '_month' suffix
        try:
            spi_scale_value = int(spi_scale_str)
        except ValueError:
            continue  # Skip if SPI scale is not a valid integer

        # Filter by SPI scale if provided
        if spi_scale is not None and spi_scale_value != spi_scale:
            continue

        # Get the SPI series for this column
        spi_series = spi_results_df[column].dropna()

        for date, spi_value in spi_series.items():
            # Convert the date to datetime if it's not already
            if not isinstance(date, pd.Timestamp):
                date = pd.to_datetime(date)
            indicator = 1 if spi_value < spi_threshold else 0
            drought_indicators.append({
                'year_month': date.strftime('%Y-%m'),
                'admin2_name': admin2_name,
                'spi_scale': spi_scale_value,
                'indicator': indicator
            })

    # Convert the list of indicators to a DataFrame
    drought_indicator_df = pd.DataFrame(drought_indicators)

    # Debug: Check if drought_indicators is populated
    if drought_indicator_df.empty:
        raise ValueError("No drought indicators were generated. Check input data or logic.")

    # Correct formatting of admin2_name before merging
    drought_indicator_df['admin2_name'] = drought_indicator_df['admin2_name'].replace({
        "Kapiri_Mposhi": "Kapiri-Mposhi",
        "Itezhi_tezhi": "Itezhi-tezhi"
    })

    # Merge with the GeoDataFrame to include the geometry and cluster information
    if 'admin2_name' not in drought_gdf.columns:
        raise KeyError("'admin2_name' column not found in drought_gdf.")
    
    drought_gdf['admin2_name'] = drought_gdf['admin2_name'].replace({
        "Kapiri_Mposhi": "Kapiri-Mposhi",
        "Itezhi_tezhi": "Itezhi-tezhi"
    })

    drought_indicator_df = drought_indicator_df.merge(
        drought_gdf[['admin2_name', 'geometry', 'cluster', 'hierarchical_cluster']],
        on='admin2_name',
        how='left'
    )

    # Convert the result to a GeoDataFrame and set the CRS
    drought_indicator_gdf = gpd.GeoDataFrame(
        drought_indicator_df,
        geometry=drought_indicator_df['geometry'],
        crs="EPSG:4326"  # Set CRS to WGS84 (latitude/longitude)
    )

    # Remove duplicates: Ensure each admin2_name and year_month appears only once
    drought_indicator_gdf = drought_indicator_gdf.drop_duplicates(subset=['admin2_name', 'year_month', 'spi_scale'])

    return drought_indicator_gdf

############################################################################################

'''

For calculating the percentage of admin2 zones that experienced a drought in a given month
in a given K-means or Hiearchical cluster

'''

############################################################################################

def calculate_drought_stats(df, group_col):
    """
    Calculate drought statistics for each group (e.g., hierarchical_cluster or cluster):
    - Total count of admin2_name regions.
    - Total count of regions in drought per month.
    - Percentage of regions in drought per month (rounded to nearest hundredth).

    Parameters:
    - df (pd.DataFrame or gpd.GeoDataFrame): The filtered DataFrame or GeoDataFrame with required columns.
    - group_col (str): The column name to group by (e.g., 'hierarchical_cluster' or 'cluster').

    Returns:
    - total_droughts_df (pd.DataFrame): DataFrame with total regions in drought per month.
    - percentage_droughts_df (pd.DataFrame): DataFrame with percentage of regions in drought per month (reset index).
    """
    # Ensure 'year_month' is in datetime format
    if 'year_month' not in df.columns:
        raise ValueError("The input DataFrame must have a 'year_month' column in datetime format.")
    
    df['year_month'] = pd.to_datetime(df['year_month'])

    # Total count of admin2_name regions in each group
    total_regions = (
        df.groupby(group_col)['admin2_name']
        .nunique()
        .rename('total_regions')
    )

    # Count the number of admin2_name regions in drought by group and year_month
    drought_stats = (
        df.groupby([group_col, 'year_month'])
        .agg(
            total_admin2s=('admin2_name', 'nunique'),  # Total regions
            drought_admin2s=('indicator', 'sum')  # Sum of indicators for drought regions
        )
        .reset_index()
    )

    # Calculate percentage of regions in drought
    drought_stats['drought_percentage'] = (
        (drought_stats['drought_admin2s'] / drought_stats['total_admin2s']) * 100
    ).round(2)

    # Pivot for total droughts per month
    total_droughts_df = drought_stats.pivot(
        index=group_col,
        columns='year_month',
        values='drought_admin2s'
    ).fillna(0)

    # Pivot for percentage of droughts per month
    percentage_droughts_df = drought_stats.pivot(
        index=group_col,
        columns='year_month',
        values='drought_percentage'
    ).fillna(0)

    # Convert year_month columns to strings for easier display
    total_droughts_df.columns = [col.strftime('%Y-%m') for col in total_droughts_df.columns]
    percentage_droughts_df.columns = [col.strftime('%Y-%m') for col in percentage_droughts_df.columns]

    # Add total_regions as a column in both DataFrames
    total_droughts_df['total_regions'] = total_regions
    percentage_droughts_df['total_regions'] = total_regions

    # Reset the index for percentage_droughts_df
    percentage_droughts_df = percentage_droughts_df.reset_index()

    return total_droughts_df, percentage_droughts_df


