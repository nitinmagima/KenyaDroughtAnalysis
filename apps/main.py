import os
import sys
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, fcluster
from utils.data_preprocessing import preprocess_rain_data, normalize_precipitation_data, merge_admin_boundaries, load_and_prepare_cluster_boundaries
from utils.spi_funcs import calculate_spi_for_regions
from utils.drought_analysis_funcs import characterize_drought_events
from utils.unsupervised_ml_funcs import plot_kmeans_and_hierarchical_clusters

# Ensure the script starts in the main project directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
os.chdir(project_root)
sys.path.insert(0, project_root)

# Streamlit app
st.title("Zambia Rain Data Dashboard with Clustering and Drought Analysis")

# File path for the CSV and GeoJSON data
data_path = os.path.join(project_root, "data", "zambia_admin2_rs_precip.csv")
zambia_admin2_boundaries_path = os.path.join(project_root, "data", "zambia_admin2_boundaries.geojson")
kmeans_boundaries_path = os.path.join(project_root, "data", "clustering boundaries", "kmeans_cluster_boundaries.geojson")
hierarchical_boundaries_path = os.path.join(project_root, "data", "clustering boundaries", "hierarchical_cluster_boundaries.geojson")

try:
    # Load the raw rainfall data
    zambia_rain_df = pd.read_csv(data_path)
    st.write("Raw Rainfall Data", zambia_rain_df)

    # Load the administrative boundaries as a GeoDataFrame
    admin_boundaries = gpd.read_file(zambia_admin2_boundaries_path)
    st.write("Admin Boundaries Columns:", admin_boundaries.columns)  # Debugging: Check column names
    admin_boundaries.rename(columns={'ADM2_NAME': 'admin2_name'}, inplace=True)  # Ensure consistent naming
    admin_boundaries = admin_boundaries[['admin2_name', 'geometry']]  # Retain relevant columns
    st.write("Admin Boundaries Sample:", admin_boundaries.head(10))

    # Merge the CHIRPS rainfall data with the administrative boundaries
    zambia_rain_df = merge_admin_boundaries(zambia_rain_df, admin_boundaries)
    zambia_rain_df = zambia_rain_df.drop(columns=['Unnamed: 0'], errors='ignore')  # Clean up unnecessary columns
    st.write("Rainfall Data with Admin Boundaries", zambia_rain_df.head(10))

    # Calculate SPI for all regions
    spi_results_df = calculate_spi_for_regions(zambia_rain_df)
    st.write("SPI Results", spi_results_df.head())

    # Generate a DataFrame of drought events
    drought_events_df = characterize_drought_events(spi_results_df)

    # Standardize administrative region names for consistency
    drought_events_df['admin2_name'] = drought_events_df['admin2_name'].replace({
        'Itezhi_tezhi': 'Itezhi-tezhi',
        'Kapiri_Mposhi': 'Kapiri-Mposhi'
    })

    # Merge drought events with administrative boundaries
    drought_events_df = drought_events_df.merge(admin_boundaries, on='admin2_name', how='left')
    st.write("Drought Events with Admin Boundaries", drought_events_df.head(50))

    # Preprocess the data
    df_pivot_zambia_rains = preprocess_rain_data(zambia_rain_df)
    st.write("Pivoted Rainfall Data", df_pivot_zambia_rains)

    # Normalize the data
    df_normalized_zambia_rains = normalize_precipitation_data(df_pivot_zambia_rains)
    st.write("Normalized Rainfall Data", df_normalized_zambia_rains)

    # PCA for dimensionality reduction
    n_components = 12
    pca = PCA(n_components=n_components)
    reduced_features = pca.fit_transform(df_normalized_zambia_rains)

    # KMeans clustering
    n_clusters_kmeans = 5
    kmeans = KMeans(n_clusters=n_clusters_kmeans, random_state=42)
    kmeans.fit(reduced_features)
    df_pivot_zambia_rains['kmeans_cluster'] = kmeans.labels_

    # Hierarchical clustering
    linkage_matrix = linkage(reduced_features, method='ward')
    n_clusters_hierarchical = 4
    hierarchical_labels = fcluster(linkage_matrix, n_clusters_hierarchical, criterion='maxclust')
    df_pivot_zambia_rains['hierarchical_cluster'] = hierarchical_labels

    # Merge the filtered DataFrame with drought events for clustering
    zambia_clustering_gdf = gpd.GeoDataFrame(
        df_pivot_zambia_rains.merge(drought_events_df, on='admin2_name', how='inner'),
        geometry='geometry',
        crs="EPSG:4326"
    )
    st.write("Merged GeoDataFrame with Clustering Results", zambia_clustering_gdf.head())

    # Load and prepare cluster boundary GeoDataFrames
    kmeans_cluster_boundaries_df, hierarchical_cluster_boundaries_df = load_and_prepare_cluster_boundaries(
        kmeans_path=kmeans_boundaries_path,
        hierarchical_path=hierarchical_boundaries_path
    )
    st.write("KMeans Cluster Boundaries", kmeans_cluster_boundaries_df.head())
    st.write("Hierarchical Cluster Boundaries", hierarchical_cluster_boundaries_df.head())

    # Plot KMeans and Hierarchical clustering results
    try:
        plot_kmeans_and_hierarchical_clusters(
            drought_gdf=zambia_clustering_gdf,
            kmeans_title="KMeans Clustering: Rainfall Patterns",
            hierarchical_title="Hierarchical Clustering: Rainfall Patterns",
            output='streamlit'  # Streamlit-specific output
        )
        st.write("Clustering plots generated successfully.")
    except Exception as e:
        st.error(f"Error while plotting clusters: {e}")

except FileNotFoundError as e:
    st.error(f"File not found: {e}")
except Exception as e:
    st.error(f"An error occurred: {e}")

