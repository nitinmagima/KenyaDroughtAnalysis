from sklearn.decomposition import PCA
import numpy as np
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

    return pca, cumulative_variance


def plot_cumulative_variance(cumulative_variance):
    """
    Plots the cumulative explained variance ratio against the number of components.

    Parameters:
    - cumulative_variance (list or np.ndarray): The cumulative explained variance ratio.
    """
    # Plot the cumulative explained variance ratio
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, marker='o', linestyle='-', color='b')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance')
    plt.title('Explained Variance vs. Number of Components')
    plt.grid(True)
    plt.show()


    
'''

Clustering Functions

'''


from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

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


def plot_elbow_method(wcss, cluster_range=range(1, 11)):
    """
    Plots the Elbow Method graph using precomputed WCSS values.

    Parameters:
    - wcss (list): A list of Within-Cluster Sum of Squares (WCSS) for each number of clusters.
    - cluster_range (range): The range of clusters tested.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(cluster_range, wcss, marker='o', linestyle='-', color='b')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Within-Cluster Sum of Squares (WCSS)')
    plt.title('Elbow Method to Determine Optimal Number of Clusters')
    plt.xticks(cluster_range)
    plt.grid(True)
    plt.show()

    
    
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors

def plot_all_geospatial_kmeans_clusters_with_legend(drought_gdf, title):
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





