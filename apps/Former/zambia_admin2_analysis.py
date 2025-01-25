import os
import sys
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
from scipy.stats import gamma, kstest
import plotly.express as px

# Ensure the script starts in the main project directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
os.chdir(project_root)  # Change to the project root directory

# Add project root and utils folder to sys.path for imports
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "utils"))

from utils.app_utils.rainfall_eda import (
    load_data,
    interactive_precip_histogram,
    perform_ks_test_table_with_pvalues,
    map_ks_test_results,
    create_interactive_qq_plot,
)
from utils.app_utils.drought_analysis import (
    calculate_spi_for_regions,
    plot_spi,
    characterize_drought_events,
    prepare_drought_event_frequency_data,
    create_drought_event_frequency_map,
    prepare_drought_characteristics_data,
    create_drought_characteristics_map,
    plot_drought_characteristics
)

# Streamlit App
st.title("Precipitation Analysis")

# File paths for the data
rain_data_path = "data/zambia_admin2_rs_precip.csv"
boundaries_path = "data/zambia_admin2_boundaries.geojson"

# Load Data
try:
    zambia_rain_gdf = load_data(rain_data_path, boundaries_path)
except FileNotFoundError as e:
    st.error(f"Required files not found: {e}")
    st.stop()

# Calculate SPI results for Tab 2
spi_results_df = calculate_spi_for_regions(zambia_rain_gdf)

# Tabs for analysis
tab1, tab2 = st.tabs(["Rainfall Analysis", "Drought Analysis"])

# Tab 1: Rainfall Analysis
with tab1:
    st.header("Rainfall Analysis")

    # Sidebar Dropdown for Main Analysis Type
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type for Rainfall Analysis",
        ["Precipitation Histogram", "Kolmogorov-Smirnov Test Results"]
    )

    if analysis_type == "Precipitation Histogram":
        st.subheader("Precipitation Histogram")
        fig = interactive_precip_histogram(
            zambia_rain_gdf, group_column="admin2_name", value_column="precipitation"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif analysis_type == "Kolmogorov-Smirnov Test Results":
        st.subheader("Kolmogorov-Smirnov Test Results")

        # Add a checkbox to toggle the visibility of the table
        show_table = st.checkbox("Show KS Test Table", value=False)

        if show_table:
            st.write("### KS Test Table")
            results, fig = perform_ks_test_table_with_pvalues(zambia_rain_gdf)
            st.plotly_chart(fig, use_container_width=True)
            total_zones = results["passing"] + results["failing"]
            failed_percentage = (results["failing"] / total_zones) * 100
            st.write(f"Percentage of Administrative Zones That Failed the Test: {failed_percentage:.2f}%")
        else:
            st.write("KS Test Table is hidden. Check the box above to display it.")

        # Analysis Text
        st.write("""
        Approximately 19% of the administrative zones in Zambia did not pass the Kolmogorov-Smirnov Test, indicating that their rainfall patterns during the rain season do not closely follow a gamma distribution. Many of these zones exhibit rainfall distributions resembling a normal distribution.

        This normal-like distribution suggests relatively consistent and predictable rainfall, with values concentrated near a central peak and minimal extreme variations. Such stability indicates that these regions may be less affected by droughts, as the reliable distribution ensures sufficient precipitation during the rain season.
        """)

        # KS Test Map
        st.write("### KS Test Results Map")
        st.write("""
        This map visualizes the results of the Kolmogorov-Smirnov (KS) Test applied to administrative zones in Zambia, providing a geo-spatial perspective on how well each zone's rainfall distribution aligns with a gamma distribution. The zones are color-coded, with green representing zones that passed the test and red indicating zones that failed.

        By mapping these results, the visualization enables a clear spatial understanding of where rainfall patterns conform to or deviate from the gamma distribution.
        """)

        # Generate Map
        passing_failing = []
        for admin2_name in zambia_rain_gdf['admin2_name'].unique():
            data = zambia_rain_gdf[zambia_rain_gdf['admin2_name'] == admin2_name]['precipitation'].dropna()
            if len(data) < 2:
                continue
            shape, loc, scale = gamma.fit(data, floc=0)
            _, p_value = kstest(data, gamma(shape, loc, scale).cdf)
            status = "Passed" if p_value > 0.05 else "Failed"
            row = zambia_rain_gdf[zambia_rain_gdf['admin2_name'] == admin2_name].iloc[0]
            passing_failing.append({
                "admin2_name": row["admin2_name"],
                "p_value": p_value,
                "status": status,
                "geometry": row["geometry"]
            })
        results_gdf = gpd.GeoDataFrame(passing_failing)
        map_object = map_ks_test_results(results_gdf)
        st_folium(map_object, width=800, height=600)

        # Add Map Analysis Below Map
        st.write("""
        The regions that did not pass the Kolmogorov-Smirnov Test are located in the northeastern part of Zambia. As noted in the analysis above, these regions exhibit normally distributed rainfall, suggesting they may have been less impacted by droughts.
        """)

        # QQ Plot
        st.write("### QQ Plot for Gamma Fit")
        st.write("""
        Another tool for understanding the distribution is the QQ-Plot. QQ-Plots are used to visualize how well a dataset aligns with a theoretical distribution, such as the gamma distribution in this case. They plot the observed data against the theoretical quantiles, with the red line representing a perfect fit. Deviations from this line highlight areas where the observed data diverges from the expected distribution, offering additional insights into the nature of the data.
        """)

        # Dropdown for region selection
        selected_region = st.selectbox(
            "Select a region to visualize the QQ plot:",
            zambia_rain_gdf['admin2_name'].unique(),
            key="qq_plot_region"
        )

        # Render QQ Plot
        qq_plot_fig = create_interactive_qq_plot(
            zambia_rain_gdf[zambia_rain_gdf['admin2_name'] == selected_region]
        )
        st.plotly_chart(qq_plot_fig, use_container_width=True)
        
        
# Tab 2: Drought Analysis
with tab2:
    st.header("Drought Analysis")

    # Sidebar Dropdown for Main Analysis Type
    drought_analysis_type = st.sidebar.selectbox(
        "Select Analysis Type for Drought Analysis",
        [
            "SPI Analysis",
            "Drought Event Frequency Analysis",
            "Drought Characteristics Analysis",
            "Drought Characteristics Map"
        ]
    )

    if drought_analysis_type == "SPI Analysis":
        st.subheader("SPI Analysis")
        spi_analysis_region = st.selectbox(
            "Select Region for SPI Analysis",
            options=spi_results_df['admin2_name'].unique(),
            index=0,
            key="spi_analysis_region_dropdown"
        )
        spi_analysis_scale = st.selectbox(
            "Select SPI Scale for SPI Analysis",
            options=spi_results_df['spi_scale'].unique(),
            index=0,
            key="spi_analysis_scale_dropdown"
        )
        try:
            spi_fig = plot_spi(spi_results_df, spi_analysis_region, spi_analysis_scale)
            st.plotly_chart(spi_fig, use_container_width=True)
        except ValueError as e:
            st.error(f"Error in SPI Analysis: {e}")

    elif drought_analysis_type == "Drought Event Frequency Analysis":
        st.subheader("Drought Event Frequency Analysis")

        # Ensure drought_events_df is available
        try:
            drought_events_df = characterize_drought_events(spi_results_df)
        except Exception as e:
            st.error(f"Error characterizing drought events: {e}")
            drought_events_df = pd.DataFrame()  # Create an empty DataFrame as fallback

        if not drought_events_df.empty:
            # Dropdown for SPI scale selection
            drought_event_spi_scale = st.selectbox(
                "Select SPI Scale for Drought Event Frequency Analysis",
                options=drought_events_df['spi_scale'].unique(),
                index=0,
                key="drought_event_scale_dropdown"
            )

            # Define a cached function for data preparation
            @st.cache_data
            def cached_prepare_drought_event_frequency_data(_boundaries_gdf, drought_events_df, selected_spi_scale):
                from utils.app_utils.drought_analysis import prepare_drought_event_frequency_data
                return prepare_drought_event_frequency_data(_boundaries_gdf, drought_events_df, selected_spi_scale)

            # Use cached function to prepare data
            try:
                drought_events_gdf = cached_prepare_drought_event_frequency_data(
                    zambia_rain_gdf, drought_events_df, drought_event_spi_scale
                )
            except ValueError as e:
                st.error(f"Error in preparation: {e}")
                drought_events_gdf = None

            if drought_events_gdf is not None:
                # Generate and display the map
                try:
                    drought_map = create_drought_event_frequency_map(
                        drought_events_gdf, drought_event_spi_scale
                    )
                    st_folium(drought_map, width=800, height=600)
                except ValueError as e:
                    st.error(f"Error in Drought Event Frequency Map: {e}")
        else:
            st.info("No drought events data available for the selected SPI scale.")

    elif drought_analysis_type == "Drought Characteristics Analysis":
        st.subheader("Drought Characteristics Analysis")
        
        # Ensure drought_events_df is available
        try:
            drought_events_df = characterize_drought_events(spi_results_df)
        except Exception as e:
            st.error(f"Error characterizing drought events: {e}")
            st.stop()

        # Dropdowns for user selection
        spi_scales = sorted(drought_events_df['spi_scale'].unique().tolist())
        selected_spi_scale = st.selectbox(
            "Select SPI Scale",
            options=spi_scales,
            index=0,
            key="characteristics_spi_scale"
        )
        
        characteristic_options = ['Drought Intensity', 'Drought Severity', 'Drought Duration (months)']
        selected_characteristic = st.selectbox(
            "Select Characteristic",
            options=characteristic_options,
            index=0,
            key="characteristics_dropdown"
        )

        # Generate and display the plot
        try:
            fig = plot_drought_characteristics(drought_events_df, selected_spi_scale, selected_characteristic)
            st.plotly_chart(fig, use_container_width=True)
        except ValueError as e:
            st.error(f"Error in Drought Characteristics Analysis: {e}")

    elif drought_analysis_type == "Drought Characteristics Map":
        st.subheader("Drought Characteristics Map")
        
        # Ensure drought_events_df is available
        try:
            drought_events_df = characterize_drought_events(spi_results_df)
        except Exception as e:
            st.error(f"Error characterizing drought events: {e}")
            st.stop()

        # Merge drought_events_df with zambia_rain_gdf to include geometry
        drought_events_gdf = zambia_rain_gdf[['admin2_name', 'geometry']].merge(
            drought_events_df, on='admin2_name', how='right'
        )

        # Dropdowns for user selection
        spi_scales = sorted(drought_events_gdf['spi_scale'].unique().tolist())
        selected_spi_scale = st.selectbox(
            "Select SPI Scale for Map",
            options=spi_scales,
            index=0,
            key="map_spi_scale"
        )
        
        characteristic_options = ['Drought Intensity', 'Drought Severity', 'Drought Duration (months)']
        selected_characteristic = st.selectbox(
            "Select Characteristic for Map",
            options=characteristic_options,
            index=0,
            key="map_characteristics_dropdown"
        )

        # Generate and display the map
        try:
            drought_map = create_drought_characteristics_map(
                drought_events_gdf,
                selected_spi_scale,
                selected_characteristic
            )
            st_folium(drought_map, width=800, height=600)
        except ValueError as e:
            st.error(f"Error in Drought Characteristics Map: {e}")
