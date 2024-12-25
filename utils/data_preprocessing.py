#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from sklearn.preprocessing import MinMaxScaler
import pandas as pd


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




