# README: Drought Identification, Trend Analysis, and Clustering Across Kenyan Administrative Units

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nitinmagima/KenyaDroughtAnalysis/HEAD)

## Project Overview

This repository contains a set of scripts for analyzing drought conditions and trends in Kenya using Google Earth Engine (GEE) and clustering drought metrics to identify patterns across administrative units. The analysis is based on methods described in the [paper](https://www.mdpi.com/2071-1050/13/3/1042) and aims to replicate the findings for drought identification, trend analysis, and clustering at both the admin 1 and admin 2 levels. The repository contains four files:

### Files Overview

1. **kenyadrought_admin1_withgee.ipynb**: This Jupyter notebook performs the analysis at the admin 1 level by downloading the required data using Google Earth Engine (GEE).
2. **kenyadrought_admin2_withgee.ipynb**: This notebook performs the analysis at the admin 2 level, also using GEE to download the necessary data.
3. **kenyadrought_admin1.ipynb**: This notebook performs the analysis at the admin 1 level using pre-downloaded data from GEE.
4. **kenyadrought_admin2.ipynb**: This notebook performs the analysis at the admin 2 level using pre-downloaded data from GEE.
5. **kenya_admin2_droughtmetrics.csv**: Includes administrative information, drought metrics such as drought duration, severity, intensity, and other categorical features (e.g., region, season).
6. **kenya_admin1_precip.csv**: Pre-downloaded for admin 1 from GEE.
7. **kenya_admin2_precip.csv**: Pre-downloaded for admin 2 from GEE.
8. **public_emdat_custom_request_2024-10-01_36a9efba-9545-41bc-a272-3b49c638962b.xlsx**: EM-DAT data for Kenya.
9. **Geospatial Data**: Administrative boundaries are stored in a GeoDataFrame (admin_boundaries). We use the FAO GAUL: Global Administrative Unit Layers for the administrative boundaries.


## Analysis Steps

### Step 1: Data Collection

Obtain long-term satellite-derived precipitation data using the CHIRPS dataset available in GEE. This data will be used to analyze drought conditions in Kenya.

### Step 2: Study Area Definition

Define the study area using Kenya's geographical boundaries.

### Step 3: Data Preprocessing

- **Extract Monthly Precipitation**: Extract monthly CHIRPS precipitation data for the study area to calculate Standardized Precipitation Index (SPI) at different time scales (e.g., SPI1, SPI3).
- **Clip to Region**: Clip the precipitation data to Kenya's boundaries to ensure that the analysis focuses solely on Kenya. This step has can been implemented using GEE or the pre-downloaded datasets.

### Step 4: Calculate Standardized Precipitation Index (SPI)

- **SPI Calculation**: Calculate SPI at different time scales (1- or 3-month) for drought evaluation. Convert the CHIRPS precipitation data into SPI values by fitting a gamma distribution to each pixel's monthly time series.

### Step 5: Drought Characterization

- **Identify Drought Events**: Use run theory to identify drought events based on SPI values.
- **Drought Duration**: Identify the number of months with SPI values below thresholds like -1.0 for moderate drought.
- **Drought Severity**: Calculate the severity by summing all SPI values during the drought.
- **Drought Intensity**: Calculate drought intensity as severity divided by duration.

### Step 6: Trend Analysis

- **Mann-Kendall Test**: Implement the Mann-Kendall trend test to determine trends in SPI values at annual, seasonal, and monthly time scales.
- **Sen’s Slope Estimator**: Apply Sen’s slope estimator to understand the magnitude of the detected trends.

### Step 7: Clustering Analysis of Drought Metrics

This step aims to perform a comprehensive clustering analysis on drought metrics across administrative units in Kenya, including data preprocessing, dimensionality reduction, and clustering.

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
  - **DBSCAN Clustering**:
    - Perform a grid search to determine the best parameters (`eps`, `min_samples`) and use the **Silhouette Score** for optimization.
    - Assign cluster labels and visualize geospatially.

### Step 8: EM-DAT Analysis

Compare historical drought years from the [Emergency Events Database (EM-DAT)](https://www.emdat.be/) to SPI-derived results.

## Disclaimer

This is a set of scripts shared for educational purposes only. Anyone who uses this code, its functionality, or its structure assumes full liability and should credit the author.

## Map Disclaimer

The designations employed and the presentation of the material on this map do not imply the expression of any opinion whatsoever on the part of the author concerning the legal status of any country, territory, city, or area or of its authorities, or concerning the delimitation of its frontiers or boundaries.