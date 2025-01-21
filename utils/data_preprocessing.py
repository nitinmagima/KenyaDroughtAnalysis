
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import geopandas as gpd
import ee

############################################################################################

'''

Functions to load and preprocess CHIRPS rainfall data

'''

############################################################################################

def initialize_ee():
    """
    Initialize Google Earth Engine with authentication and project setup.
    """
    ee.Authenticate()
    ee.Initialize(project='ee-sg4283')  # Replace with your project ID


def fetch_precipitation_data_admin2(admin2_name):
    """
    Fetch monthly precipitation data for a given Admin Level 2 region in Zambia for 2000 to 2023,
    and return a restructured DataFrame with the following columns:
    - year, month, date, region, admin2_name, precipitation.
    """
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
    startyear, endyear = 2000, 2023
    startdate, enddate = ee.Date.fromYMD(startyear, 1, 1), ee.Date.fromYMD(endyear, 12, 31)

    # Define the region from Zambia (Admin Level 2)
    region = ee.FeatureCollection('FAO/GAUL/2015/level2') \
              .filter(ee.Filter.eq('ADM0_NAME', 'Zambia')) \
              .filter(ee.Filter.eq('ADM2_NAME', admin2_name)).first()

    def MonthlySum(year):
        """
        Sum precipitation data for each month of a given year.
        """
        def monthSum(month):
            # Filter the CHIRPS dataset for the specific month and year
            monthly_sum = chirps.filterDate(startdate, enddate) \
                                .filter(ee.Filter.calendarRange(year, year, 'year')) \
                                .filter(ee.Filter.calendarRange(month, month, 'month')) \
                                .sum() \
                                .reduceRegion(ee.Reducer.mean(), geometry=region.geometry(), scale=5000, maxPixels=1e8)

            # Return the precipitation data and additional info
            return ee.Feature(None, {
                'year': year,
                'month': month,
                'date': ee.Date.fromYMD(year, month, 1).format(),
                'region': 'Zambia',
                'admin2_name': admin2_name,
                'precipitation': monthly_sum.get('precipitation')
            })
        return ee.List.sequence(1, 12).map(monthSum)

    years = ee.List.sequence(startyear, endyear)
    monthlyPrecip = years.map(MonthlySum).flatten()
    monthlyPrecipCollection = ee.FeatureCollection(monthlyPrecip)

    properties_list = monthlyPrecipCollection.getInfo()

    if properties_list['features']:
        data = [feature['properties'] for feature in properties_list['features']]
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame()

    def restructure_dataframe(df):
        """
        Restructure the DataFrame to match the desired column order:
        ['year', 'month', 'date', 'region', 'admin2_name', 'precipitation']
        """
        desired_order = ['year', 'month', 'date', 'region', 'admin2_name', 'precipitation']
        return df[desired_order]

    return restructure_dataframe(df)


def fetch_and_combine_precipitation_data(admin2_names):
    """
    Fetch and combine monthly precipitation data for all Admin Level 2 regions in Zambia
    from 2000 to 2023, and return a single combined DataFrame.

    Parameters:
    admin2_names (list): List of Admin Level 2 region names.

    Returns:
    pd.DataFrame: Combined DataFrame containing precipitation data for all regions.
    """
    all_precip_data = []

    for admin2_name in admin2_names:
        print(f"Fetching precipitation data for {admin2_name}...")
        df = fetch_precipitation_data_admin2(admin2_name)
        all_precip_data.append(df)

    combined_df = pd.concat(all_precip_data, ignore_index=True)
    return combined_df


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

Calculates drought averages by admin2 zones by SPI1 and SPI3 respectively

'''

############################################################################################

def calculate_admin2_drought_averages(df):
    """
    Calculate the averages of Drought Duration (months), Drought Severity, and Drought Intensity
    for each admin2_name by SPI scales (1 and 3), and include the spi_scale column.

    Parameters:
    - df (GeoDataFrame): Input GeoDataFrame containing drought data.

    Returns:
    - tuple: Two GeoDataFrames:
        - spi1_averages: Averages for SPI1 with spi_scale column.
        - spi3_averages: Averages for SPI3 with spi_scale column.
    """
    # Filter for SPI1
    spi1_df = df[df['spi_scale'] == 1]
    spi1_averages = (
        spi1_df.groupby('admin2_name')
        .agg({
            'Drought Duration (months)': 'mean',
            'Drought Severity': 'mean',
            'Drought Intensity': 'mean',
            'geometry': 'first'  # Retain geometry
        })
        .reset_index()
    )
    spi1_averages['spi_scale'] = 1  # Add spi_scale column
    spi1_averages = gpd.GeoDataFrame(spi1_averages, geometry='geometry')

    # Filter for SPI3
    spi3_df = df[df['spi_scale'] == 3]
    spi3_averages = (
        spi3_df.groupby('admin2_name')
        .agg({
            'Drought Duration (months)': 'mean',
            'Drought Severity': 'mean',
            'Drought Intensity': 'mean',
            'geometry': 'first'  # Retain geometry
        })
        .reset_index()
    )
    spi3_averages['spi_scale'] = 3  # Add spi_scale column
    spi3_averages = gpd.GeoDataFrame(spi3_averages, geometry='geometry')

    # Ensure CRS for both GeoDataFrames
    for gdf in [spi1_averages, spi3_averages]:
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)
        else:
            gdf.to_crs("EPSG:4326", inplace=True)

    return spi1_averages, spi3_averages


############################################################################################

'''
Preprocessing functions for getting the SPI1 and SPI3 dataframes that have k-means
and hierarchical cluster indicators

-Used after the clustering 
-Functions are called simultaneously process_all_drought_data function below 

'''


############################################################################################

def filter_and_merge_with_clusters(drought_gdf, cluster_boundaries_df=None):
    """
    Filters the drought data for SPI1 and SPI3, then merges with either KMeans or Hierarchical cluster boundaries.
    Adds an indicator column 'kmeans' set to 1 if KMeans clusters are used, and 0 if Hierarchical clusters are used.
    
    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing the drought data.
    - cluster_boundaries_df (GeoDataFrame, optional): The KMeans or Hierarchical cluster boundaries GeoDataFrame.
    
    Returns:
    - spi1_merged (GeoDataFrame): The SPI1 DataFrame merged with the cluster boundaries, with indicator.
    - spi3_merged (GeoDataFrame): The SPI3 DataFrame merged with the cluster boundaries, with indicator.
    """
    
    # Filter for SPI1 and SPI3
    spi1_df = drought_gdf[drought_gdf['spi_scale'] == 1]
    spi3_df = drought_gdf[drought_gdf['spi_scale'] == 3]
    
    # Check if cluster boundaries are passed
    if cluster_boundaries_df is not None:
        # Add indicator column for KMeans or Hierarchical
        if 'cluster' in cluster_boundaries_df.columns:
            cluster_boundaries_df['kmeans'] = 1  # KMeans indicator
            spi1_merged = gpd.sjoin(spi1_df, cluster_boundaries_df, how="left", predicate='intersects')
            spi3_merged = gpd.sjoin(spi3_df, cluster_boundaries_df, how="left", predicate='intersects')
        
        elif 'hierarchical_cluster' in cluster_boundaries_df.columns:
            cluster_boundaries_df['kmeans'] = 0  # Hierarchical indicator
            spi1_merged = gpd.sjoin(spi1_df, cluster_boundaries_df, how="left", predicate='intersects')
            spi3_merged = gpd.sjoin(spi3_df, cluster_boundaries_df, how="left", predicate='intersects')
        
        else:
            raise KeyError("Neither 'cluster' nor 'hierarchical_cluster' columns found in the cluster_boundaries_df.")
        
        # After merge, clean up columns and rename
        if 'cluster_right' in spi1_merged.columns:
            spi1_merged = spi1_merged.drop(columns=['cluster_right', 'index_right'])
            spi1_merged = spi1_merged.rename(columns={'cluster_left': 'cluster'})
        
        if 'hierarchical_cluster_right' in spi1_merged.columns:
            spi1_merged = spi1_merged.drop(columns=['hierarchical_cluster_right', 'index_right'])
            spi1_merged = spi1_merged.rename(columns={'hierarchical_cluster_left': 'hierarchical_cluster'})
        
        if 'cluster_right' in spi3_merged.columns:
            spi3_merged = spi3_merged.drop(columns=['cluster_right', 'index_right'])
            spi3_merged = spi3_merged.rename(columns={'cluster_left': 'cluster'})
        
        if 'hierarchical_cluster_right' in spi3_merged.columns:
            spi3_merged = spi3_merged.drop(columns=['hierarchical_cluster_right', 'index_right'])
            spi3_merged = spi3_merged.rename(columns={'hierarchical_cluster_left': 'hierarchical_cluster'})

        # Drop duplicates
        spi1_merged = spi1_merged.drop_duplicates()
        spi3_merged = spi3_merged.drop_duplicates()
        
        return spi1_merged, spi3_merged
    
    else:
        # If no cluster boundaries are provided, return the original dataframes
        return spi1_df, spi3_df


def calculate_drought_averages_with_indicator(spi1_merged, spi3_merged):
    """
    Calculate average drought characteristics by cluster or hierarchical cluster, maintaining the 'spi_scale' and 'kmeans' indicator.
    Excludes rows where 'Drought Duration (months)' is zero from the calculation.
    
    Parameters:
    - spi1_merged (GeoDataFrame): Merged SPI1 data with cluster boundaries and kmeans indicator.
    - spi3_merged (GeoDataFrame): Merged SPI3 data with cluster boundaries and kmeans indicator.
    
    Returns:
    - spi1_avg (GeoDataFrame): SPI1 averages per cluster or hierarchical cluster with indicator and spi_scale.
    - spi3_avg (GeoDataFrame): SPI3 averages per cluster or hierarchical cluster with indicator and spi_scale.
    """
    # Filter out rows where 'Drought Duration (months)' is zero
    spi1_filtered = spi1_merged[spi1_merged['Drought Duration (months)'] > 0]
    spi3_filtered = spi3_merged[spi3_merged['Drought Duration (months)'] > 0]
    
    # For SPI1, group by 'cluster' if kmeans == 1, else group by 'hierarchical_cluster' if kmeans == 0
    if spi1_filtered['kmeans'].iloc[0] == 1:  # Check if kmeans == 1
        spi1_avg = spi1_filtered.groupby(
            ['cluster', 'spi_scale', 'kmeans']
        )[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']].mean().reset_index()
    else:
        spi1_avg = spi1_filtered.groupby(
            ['hierarchical_cluster', 'spi_scale', 'kmeans']
        )[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']].mean().reset_index()

    # For SPI3, group by 'cluster' if kmeans == 1, else group by 'hierarchical_cluster' if kmeans == 0
    if spi3_filtered['kmeans'].iloc[0] == 1:  # Check if kmeans == 1
        spi3_avg = spi3_filtered.groupby(
            ['cluster', 'spi_scale', 'kmeans']
        )[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']].mean().reset_index()
    else:
        spi3_avg = spi3_filtered.groupby(
            ['hierarchical_cluster', 'spi_scale', 'kmeans']
        )[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']].mean().reset_index()

    return spi1_avg, spi3_avg


def calculate_drought_averages_by_admin2(spi1_merged, spi3_merged):
    """
    Calculate average drought characteristics by admin2 zone, maintaining the 'spi_scale', 'kmeans' indicators, 
    and the 'cluster' and 'hierarchical_cluster' columns, as well as geometry.
    This function includes the '_admin2' suffix for clarity.
    
    Parameters:
    - spi1_merged (GeoDataFrame): Merged SPI1 data with cluster boundaries and kmeans indicator.
    - spi3_merged (GeoDataFrame): Merged SPI3 data with cluster boundaries and kmeans indicator.
    
    Returns:
    - spi1_avg_admin2 (GeoDataFrame): SPI1 averages per admin2 zone with indicator and spi_scale.
    - spi3_avg_admin2 (GeoDataFrame): SPI3 averages per admin2 zone with indicator and spi_scale.
    """
    # Calculate average for SPI1 data by admin2 zone, keeping the kmeans indicator and cluster/hierarchical_cluster columns
    spi1_avg_admin2 = spi1_merged.groupby(['admin2_name', 'spi_scale', 'kmeans'], as_index=False)[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']].mean()
    spi1_avg_admin2 = spi1_avg_admin2.rename(columns={
        'Drought Duration (months)': 'Drought Duration (months)_admin2',
        'Drought Severity': 'Drought Severity_admin2',
        'Drought Intensity': 'Drought Intensity_admin2'
    })

    # Retain the correct cluster and hierarchical_cluster values by using 'first' (as they should be the same for each admin2_name)
    spi1_avg_admin2['cluster'] = spi1_merged.groupby('admin2_name')['cluster'].first().values
    spi1_avg_admin2['hierarchical_cluster'] = spi1_merged.groupby('admin2_name')['hierarchical_cluster'].first().values

    # Retain geometry using first value in each admin2_name group
    spi1_avg_admin2['geometry'] = spi1_merged.groupby('admin2_name')['geometry'].first().values

    # Calculate average for SPI3 data by admin2 zone, keeping the kmeans indicator and cluster/hierarchical_cluster columns
    spi3_avg_admin2 = spi3_merged.groupby(['admin2_name', 'spi_scale', 'kmeans'], as_index=False)[['Drought Duration (months)', 'Drought Severity', 'Drought Intensity']].mean()
    spi3_avg_admin2 = spi3_avg_admin2.rename(columns={
        'Drought Duration (months)': 'Drought Duration (months)_admin2',
        'Drought Severity': 'Drought Severity_admin2',
        'Drought Intensity': 'Drought Intensity_admin2'
    })

    # Retain the correct cluster and hierarchical_cluster values by using 'first' (as they should be the same for each admin2_name)
    spi3_avg_admin2['cluster'] = spi3_merged.groupby('admin2_name')['cluster'].first().values
    spi3_avg_admin2['hierarchical_cluster'] = spi3_merged.groupby('admin2_name')['hierarchical_cluster'].first().values

    # Retain geometry using first value in each admin2_name group
    spi3_avg_admin2['geometry'] = spi3_merged.groupby('admin2_name')['geometry'].first().values

    return spi1_avg_admin2, spi3_avg_admin2


def merge_drought_averages(spi1_avg, spi1_avg_admin2, spi3_avg, spi3_avg_admin2, merge_type='cluster'):
    """
    Merges SPI1 and SPI3 averages with the corresponding admin2 averages for either KMeans or Hierarchical clusters.
    
    Parameters:
    - spi1_avg (GeoDataFrame): SPI1 average DataFrame.
    - spi1_avg_admin2 (GeoDataFrame): SPI1 average by admin2 DataFrame.
    - spi3_avg (GeoDataFrame): SPI3 average DataFrame.
    - spi3_avg_admin2 (GeoDataFrame): SPI3 average by admin2 DataFrame.
    - merge_type (str): Type of merge ('cluster' or 'hierarchical_cluster') to choose the correct column for merging.

    Returns:
    - spi1_combined (GeoDataFrame): Merged SPI1 averages with admin2 data.
    - spi3_combined (GeoDataFrame): Merged SPI3 averages with admin2 data.
    """
    if merge_type == 'cluster':
        # Merge SPI1 and SPI3 for KMeans clusters
        spi1_combined = pd.merge(spi1_avg, spi1_avg_admin2, 
                                 on=['spi_scale', 'kmeans', 'cluster'], 
                                 suffixes=('_km', '_admin2'))

        spi3_combined = pd.merge(spi3_avg, spi3_avg_admin2, 
                                 on=['spi_scale', 'kmeans', 'cluster'], 
                                 suffixes=('_km', '_admin2'))

    elif merge_type == 'hierarchical_cluster':
        # Merge SPI1 and SPI3 for Hierarchical clusters
        spi1_combined = pd.merge(spi1_avg, spi1_avg_admin2, 
                                 on=['spi_scale', 'kmeans', 'hierarchical_cluster'], 
                                 suffixes=('_hc', '_admin2'))

        spi3_combined = pd.merge(spi3_avg, spi3_avg_admin2, 
                                 on=['spi_scale', 'kmeans', 'hierarchical_cluster'], 
                                 suffixes=('_hc', '_admin2'))

    else:
        raise ValueError("merge_type must be 'cluster' or 'hierarchical_cluster'")

    return spi1_combined, spi3_combined


def reorder_and_sort_columns(*dfs):
    """
    Reorders columns and sorts by 'admin2_name' for the given DataFrames, 
    keeping the original DataFrame names.
    
    The desired column order is:
    ['admin2_name', 'geometry', 'spi_scale', 'cluster', 'hierarchical_cluster', 
     'Drought Duration (months)', 'Drought Severity', 'Drought Intensity', 
     'Drought Duration (months)_admin2', 'Drought Severity_admin2', 'Drought Intensity_admin2', 'kmeans']
    
    Parameters:
    - dfs: DataFrames to reorder and sort.
    
    Returns:
    - A list of DataFrames with columns reordered and sorted by 'admin2_name'.
    """
    # Define the desired column order
    desired_columns = [
        'admin2_name', 'geometry', 'spi_scale', 'cluster', 'hierarchical_cluster', 
        'Drought Duration (months)', 'Drought Severity', 'Drought Intensity', 
        'Drought Duration (months)_admin2', 'Drought Severity_admin2', 'Drought Intensity_admin2', 'kmeans'
    ]
    
    # Reorder and sort each DataFrame, store in a list
    reordered_dfs = []
    for df in dfs:
        df = df[desired_columns]  # Reorder columns
        df = df.sort_values(by='admin2_name')  # Sort by admin2_name
        reordered_dfs.append(df)
    
    return reordered_dfs


def calculate_differences(*dfs):
    """
    Calculates the differences between the relevant columns for the given DataFrames.
    Differences are calculated between 'Drought Duration (months)', 'Drought Severity', 
    'Drought Intensity', and their '_admin2' counterparts. Ensures that if 
    'Drought Duration (months)_admin2' is 0, all difference columns are set to 0.
    
    Parameters:
    - dfs: DataFrames to calculate the differences.
    
    Returns:
    - A list of DataFrames with added difference columns.
    """
    diff_dfs = []
    for df in dfs:
        # Calculate differences for each relevant column
        df['Drought Duration Diff'] = df['Drought Duration (months)'] - df['Drought Duration (months)_admin2']
        df['Drought Severity Diff'] = df['Drought Severity'] - df['Drought Severity_admin2']
        df['Drought Intensity Diff'] = df['Drought Intensity'] - df['Drought Intensity_admin2']
        
        # Set differences to 0 where 'Drought Duration (months)_admin2' is 0
        zero_mask = df['Drought Duration (months)_admin2'] == 0
        df.loc[zero_mask, ['Drought Duration Diff', 'Drought Severity Diff', 'Drought Intensity Diff']] = 0
        
        # Add the modified DataFrame to the list
        diff_dfs.append(df)
    
    return diff_dfs


def merge_spi_differences(spi1_combined_diff, spi3_combined_diff, geometry_col='geometry'):
    """
    Concatenates SPI1 and SPI3 combined data for KMeans or Hierarchical clusters
    and converts the final result to a GeoDataFrame.

    Parameters:
    - spi1_combined_diff (GeoDataFrame or DataFrame): SPI1 combined difference DataFrame.
    - spi3_combined_diff (GeoDataFrame or DataFrame): SPI3 combined difference DataFrame.
    - geometry_col (str): Name of the column containing geometry data. Default is 'geometry'.

    Returns:
    - final_diff_df (GeoDataFrame): A GeoDataFrame containing the merged SPI1 and SPI3 differences.
    """
    # Concatenate the differences for KMeans or Hierarchical clusters
    final_diff_df = pd.concat([spi1_combined_diff, spi3_combined_diff], ignore_index=True)

    # Convert to GeoDataFrame if necessary
    if geometry_col in final_diff_df.columns:
        final_diff_df = gpd.GeoDataFrame(final_diff_df, geometry=geometry_col)
    else:
        raise KeyError(f"Column '{geometry_col}' not found in the DataFrame.")

    return final_diff_df


############################################################################################

'''
Calls all seven functions from above
'''

############################################################################################

def process_all_drought_data(
    drought_gdf, 
    kmeans_cluster_boundaries_df, 
    hierarchical_cluster_boundaries_df, 
    return_type="final_diff"
):
    """
    Process the drought data by filtering, merging with clusters, calculating averages,
    and calculating differences. Allows returning either final difference DataFrames or admin2 averages.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing the drought data.
    - kmeans_cluster_boundaries_df (GeoDataFrame): The KMeans cluster boundaries GeoDataFrame.
    - hierarchical_cluster_boundaries_df (GeoDataFrame): The Hierarchical cluster boundaries GeoDataFrame.
    - return_type (str): Specify what to return. Options:
        - "final_diff" (default): Return final difference DataFrames.
        - "admin2_avg": Return admin2 averages as GeoDataFrames.

    Returns:
    - Depends on return_type:
        - "final_diff": 
            - final_diff_df_km (GeoDataFrame): Final merged and difference calculated GeoDataFrame for KMeans.
            - final_diff_df_hc (GeoDataFrame): Final merged and difference calculated GeoDataFrame for Hierarchical clusters.
        - "admin2_avg": 
            - spi1_avg_admin2_km (GeoDataFrame): SPI1 averages by Admin2 for KMeans.
            - spi3_avg_admin2_km (GeoDataFrame): SPI3 averages by Admin2 for KMeans.
            - spi1_avg_admin2_hc (GeoDataFrame): SPI1 averages by Admin2 for Hierarchical clusters.
            - spi3_avg_admin2_hc (GeoDataFrame): SPI3 averages by Admin2 for Hierarchical clusters.
    """
    # Filter and Merge with Cluster Boundaries (for both KMeans and Hierarchical clusters)
    spi1_merged_km, spi3_merged_km = filter_and_merge_with_clusters(drought_gdf, kmeans_cluster_boundaries_df)
    spi1_merged_hc, spi3_merged_hc = filter_and_merge_with_clusters(drought_gdf, hierarchical_cluster_boundaries_df)
    
    # Calculate Drought Averages with Indicator (for both KMeans and Hierarchical clusters)
    spi1_avg_km, spi3_avg_km = calculate_drought_averages_with_indicator(spi1_merged_km, spi3_merged_km)
    spi1_avg_hc, spi3_avg_hc = calculate_drought_averages_with_indicator(spi1_merged_hc, spi3_merged_hc)
    
    # Calculate Drought Averages by Admin2 (for both KMeans and Hierarchical clusters)
    spi1_avg_admin2_km, spi3_avg_admin2_km = calculate_drought_averages_by_admin2(spi1_merged_km, spi3_merged_km)
    spi1_avg_admin2_hc, spi3_avg_admin2_hc = calculate_drought_averages_by_admin2(spi1_merged_hc, spi3_merged_hc)
    
    if return_type == "admin2_avg":
        # Ensure averages are GeoDataFrames
        spi1_avg_admin2_km = gpd.GeoDataFrame(spi1_avg_admin2_km, geometry='geometry', crs="EPSG:4326")
        spi3_avg_admin2_km = gpd.GeoDataFrame(spi3_avg_admin2_km, geometry='geometry', crs="EPSG:4326")
        spi1_avg_admin2_hc = gpd.GeoDataFrame(spi1_avg_admin2_hc, geometry='geometry', crs="EPSG:4326")
        spi3_avg_admin2_hc = gpd.GeoDataFrame(spi3_avg_admin2_hc, geometry='geometry', crs="EPSG:4326")
        return spi1_avg_admin2_km, spi3_avg_admin2_km, spi1_avg_admin2_hc, spi3_avg_admin2_hc

    # Merge the Averages (for both KMeans and Hierarchical clusters)
    spi1_combined_km, spi3_combined_km = merge_drought_averages(spi1_avg_km, spi1_avg_admin2_km, spi3_avg_km, spi3_avg_admin2_km, merge_type='cluster')
    spi1_combined_hc, spi3_combined_hc = merge_drought_averages(spi1_avg_hc, spi1_avg_admin2_hc, spi3_avg_hc, spi3_avg_admin2_hc, merge_type='hierarchical_cluster')
    
    # Reorder and Sort Columns (for both KMeans and Hierarchical clusters)
    spi1_combined_km, spi3_combined_km = reorder_and_sort_columns(spi1_combined_km, spi3_combined_km)
    spi1_combined_hc, spi3_combined_hc = reorder_and_sort_columns(spi1_combined_hc, spi3_combined_hc)
    
    # Calculate the Differences (for both KMeans and Hierarchical clusters)
    spi1_combined_km_diff, spi3_combined_km_diff = calculate_differences(spi1_combined_km, spi3_combined_km)
    spi1_combined_hc_diff, spi3_combined_hc_diff = calculate_differences(spi1_combined_hc, spi3_combined_hc)
    
    # Merge and Calculate Differences (for both KMeans and Hierarchical clusters)
    final_diff_df_km = merge_spi_differences(spi1_combined_km_diff, spi3_combined_km_diff)
    final_diff_df_hc = merge_spi_differences(spi1_combined_hc_diff, spi3_combined_hc_diff)

    return final_diff_df_km, final_diff_df_hc


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

Add saving cluster boundaries and clustering preprocessing 

'''

############################################################################################



def save_regular_cluster_boundaries(gdf, output_path):
    """
    Dissolve GeoDataFrame by K-Means clusters and save to a file.

    Parameters:
    - gdf (GeoDataFrame): Input GeoDataFrame containing K-Means cluster information.
    - output_path (str): File path to save the dissolved boundaries.
    """
    regular_cluster_boundaries = gdf.dissolve(by='cluster', aggfunc='sum').reset_index()
    regular_cluster_boundaries.to_file(output_path, driver='GeoJSON')
    print(f"Regular cluster boundaries saved successfully to {output_path}")


def save_hierarchical_cluster_boundaries(gdf, output_path):
    """
    Dissolve GeoDataFrame by Hierarchical clusters and save to a file.

    Parameters:
    - gdf (GeoDataFrame): Input GeoDataFrame containing Hierarchical cluster information.
    - output_path (str): File path to save the dissolved boundaries.
    """
    hierarchical_cluster_boundaries = gdf.dissolve(by='hierarchical_cluster', aggfunc='sum').reset_index()
    hierarchical_cluster_boundaries.to_file(output_path, driver='GeoJSON')
    print(f"Hierarchical cluster boundaries saved successfully to {output_path}")

############################################################################################

'''
Returns dataframe with K-Means and Hiearachical cluster geometries 
'''

############################################################################################

def load_and_prepare_cluster_boundaries(kmeans_path, hierarchical_path):
    """
    Load, clean, and prepare GeoDataFrames for k-means and hierarchical clustering boundaries.

    Parameters:
    - kmeans_path (str): Path to the k-means cluster boundaries GeoJSON file.
    - hierarchical_path (str): Path to the hierarchical cluster boundaries GeoJSON file.

    Returns:
    - tuple: A tuple containing two GeoDataFrames:
        - kmeans_cluster_boundaries_df: Cleaned GeoDataFrame for k-means clusters.
        - hierarchical_cluster_boundaries_df: Cleaned GeoDataFrame for hierarchical clusters.
    """
    # Load the GeoJSON files into GeoDataFrames
    kmeans_cluster_boundaries_df = gpd.read_file(kmeans_path)
    hierarchical_cluster_boundaries_df = gpd.read_file(hierarchical_path)

    # Drop unnecessary columns (2nd to 6th columns by position)
    kmeans_cluster_boundaries_df = kmeans_cluster_boundaries_df.drop(
        kmeans_cluster_boundaries_df.iloc[:, 1:7].columns, axis=1
    )
    hierarchical_cluster_boundaries_df = hierarchical_cluster_boundaries_df.drop(
        hierarchical_cluster_boundaries_df.iloc[:, 1:7].columns, axis=1
    )

    # Set CRS to EPSG:4326 for both GeoDataFrames
    kmeans_cluster_boundaries_df = kmeans_cluster_boundaries_df.set_crs("EPSG:4326", allow_override=True)
    hierarchical_cluster_boundaries_df = hierarchical_cluster_boundaries_df.set_crs("EPSG:4326", allow_override=True)

    return kmeans_cluster_boundaries_df, hierarchical_cluster_boundaries_df


############################################################################################

'''

For creating SPI1 and SPI3 drought indicator dataframes

'''

############################################################################################

def generate_drought_indicators(spi_results_df, drought_gdf, spi_threshold=-1.0, spi_scale=None):
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

def calculate_drought_percentage(df, group_col):
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


