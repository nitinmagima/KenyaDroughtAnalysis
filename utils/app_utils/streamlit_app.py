import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from scipy.stats import gamma, kstest
from streamlit_folium import st_folium
import folium

def interactive_precip_histogram(dataframe, group_column, value_column):
    unique_groups = sorted(dataframe[group_column].unique())
    fig = go.Figure()

    for i, group in enumerate(unique_groups):
        group_data = dataframe[dataframe[group_column] == group]
        fig.add_trace(
            go.Histogram(
                x=group_data[value_column],
                name=group,
                visible=(i == 0),
                marker=dict(color="rgba(135, 206, 250, 0.6)", line=dict(color="black", width=1.5)),
                hovertemplate=f"Range: %{{x}} mm<br>Count: %{{y}}<extra></extra>"
            )
        )

    buttons = []
    for i, group in enumerate(unique_groups):
        buttons.append(
            dict(
                label=group,
                method="update",
                args=[
                    {"visible": [j == i for j in range(len(unique_groups))]},
                    {"title": f"{group} Rain Season"}
                ]
            )
        )

    fig.update_layout(
        updatemenus=[dict(active=0, buttons=buttons)],
        title=f"Precipitation Histogram ({unique_groups[0]})",
        xaxis=dict(title="Precipitation (mm)", gridcolor="lightgrey"),
        yaxis=dict(title="Frequency", gridcolor="lightgrey"),
        barmode="overlay",
        plot_bgcolor="white"
    )
    return fig

def perform_ks_test_table_with_pvalues(zambia_rain_df):
    passing_admin2_names = []
    failing_admin2_names = []

    for admin2_name in zambia_rain_df['admin2_name'].unique():
        data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]['precipitation'].dropna()
        if len(data) < 2:
            continue
        shape, loc, scale = gamma.fit(data, floc=0)
        _, p_value = kstest(data, gamma(shape, loc, scale).cdf)
        formatted_name = f"{admin2_name} (p={p_value:.4f})"
        if p_value > 0.05:
            passing_admin2_names.append(formatted_name)
        else:
            failing_admin2_names.append(formatted_name)

    fig = go.Figure()
    fig.add_trace(
        go.Table(
            header=dict(values=["Passing Admin2 Areas"], align="left", font=dict(size=12, color="white"), fill_color="green"),
            cells=dict(values=[passing_admin2_names], align="left", font=dict(size=10), fill_color="lightgreen"),
            visible=True
        )
    )
    fig.add_trace(
        go.Table(
            header=dict(values=["Failing Admin2 Areas"], align="left", font=dict(size=12, color="white"), fill_color="red"),
            cells=dict(values=[failing_admin2_names], align="left", font=dict(size=10), fill_color="lightpink"),
            visible=False
        )
    )
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(label="Passing Areas", method="update", args=[{"visible": [True, False]}, {"title": "Passing"}]),
                    dict(label="Failing Areas", method="update", args=[{"visible": [False, True]}, {"title": "Failing"}])
                ],
                direction="down",
                showactive=True
            )
        ],
        title="Kolmogorov-Smirnov Test Results",
    )
    return {"passing": len(passing_admin2_names), "failing": len(failing_admin2_names)}, fig

def map_ks_test_results(results_gdf):
    m = folium.Map(location=[-13.1339, 27.8493], zoom_start=6)
    for _, row in results_gdf.iterrows():
        color = "green" if row["status"] == "Passed" else "red"
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(f"Name: {row['admin2_name']}<br>P-value: {row['p_value']:.4f}"),
        ).add_to(m)
    return m

# Streamlit App
st.title("Precipitation Analysis")

try:
    zambia_rain_df = pd.read_csv("../data/zambia_admin2_rs_precip.csv")
    admin_boundaries = gpd.read_file("../data/zambia_admin2_boundaries.geojson")

    admin_boundaries.rename(columns={"ADM2_NAME": "admin2_name"}, inplace=True)

    zambia_rain_df = gpd.GeoDataFrame(zambia_rain_df.merge(admin_boundaries, on="admin2_name"))

except FileNotFoundError:
    st.error("Required files not found.")
    st.stop()

analysis_type = st.sidebar.selectbox("Select Analysis Type", ["Precipitation Histogram", "Kolmogorov-Smirnov Test", "Map KS Test Results"])

if analysis_type == "Precipitation Histogram":
    st.subheader("Precipitation Histogram")
    fig = interactive_precip_histogram(dataframe=zambia_rain_df, group_column="admin2_name", value_column="precipitation")
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "Kolmogorov-Smirnov Test":
    st.subheader("Kolmogorov-Smirnov Test")
    results, fig = perform_ks_test_table_with_pvalues(zambia_rain_df)
    st.plotly_chart(fig, use_container_width=True)
    total_zones = results["passing"] + results["failing"]
    failed_percentage = (results["failing"] / total_zones) * 100
    st.write(f"**Percentage of Administrative Zones That Failed the Test:** {failed_percentage:.2f}%")

elif analysis_type == "Map KS Test Results":
    st.subheader("KS Test Results Map")
    passing_failing = []
    for admin2_name in zambia_rain_df['admin2_name'].unique():
        data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]['precipitation'].dropna()
        if len(data) < 2:
            continue
        shape, loc, scale = gamma.fit(data, floc=0)
        _, p_value = kstest(data, gamma(shape, loc, scale).cdf)
        status = "Passed" if p_value > 0.05 else "Failed"
        row = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name].iloc[0]
        passing_failing.append({
            "admin2_name": row["admin2_name"],
            "p_value": p_value,
            "status": status,
            "geometry": row["geometry"]
        })

    results_gdf = gpd.GeoDataFrame(passing_failing)
    map_object = map_ks_test_results(results_gdf)
    st_folium(map_object, width=800, height=600)
