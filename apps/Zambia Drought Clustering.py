import os
import sys
import streamlit as st
import geopandas as gpd
import pandas as pd

# Ensure the script starts in the app_utils directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(os.path.dirname(current_dir), "utils", "app_utils")
os.chdir(project_root)  # Set working directory to app_utils

# Add app_utils to sys.path for imports
sys.path.append(project_root)

# Import the plotting functions
try:
    from drought_maps import (
        plot_kmeans_and_hierarchical_clusters,
        map_drought_characteristics,
        create_streamlit_heatmap,
    )
except Exception as e:
    st.error(f"Import Failed: {e}")
    st.stop()

# File paths for the GeoJSON and CSV files
zambia_clustering_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'zambia_clustering.geojson')
spi1_averages_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'spi1_averages.geojson')
spi3_averages_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'spi3_averages.geojson')
kmeans_boundaries_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'kmeans_cluster_boundaries.geojson')
hierarchical_boundaries_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'hierarchical_cluster_boundaries.geojson')
perc_droughts_km_spi1_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'perc_droughts_km_spi1.csv')
perc_droughts_km_spi3_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'perc_droughts_km_spi3.csv')
perc_droughts_hc_spi1_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'perc_droughts_hc_spi1.csv')
perc_droughts_hc_spi3_path = os.path.join(project_root, '..', '..', 'data', 'app_data', 'perc_droughts_hc_spi3.csv')

# Streamlit Title
st.title("Zambia Drought Clustering Visualization")

# Tabs for organizing content
tab1, tab2, tab3, tab4 = st.tabs(["Data Overview", "Clustering Visualization", "Drought Characteristics", "Drought Heatmaps"])

# Tab 1: Data Overview
with tab1:
    st.header("Data Overview")

    # Load the Zambia Clustering GeoJSON file
    try:
        zambia_clustering_gdf = gpd.read_file(zambia_clustering_path)
        st.success("Successfully loaded GeoDataFrame from the GeoJSON file!")
        st.write("GeoDataFrame preview:")
        st.write(zambia_clustering_gdf.head())
    except FileNotFoundError as e:
        st.error(f"GeoJSON file not found: {e}")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading the GeoDataFrame: {e}")
        st.stop()

    # Load SPI averages as GeoDataFrames
    try:
        spi1_averages_gdf = gpd.read_file(spi1_averages_path)
        spi3_averages_gdf = gpd.read_file(spi3_averages_path)
        st.success("Successfully loaded SPI averages GeoJSON files!")

        # Display SPI1 averages
        st.subheader("SPI1 Averages (GeoJSON)")
        st.write(spi1_averages_gdf.head())

        # Display SPI3 averages
        st.subheader("SPI3 Averages (GeoJSON)")
        st.write(spi3_averages_gdf.head())
    except FileNotFoundError as e:
        st.error(f"SPI averages GeoJSON files not found: {e}")
    except Exception as e:
        st.error(f"An error occurred while loading the SPI averages: {e}")

# Tab 2: Clustering Visualization
with tab2:
    st.header("K-Means and Hierarchical Clustering Visualization")

    # Call the plotting function
    try:
        plot_kmeans_and_hierarchical_clusters(
            drought_gdf=zambia_clustering_gdf,
            kmeans_title="Zambia Rainfall Clusters - K-Means",
            hierarchical_title="Zambia Rainfall Clusters - Hierarchical"
        )
    except Exception as e:
        st.error(f"An error occurred while plotting the clusters: {e}")

# Tab 3: Drought Characteristics Visualization
with tab3:
    st.header("Drought Characteristics Visualization")

    # Add the augmented description under the header
    st.markdown(
        """
        This visualization showcases geospatial maps of Zambia, illustrating average drought characteristics based on 
        two Standardized Precipitation Index (SPI) scales: SPI 1 (1-month scale) and SPI 3 (3-month scale). 
        The maps depict three key drought metrics: average duration (months), severity (precipitation deficit), 
        and intensity (sharpness of drought conditions). SPI 1 captures short-term drought dynamics, 
        while SPI 3 reflects relatively longer-term trends.

        Additionally, these visualizations incorporate overlays of cluster boundaries generated from 
        K-Means and Hierarchical clustering methods. These boundaries highlight distinct spatial groupings 
        based on the drought characteristics, providing an insightful context to evaluate patterns and 
        trends within each cluster. The blue lines delineate these clusters, allowing for a clearer 
        interpretation of regional drought dynamics in relation to the clustering models.
        """
    )

    # Sub-header for K-Means Clustering
    st.subheader("Drought Characteristics with K-Means Clusters")
    try:
        # Load K-Means cluster boundaries
        kmeans_cluster_boundaries_gdf = gpd.read_file(kmeans_boundaries_path)
        
        # Render K-Means map
        map_drought_characteristics(
            gdf1=spi1_averages_gdf,
            gdf2=spi3_averages_gdf,
            cluster_boundaries_df=kmeans_cluster_boundaries_gdf,
            cluster_type="K-Means"
        )
    except Exception as e:
        st.error(f"An error occurred while plotting K-Means clusters: {e}")

    # Sub-header for Hierarchical Clustering
    st.subheader("Drought Characteristics with Hierarchical Clusters")
    try:
        # Load Hierarchical cluster boundaries
        hierarchical_cluster_boundaries_gdf = gpd.read_file(hierarchical_boundaries_path)
        
        # Render Hierarchical map
        map_drought_characteristics(
            gdf1=spi1_averages_gdf,
            gdf2=spi3_averages_gdf,
            cluster_boundaries_df=hierarchical_cluster_boundaries_gdf,
            cluster_type="Hierarchical"
        )
    except Exception as e:
        st.error(f"An error occurred while plotting Hierarchical clusters: {e}")

# Tab for Drought Percentage Plots
with tab4:
    st.header("Drought Percentages by Clustering")

    # SPI1 Heatmaps
    col1, col2 = st.columns(2)

    with col1:
        df_km_spi1 = pd.read_csv(perc_droughts_km_spi1_path).drop(columns=['total_regions'], errors='ignore')
        fig_km_spi1 = create_streamlit_heatmap(
            df=df_km_spi1,
            title="K-Means Clusters (SPI1)",
            ylabel="K-Means Cluster",
            index_col="cluster"
        )
        st.pyplot(fig_km_spi1)

    with col2:
        df_hc_spi1 = pd.read_csv(perc_droughts_hc_spi1_path).drop(columns=['total_regions'], errors='ignore')
        fig_hc_spi1 = create_streamlit_heatmap(
            df=df_hc_spi1,
            title="Hierarchical Clusters (SPI1)",
            ylabel="Hierarchical Cluster",
            index_col="hierarchical_cluster"
        )
        st.pyplot(fig_hc_spi1)

    # SPI3 Heatmaps
    col3, col4 = st.columns(2)

    with col3:
        df_km_spi3 = pd.read_csv(perc_droughts_km_spi3_path).drop(columns=['total_regions'], errors='ignore')
        fig_km_spi3 = create_streamlit_heatmap(
            df=df_km_spi3,
            title="K-Means Clusters (SPI3)",
            ylabel="K-Means Cluster",
            index_col="cluster"
        )
        st.pyplot(fig_km_spi3)

    with col4:
        df_hc_spi3 = pd.read_csv(perc_droughts_hc_spi3_path).drop(columns=['total_regions'], errors='ignore')
        fig_hc_spi3 = create_streamlit_heatmap(
            df=df_hc_spi3,
            title="Hierarchical Clusters (SPI3)",
            ylabel="Hierarchical Cluster",
            index_col="hierarchical_cluster"
        )
        st.pyplot(fig_hc_spi3)
