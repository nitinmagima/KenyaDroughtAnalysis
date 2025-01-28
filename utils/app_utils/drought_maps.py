import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import streamlit as st
import geopandas as gpd


def plot_kmeans_and_hierarchical_clusters(drought_gdf, kmeans_title, hierarchical_title):
    """
    Plots geospatial maps for both K-Means and Hierarchical Clusters side by side in Streamlit.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing clustering results and geometry.
    - kmeans_title (str): Title for the K-Means plot.
    - hierarchical_title (str): Title for the Hierarchical Clustering plot.
    """
    # Check if required columns exist in the GeoDataFrame
    if 'cluster' not in drought_gdf.columns:
        st.error("The column 'cluster' does not exist in the GeoDataFrame for K-Means clustering.")
        return
    if 'hierarchical_cluster' not in drought_gdf.columns:
        st.error("The column 'hierarchical_cluster' does not exist in the GeoDataFrame for Hierarchical clustering.")
        return

    # Set up the figure with two side-by-side subplots
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # Plot K-Means clusters
    drought_gdf.plot(
        color='lightgrey', linewidth=0.5, ax=axes[0], edgecolor='black'
    )
    unique_kmeans_clusters = drought_gdf['cluster'].unique()
    kmeans_colors = list(mcolors.TABLEAU_COLORS.values()) * (len(unique_kmeans_clusters) // len(mcolors.TABLEAU_COLORS.values()) + 1)
    kmeans_patches = []
    for idx, cluster_label in enumerate(unique_kmeans_clusters):
        color = kmeans_colors[idx]
        drought_gdf[drought_gdf['cluster'] == cluster_label].plot(
            color=color, linewidth=0.8, ax=axes[0], edgecolor='black'
        )
        kmeans_patches.append(mpatches.Patch(color=color, label=f'Cluster {cluster_label}'))
    axes[0].legend(handles=kmeans_patches, title="K-Means Clusters", loc='upper left', fontsize='small', title_fontsize='medium')
    axes[0].set_title(f'K-Means Clusters - {kmeans_title}', fontsize=15)
    axes[0].axis('off')

    # Plot Hierarchical clusters
    drought_gdf.plot(
        color='lightgrey', linewidth=0.5, ax=axes[1], edgecolor='black'
    )
    unique_hierarchical_clusters = drought_gdf['hierarchical_cluster'].unique()
    hierarchical_colors = list(mcolors.TABLEAU_COLORS.values()) * (len(unique_hierarchical_clusters) // len(mcolors.TABLEAU_COLORS.values()) + 1)
    hierarchical_patches = []
    for idx, cluster_label in enumerate(unique_hierarchical_clusters):
        color = hierarchical_colors[idx]
        drought_gdf[drought_gdf['hierarchical_cluster'] == cluster_label].plot(
            color=color, linewidth=0.8, ax=axes[1], edgecolor='black'
        )
        hierarchical_patches.append(mpatches.Patch(color=color, label=f'Cluster {cluster_label}'))
    axes[1].legend(handles=hierarchical_patches, title="Hierarchical Clusters", loc='upper left', fontsize='small', title_fontsize='medium')
    axes[1].set_title(f'Hierarchical Clusters - {hierarchical_title}', fontsize=15)
    axes[1].axis('off')

    # Adjust layout
    plt.tight_layout()

    # Display in Streamlit
    st.pyplot(fig)
    

def map_drought_characteristics(
    gdf1,
    gdf2,
    cluster_boundaries_df=None,
    cluster_type=None,
):
    """
    Plots geospatial maps for drought characteristics averaged for each admin2 region 
    with consistent color scales, and displays them in Streamlit.

    Parameters:
    - gdf1 (GeoDataFrame): GeoDataFrame for SPI 1 averages by admin2.
    - gdf2 (GeoDataFrame): GeoDataFrame for SPI 3 averages by admin2.
    - cluster_boundaries_df (GeoDataFrame, optional): GeoDataFrame containing cluster boundaries.
    - cluster_type (str, optional): A string indicating the type of clustering (e.g., "K-Means", "Hierarchical").
      If None, the default title is used.

    Raises:
    - ValueError: If required inputs are missing.
    """
    # Validate inputs
    if gdf1 is None or gdf2 is None:
        st.error("gdf1 and gdf2 are required for plotting averages.")
        return

    # Define drought characteristics and their color scale limits
    drought_characteristics = [
        "Drought Duration (months)",
        "Drought Severity",
        "Drought Intensity",
        "Drought Duration (months)_admin2",
        "Drought Severity_admin2",
        "Drought Intensity_admin2",
    ]
    color_scale_limits = {
        "Drought Duration (months)": (0, 4),
        "Drought Severity": (-3, 0),
        "Drought Intensity": (0, 4),
        "Drought Duration (months)_admin2": (0, 4),
        "Drought Severity_admin2": (-3, 0),
        "Drought Intensity_admin2": (0, 4),
    }

    # Filter available characteristics
    available_characteristics = [
        char
        for char in drought_characteristics
        if char in gdf1.columns and char in gdf2.columns
    ]

    # Set up the figure
    fig, axes = plt.subplots(
        nrows=2, ncols=len(available_characteristics), figsize=(6 * len(available_characteristics), 10)
    )
    fig.subplots_adjust(hspace=0.4, wspace=0.3)  # Adjust spacing

    spi_dataframes = {1: gdf1, 3: gdf2}

    for i, (spi_scale, spi_gdf) in enumerate(spi_dataframes.items()):
        if not isinstance(spi_gdf, gpd.GeoDataFrame):
            st.error(f"SPI {spi_scale} input must be a GeoDataFrame.")
            return
        if "geometry" not in spi_gdf.columns:
            st.error(f"SPI {spi_scale} input is missing a 'geometry' column.")
            return

        for j, characteristic in enumerate(available_characteristics):
            ax = axes[i, j]

            # Get color scale limits
            vmin, vmax = color_scale_limits[characteristic]

            # Use the same colormap for Duration and Intensity, reversed for Severity
            cmap = "YlOrRd" if "Duration" in characteristic or "Intensity" in characteristic else "YlOrRd_r"

            # Plot the map
            spi_gdf.plot(
                column=characteristic,
                cmap=cmap,
                linewidth=0.8,
                ax=ax,
                edgecolor="black",
                legend=True,
                legend_kwds={"shrink": 0.6},
                vmin=vmin,
                vmax=vmax,
            )

            # Overlay cluster boundaries if provided
            if cluster_boundaries_df is not None:
                cluster_boundaries_df.plot(
                    ax=ax,
                    color="none",  # Transparent fill
                    edgecolor="blue",  # Blue border for averages
                    linewidth=1.5,  # Thicker lines for clarity
                )

            # Set individual plot title
            title = characteristic.replace("_admin2", "").replace("Drought ", "Average ")
            ax.set_title(f"{title} (SPI {spi_scale})", fontsize=12)
            ax.axis("off")

    # Remove the main figure title
    plt.suptitle("")  # No overarching subtitle

    # Use Streamlit to display the figure
    st.pyplot(fig)



def create_streamlit_heatmap(df, title, ylabel, index_col, vmax=100):
    """
    Create a heatmap for Streamlit with improved alignment and aesthetics.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing drought percentage data.
    - title (str): Title of the heatmap.
    - ylabel (str): Label for the y-axis.
    - index_col (str): The column to set as the index.
    - vmax (int): Maximum value for the color scale.

    Returns:
    - fig: Matplotlib figure object.
    """
    # Prepare the DataFrame
    if index_col in df.columns:
        df = df.set_index(index_col)
    else:
        raise KeyError(f"Index column '{index_col}' not found in DataFrame.")
    
    # Create the heatmap
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(
        df,
        ax=ax,
        cmap="YlOrRd",  # Light orange to red
        cbar_kws={'label': '% of Regions in Drought'},
        vmin=0,
        vmax=vmax,
        linewidths=0.5
    )
    
    # Customize labels and title
    ax.set_title(title, fontsize=14, pad=20)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlabel("Year-Month", fontsize=12)
    ax.tick_params(axis='x', labelrotation=90)
    ax.tick_params(axis='both', labelsize=10)  # Adjust label font size
    
    return fig


