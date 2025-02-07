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
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Clustering Visualization", "Drought Characteristics", "Drought Heatmaps"])

# Tab 1: Introduction to the Project
with tab1:
    st.header("Introduction to Weather-Indexed Insurance and Zonal Risk")

    # Introductory text with citation link
    st.markdown(
        """
        Weather-indexed insurance provides payouts based on external indices, such as rainfall levels, rather than actual crop losses, 
        making it a valuable tool for smallholder farmers in developing countries. However, it introduces **basis risk**, particularly 
        **zonal risk**, where farmers in drier sub-regions may receive inadequate coverage due to uniform payouts within an insurance zone. 
        Building on **[Lobel and Stigler et al. (2021)](https://www.research-collection.ethz.ch/bitstream/handle/20.500.11850/592677/Optimal_index_insurance_and_basis_risk_decompositi.pdf?sequence=1&isAllowed=y)**, 
        our work focuses on **reducing this risk** by applying **unsupervised machine learning** to identify clusters with 
        **minimal rainfall heterogeneity**, especially during **droughts**. By refining insurance zones based on rainfall patterns, 
        we aim to enhance the **effectiveness of weather-indexed insurance** and improve coverage for **smallholder farmers**.
        """
    )

    # Methodology Section
    st.markdown("### **Methodology**")

    st.markdown(
        """
        - **Data Preprocessing**  
            - Encode categorical features and normalize numerical metrics using **MinMaxScaler**.  
        
        - **Dimensionality Reduction Using PCA**  
            - Determine the optimal number of components for dimensionality reduction by **analyzing cumulative explained variance**.  
            - Apply **Principal Component Analysis (PCA)** accordingly.  
        
        - **Clustering Analysis**  
            - **K-Means Clustering**  
                - Determine the optimal number of clusters using the **Elbow Method**.  
                - Apply **K-Means clustering** and **visualize clusters geospatially**.  
            - **Hierarchical Clustering**  
                - Create a **linkage matrix** using **Ward’s method** and determine the **optimal clusters using a dendrogram**.  
                - Assign **cluster labels** and **visualize clusters geospatially**.  
        """
    )

    # Load the necessary GeoDataFrames and DataFrames (but do not display them)
    try:
        zambia_clustering_gdf = gpd.read_file(zambia_clustering_path)
        spi1_averages_gdf = gpd.read_file(spi1_averages_path)
        spi3_averages_gdf = gpd.read_file(spi3_averages_path)
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        st.stop()
d
        
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
        two Standardized Precipitation Index (SPI) scales: **SPI 1** (1-month scale) and **SPI 3** (3-month scale). 
        The maps depict three key drought metrics:  
        - **Average Drought Duration** (months)  
        - **Average Drought Severity** (precipitation deficit)  
        - **Average Drought Intensity** (sharpness of drought conditions)  

        **SPI 1** captures short-term drought dynamics, while **SPI 3** reflects relatively longer-term trends.

        Additionally, these visualizations incorporate overlays of cluster boundaries generated from **K-Means** and 
        **Hierarchical Clustering** methods. These boundaries highlight distinct spatial groupings based on the 
        drought characteristics, providing an insightful context to evaluate patterns and trends within each cluster.  
        The **blue lines** delineate these clusters, allowing for a clearer interpretation of regional drought dynamics 
        in relation to the clustering models.
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

    # Add K-Means Clustering Summary Bullet Points
    st.markdown("##### Key Findings: K-Means Clustering")
    st.markdown(
        """
        - **SPI1 Scale**  
          - **Drought Duration:** Clusters **3 and 4** had **no variation**; others had **minimal variability**, indicating **stable drought lengths**.  
          - **Drought Severity:** **Cluster 0** had the **least** variation; **Clusters 1 and 2** had the **most**, but differences were **small overall**.  
          - **Drought Intensity:** Minimal variation; **Clusters 1 and 2** were the **most uniform**.  

        - **SPI3 Scale**  
          - **Drought Duration:** Slightly **more variation** than SPI1 due to **longer accumulation**. **Cluster 1** had the **highest variation**.  
          - **Drought Severity:** **Higher variability** than SPI1; **Cluster 0** had the **least**, **Clusters 3 and 4** had the **most**.  
          - **Drought Intensity:** **Minimal variation** within each cluster.  
        """
    )

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

    # Add Hierarchical Clustering Summary Bullet Points
    st.markdown("##### Key Findings: Hierarchical Clustering")
    st.markdown(
        """
        - **SPI1 Scale**  
          - **Drought Duration:** **Minimal variance**; **Cluster 4** had **no variation** (all droughts lasted exactly **1 month**).  
          - **Drought Severity:** **Slightly more variation** than K-Means due to **larger land area**, but still **minimal within clusters**.  
          - **Drought Intensity:** **Minimal variation**, similar to K-Means. **Cluster 2** had the **smallest variation** while covering the **largest land area**.  

        - **SPI3 Scale**  
          - **Drought Duration:** **Minimal variance despite increased variability at SPI3**. **Drought patterns remain stable** across administrative zones within clusters.  
          - **Drought Severity:** **More uniform variability** than K-Means; **higher but more consistent variances** due to **larger administrative zones**.  
          - **Drought Intensity:** **Negligible changes from SPI1**; intensity remains **almost uniform within clusters**.  
        """
    )

        
# Tab for Drought Percentage Plots
with tab4:
    st.header("Drought Percentages by Clusters")

    # Add intro text below the title
    st.markdown(
        """
        These heatmaps show the **percentage of administrative zones** within each cluster experiencing drought over time, 
        based on **K-Means and Hierarchical Clustering**. The visualizations compare **drought frequency** across 
        **SPI1 (short-term)** and **SPI3 (longer-term)** scales, highlighting **temporal patterns within each clustering method**.
        """
    )

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

    # Add Summary Notes Below the Plots
    st.markdown(
        """
        ### **Key Findings**
        
        - **SPI1 vs. SPI3 Differences:**  
          - SPI1 exhibits **higher frequency and more noise**, whereas SPI3 captures **longer-lasting droughts** for both K-Means and Hierarchical Clusters.  

        - **Drought Synchronization Across Clusters:**  
          - Droughts are **relatively synchronous**, which aligns with Zambia’s **homogeneous climate**.  
          - However, there are **isolated cases** where only **one or two clusters** experience high drought percentages:  
            - **K-Means Clusters 3 & 4 (SPI3)**, Nov 2016 – Feb 2017  
            - **Hierarchical Clusters 2 & 4 (SPI3)**, December 2008  
          - These cases are minimal, and **most droughts occur concurrently across clusters**.  

        - **SPI3 as a More Reliable Drought Indicator:**  
          - SPI3 reduces **random noise and short-term fluctuations**, making it a **better metric for short-term drought monitoring**.  
          - Since we are **interested in seasonal drought patterns**, SPI3 provides **more meaningful insights** into long-term drought behavior.  
        """
    )
