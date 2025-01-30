# Drought Identification, Trend Analysis, and Clustering Across Zambia Administrative Units

------

## Project Overview

Weather-indexed insurance is an emerging tool designed to support smallholder farmers in developing countries. Unlike traditional crop insurance, which compensates farmers for actual crop losses, weather-indexed insurance provides payouts based on an external index, such as rainfall levels. If rainfall falls below a predetermined threshold, farmers receive compensation—regardless of their actual yield. While this model offers advantages, it also introduces *basis risk*: the risk that farmers may experience significant crop losses but receive no payout. This has contributed to the limited adoption of indexed insurance among smallholder farmers.  

Building upon the work of [Lobel and Stigler et al. (2021)](https://www.research-collection.ethz.ch/bitstream/handle/20.500.11850/592677/Optimal_index_insurance_and_basis_risk_decompositi.pdf?sequence=1&amp;isAllowed=y), which examines different types of basis risk, our focus is on *zonal risk*—the risk arising from using the same index across an insurance zone when there is significant within-zone heterogeneity. Specifically, when payouts are determined by zone-average rainfall, farmers in drier sub-regions within the zone may receive insufficient coverage, exacerbating basis risk.  

Our contribution is the application of unsupervised machine learning to identify clusters with minimal rainfall heterogeneity, particularly during drought conditions. By refining insurance zones based on rainfall patterns, we aim to reduce zonal risk and improve the effectiveness of weather-indexed insurance for smallholder farmers.

The Jupyter Notebook builds on [ Mall, Pandey, Petropoulos, Singh, and Srivastava, (2021)
](https://www.mdpi.com/2071-1050/13/3/1042) to replicate their drought identification and trend analysis in Zambia using Google Earth Engine (GEE) for Python. After applying this analysis, we use clustering techniques to explore spatial patterns in drought conditions.

## Analysis Steps

----

### Step 1: Preprocessing 

Obtain long-term satellite-derived precipitation data using the CHIRPS dataset available in GEE. This data will be used to analyze drought conditions in Kenya.

- **Study Area Definition**: Define the study area using Zambia's geographical boundaries.
- **Extract Monthly Precipitation**: Extract monthly CHIRPS precipitation data for the study area to calculate Standardized Precipitation Index (SPI) at different time scales (e.g., SPI1, SPI3, SPI6, SPI12).
- **Clip to Region**: Clip the precipitation data to Zambia's boundaries to ensure that the analysis focuses solely on Zambia. This step has already been implemented using GEE.
- **Filter rainfall season(s)**:  Filter the precipitation data to include only Zambia's primary rainfall seasons, ensuring that the analysis emphasizes the periods most relevant for understanding precipitation patterns and their impact.


### Step 2: Rainfall and Drought Exploratory Data Analysis

- **Gamma Distribution Analysis**
    - **Kolmogorov-Smirnov Test**: Determines which rainfall patterns fit under the gamma distirbution
- **SPI Calculation**: 
    - Calculate SPI at different time scales (1-, 3-, 6-, and 12-month) for drought evaluation. Convert the CHIRPS precipitation data into SPI values by fitting a gamma distribution to each pixel's monthly time series.
- **Identify Drought Events**: Use run theory to identify drought events based on SPI values.
    - **Drought Duration**: Identify the number of months with SPI values below thresholds like -1.0 for moderate drought.
    - **Drought Severity**: Calculate the severity by summing all SPI values during the drought.
    - **Drought Intensity**: Calculate drought intensity as severity divided by duration.
- **Distribution Analysis**: 
    - Analyzes the distribution of key drought metrics—duration, severity, and intensity—by administrative zone for each SPI scale. 
- **Drought Event Frequencies**:
    - Histograms and interactive maps displaying drought event frequencies by administrative zone and SPI scale. 
- **Adiministrative Level Comparison**:
    - Box plots visualizing the distribution of drought characteristics across administrative regions, filtered by SPI scale. Enables comparison of central tendencies and variability for intensity, severity, and duration  
- **Correlation Analysis**
    - Scatter plot visualizing drought characteristic relationships across districts by SPI scale.
- **SPI Scale (1-month vs. 3-month) Analysis**
    - Plot comparing SPI 1 and SPI 3 drought metrics for the same administrative zones.
- **Average Drought Duration, Severity and Intensity**
    - Table and GeoPandas map displaying the average drought duration, severity, and intensity for SPI 1 and SPI 3 scales.
- **Trend Analysis**
    - **Mann-Kendall Test**: Implement the Mann-Kendall trend test to determine trends in SPI values at annual, seasonal, and monthly time scales.
    - **Sen’s Slope Estimator**: Apply Sen’s slope estimator to understand the magnitude of the detected trends.


### Step 3: Clustering Analysis 

This step aims to perform a comprehensive clustering analysis on rainfall across administrative units in Zambia, including data preprocessing, dimensionality reduction, and clustering.

#### Workflow Steps

- **Data Preprocessing**:
  - Encode categorical features, and normalize numerical metrics using `MinMaxScaler`.
- **Feature Engineering**:
  - Construct a feature vector (`feature_vector`) for clustering, including encoded categorical features and  normalized numerical metrics.
- **Dimensionality Reduction Using PCA**:
  - Determine the optimal number of components for dimensionality reduction by analyzing cumulative explained variance and applying PCA accordingly.
- **Clustering Analysis**:
  - **K-Means Clustering**:
    - Determine the optimal number of clusters using the **Elbow Method** and apply K-Means.
    - Visualize the clusters geospatially.
  - **Hierarchical Clustering**:
    - Create a linkage matrix using **Ward's method** and determine the optimal clusters using a dendrogram.
    - Assign cluster labels and visualize geospatially.


### Step 4:  Cluster Drought Exploration

- **Drought Event Frequecy Maps**: 
    - Maps of drought event frequency of SPI1 and SPI3 with K-Means and Hierarchical Cluster Boundaries. 
- **Average Drought Duration, Severity, and Intensity with Cluster Boundaries**: 
    - Table and GeoPandas map displaying the average drought duration, severity, and intensity for SPI 1 and SPI 3 scales with K-Means and Hierarchical Cluster Boundaries.
- **Temporal and Spatial Visualizations**
    - **Heatmaps for Drought Percentages**
        - Heatmaps visualizing the percentage of administrative zones in each cluster (K-Means or Hierarchical) experiencing droughts for SPI1 and SPI3 scales.
    - **Interactive Time Slider Maps for Drought Analysis**: 
        - Interactive time slider maps showing administrative zones experiencing drought in each rainfall season month.


----

## Dependencies 

These are the libraries and packages required for your Jupyter Notebook:

### Core Libraries
- `ee` (Google Earth Engine)
- `geemap`
- ![](https://img.shields.io/badge/numpy-informational?style=flat&logo=numpy&logoColor=white&color=003865)
- `pandas`
- `geopandas`
- `json`
- `time`
- `logging`
- `os`

### Visualization Libraries
- `matplotlib`
- `seaborn`
- `mpld3`
- `plotly`

### Statistical and Analysis Libraries
- `scipy`
- `pymannkendall`

### Machine Learning Libraries
- `sklearn` (scikit-learn)
- `scipy.cluster.hierarchy`

### Interactive Widgets
- `ipywidgets`

### Installation Instructions
To ensure all dependencies are installed, please run the following command:

```bash
pip install earthengine-api geemap numpy pandas geopandas matplotlib seaborn mpld3 plotly scipy pymannkendall scikit-learn ipywidgets
```

----

### Directory
```
├── .gitignore
├── README.md
├── apps
│   └── Zambia Drought Clustering.py
├── data
│   ├── app_data
│   │   ├── hierarchical_cluster_boundaries.geojson
│   │   ├── kmeans_cluster_boundaries.geojson
│   │   ├── perc_droughts_hc_spi1.csv
│   │   ├── perc_droughts_hc_spi3.csv
│   │   ├── perc_droughts_km_spi1.csv
│   │   ├── perc_droughts_km_spi3.csv
│   │   ├── spi1_averages.geojson
│   │   ├── spi3_averages.geojson
│   │   └── zambia_clustering.geojson
│   ├── clustering boundaries
│   │   ├── hierarchical_cluster_boundaries.geojson
│   │   └── kmeans_cluster_boundaries.geojson
│   ├── zambia_admin2_boundaries.geojson
│   └── zambia_admin2_rs_precip.csv
├── drought heatmaps
│   ├── spi_1_hc_map.html
│   ├── spi_1_km_map.html
│   ├── spi_3_hc_map.html
│   └── spi_3_km_map.html
├── utils
│   ├── app_utils
│   │   └── drought_maps.py
│   ├── data_preprocessing.py
│   ├── drought_analysis_funcs.py
│   ├── gamma_distribution_funcs.py
│   ├── heatmap_func.py
│   ├── spi_funcs.py
│   └── unsupervised_ml_funcs.py
├── zambiadrought_admin2.ipynb
└── zambiadrought_admin2_withgee.ipynb

```
