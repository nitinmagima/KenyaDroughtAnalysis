from sklearn.decomposition import PCA
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


def compute_cumulative_variance(feature_vector):
    """
    Applies PCA to the given feature vector and computes the cumulative explained variance ratio.

    Parameters:
    - feature_vector (pd.DataFrame or np.ndarray): The feature matrix to apply PCA on.

    Returns:
    - pca: The fitted PCA object (to access components, variance, etc., later).
    - cumulative_variance: The cumulative explained variance ratio for each component.
    """
    # Apply PCA without specifying the number of components to capture all variance
    pca = PCA()
    pca.fit(feature_vector)

    # Calculate the cumulative explained variance ratio
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)

    return pca, np.round(cumulative_variance, 3)


def plot_cumulative_variance_plotly(cumulative_variance):
    """
    Creates an interactive Plotly line chart for the cumulative explained variance ratio.

    Parameters:
    - cumulative_variance (list or np.ndarray): The cumulative explained variance ratio.
    """
    # Create a line chart with Plotly
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(cumulative_variance) + 1)),
            y=cumulative_variance,
            mode='lines+markers',
            name='Cumulative Variance',
            marker=dict(color='blue', size=8),
            line=dict(color='blue', width=2),
            hovertemplate='<b>Components: %{x}</b><br>Cumulative Variance: %{y:.3f}<extra></extra>',
        )
    )

    # Add a horizontal red dashed line at Cumulative Explained Variance = 0.95
    fig.add_trace(
        go.Scatter(
            x=[0.5, len(cumulative_variance) + 1],
            y=[0.95, 0.95],
            mode='lines',
            name='95% Variance Threshold',
            line=dict(color='red', width=2, dash='dash'),
            hoverinfo='none',
        )
    )

    # Customize the layout
    fig.update_layout(
        title='Explained Variance vs. Number of Components',
        xaxis=dict(title='Number of Components', tickmode='linear', range=[0.5, len(cumulative_variance) + 1]),
        yaxis=dict(title='Cumulative Explained Variance', range=[0, 1.05]),
        template='plotly_white',
        height=600,
        width=800,
        margin=dict(t=50, b=50, l=50, r=50),
    )

    # Display the plot
    fig.show()

    
'''

Clustering Functions

'''


def compute_wcss(reduced_features, cluster_range=range(1, 11)):
    """
    Computes the Within-Cluster Sum of Squares (WCSS) for a range of clusters for K-Means.

    Parameters:
    - reduced_features (pd.DataFrame or np.ndarray): The feature matrix for clustering.
    - cluster_range (range, optional): The range of clusters to test. Default is range(1, 11).

    Returns:
    - wcss (list): A list of WCSS values for each number of clusters.
    """
    wcss = []
    for n_clusters in cluster_range:
        # Explicitly set n_init to avoid warnings
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(reduced_features)
        wcss.append(kmeans.inertia_)  # Inertia is the WCSS
    return wcss

def plot_elbow_method_interactive(wcss, cluster_range=range(1, 11)):
    """
    Creates an interactive Elbow Method plot using Plotly.

    Parameters:
    - wcss (list): A list of Within-Cluster Sum of Squares (WCSS) for each number of clusters.
    - cluster_range (range): The range of clusters tested.
    """
    # Create the elbow plot
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(cluster_range),
            y=wcss,
            mode='lines+markers',
            line=dict(color='blue'),
            marker=dict(size=8, color='blue'),
            name='WCSS'
        )
    )

    # Add a title and axis labels
    fig.update_layout(
        title=dict(
            text='Elbow Method to Determine Optimal Number of Clusters',
            x=0.5,
            font=dict(size=18)
        ),
        xaxis=dict(
            title='Number of Clusters',
            tickmode='linear',
            tick0=1,
            dtick=1,
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title='Within-Cluster Sum of Squares (WCSS)',
            showgrid=True,
            zeroline=False
        ),
        template='plotly_white',
        height=600,
        width=1000
    )

    # Show the interactive plot
    fig.show()
    
    
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors

def plot_all_geospatial_kmeans_clusters_with_legend(drought_gdf, title):
    
    ## TO DELETE!!!

    """
    Plots a static geospatial map showing all K-Means clusters with each cluster in a different color.
    Includes a legend to identify each cluster.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing the clustering results and geometry.
    - title (str): Title for the plot to describe the context (e.g., clustering parameters).
    """
    # Check if the cluster column exists in the GeoDataFrame
    if 'cluster' not in drought_gdf.columns:
        print(f"Error: The column 'cluster' does not exist in the GeoDataFrame.")
        return

    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot the entire GeoDataFrame with a default color (to show background regions)
    drought_gdf.plot(
        color='lightgrey',  # Default color for non-clustered regions
        linewidth=0.5,      # Line width for boundaries
        ax=ax,              # Axis to plot on
        edgecolor='black'   # Edge color
    )

    # Get unique clusters
    unique_clusters = drought_gdf['cluster'].unique()

    # Generate distinct colors using Tableau Colors (a set of distinct colors provided by matplotlib)
    distinct_colors = list(mcolors.TABLEAU_COLORS.values())
    if len(unique_clusters) > len(distinct_colors):
        # If there are more clusters than available distinct colors, repeat the color set
        distinct_colors = distinct_colors * (len(unique_clusters) // len(distinct_colors) + 1)

    # Create a list to hold legend entries
    legend_patches = []

    # Plot each cluster with a different color
    for idx, cluster_label in enumerate(unique_clusters):
        color = distinct_colors[idx]  # Get a distinct color for the current cluster
        drought_gdf[drought_gdf['cluster'] == cluster_label].plot(
            color=color,         # Color for the current cluster
            linewidth=0.8,       # Line width for boundaries
            ax=ax,               # Axis to plot on
            edgecolor='black'    # Edge color
        )
        # Add an entry to the legend
        legend_patches.append(mpatches.Patch(color=color, label=f'Cluster {cluster_label}'))

    # Add the legend to the plot
    plt.legend(handles=legend_patches, title="K-Means Clusters", loc='upper right', fontsize='small', title_fontsize='medium')

    # Customize the title and remove axis
    plt.title(f'K-Means Clusters by Administrative Unit Using Precipitation - {title}', fontsize=15)
    plt.axis('off')

    # Display the map
    plt.show()



import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.colors as mcolors
import pandas as pd

# Function to plot hierarchical clustering dendrogram
def plot_hierarchical_dendrogram(reduced_features, method='ward', truncate_mode='level', p=5, cut_off=None, title='Dendrogram for Hierarchical Clustering'):
    """
    Performs hierarchical clustering using the specified method and plots the dendrogram.

    Parameters:
    - reduced_features (pd.DataFrame or np.ndarray): The feature matrix for clustering.
    - method (str): The linkage method to use (default is 'ward').
    - truncate_mode (str): Truncation mode for the dendrogram (default is 'level').
    - p (int): The number of levels to show in the dendrogram (default is 5).
    - cut_off (float, optional): A y-axis value where a horizontal line is drawn (to visualize a potential cut-off).
    - title (str): The title for the dendrogram plot.

    Returns:
    - linkage_matrix: The linkage matrix produced by hierarchical clustering.
    """
    # Perform hierarchical clustering using the specified method
    linkage_matrix = linkage(reduced_features, method=method)

    # Plot the dendrogram
    plt.figure(figsize=(12, 8))
    dendrogram(linkage_matrix, truncate_mode=truncate_mode, p=p)
    plt.xlabel('Sample Index or Cluster Size')
    plt.ylabel('Distance')
    plt.title(title)

    # Optional cut-off line for determining clusters
    if cut_off is not None:
        plt.axhline(y=cut_off, color='r', linestyle='--')

    # Show the plot
    plt.show()

    return linkage_matrix


# Function to plot a geospatial map showing all Hierarchical Clusters with a legend
def plot_all_hierarchical_clusters_with_legend(drought_gdf, title):
    
    ## TO DELETE!!!
    
    """
    Plots a static geospatial map showing all Hierarchical Clusters with each cluster in a different color.
    Includes a legend to identify each cluster.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing hierarchical cluster assignments.
    - title (str): Title for the map plot.
    """
    # Check if the hierarchical_cluster column exists in the GeoDataFrame
    if 'hierarchical_cluster' not in drought_gdf.columns:
        print(f"Error: The column 'hierarchical_cluster' does not exist in the GeoDataFrame.")
        return

    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot the entire GeoDataFrame with a default color (to show background regions)
    drought_gdf.plot(
        color='lightgrey',     # Default color for all administrative units
        linewidth=0.5,         # Line width for boundaries
        ax=ax,                 # Axis to plot on
        edgecolor='black'      # Edge color
    )

    # Get unique clusters
    unique_clusters = drought_gdf['hierarchical_cluster'].unique()

    # Generate distinct colors using Tableau Colors (a set of distinct colors provided by matplotlib)
    distinct_colors = list(mcolors.TABLEAU_COLORS.values())
    if len(unique_clusters) > len(distinct_colors):
        # If there are more clusters than available distinct colors, repeat the color set
        distinct_colors = distinct_colors * (len(unique_clusters) // len(distinct_colors) + 1)

    # Create a list to hold legend entries
    legend_patches = []

    # Plot each cluster with a different color
    for idx, cluster_label in enumerate(unique_clusters):
        color = distinct_colors[idx]  # Get a distinct color for the current cluster
        drought_gdf[drought_gdf['hierarchical_cluster'] == cluster_label].plot(
            color=color,         # Color for the current cluster
            linewidth=0.8,       # Line width for boundaries
            ax=ax,               # Axis to plot on
            edgecolor='black'    # Edge color
        )
        # Add an entry to the legend
        legend_patches.append(mpatches.Patch(color=color, label=f'Cluster {cluster_label}'))

    # Add the legend to the plot
    plt.legend(handles=legend_patches, title="Hierarchical Clusters", loc='upper right', fontsize='small', title_fontsize='medium')

    # Customize the title and remove axis
    plt.title(f'Hierarchical Clusters by Administrative Unit - {title}', fontsize=15)
    plt.axis('off')

    # Display the map
    plt.show()



import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors

def plot_kmeans_and_hierarchical_clusters(drought_gdf, kmeans_title, hierarchical_title):
    """
    Plots geospatial maps for both K-Means and Hierarchical Clusters side by side.

    Parameters:
    - drought_gdf (GeoDataFrame): The GeoDataFrame containing clustering results and geometry.
    - kmeans_title (str): Title for the K-Means plot.
    - hierarchical_title (str): Title for the Hierarchical Clustering plot.
    """
    # Check if required columns exist in the GeoDataFrame
    if 'cluster' not in drought_gdf.columns:
        print("Error: The column 'cluster' does not exist in the GeoDataFrame for K-Means clustering.")
        return
    if 'hierarchical_cluster' not in drought_gdf.columns:
        print("Error: The column 'hierarchical_cluster' does not exist in the GeoDataFrame for Hierarchical clustering.")
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

    # Adjust layout and display the plots
    plt.tight_layout()
    plt.show()
    
    
    
import geopandas as gpd

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


