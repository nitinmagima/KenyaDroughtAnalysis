import matplotlib.pyplot as plt
from scipy.stats import gamma, probplot
from scipy.stats import kstest
import ipywidgets as widgets
from ipywidgets import Dropdown, interact


# Function to update the plot based on selected admin2_name
def update_plot(admin2_name, zambia_rain_df):
    """
    Plots a histogram of precipitation data for a selected Admin Level 2 region.

    Parameters:
    admin2_name (str): The name of the admin2 region.
    zambia_rain_df (pd.DataFrame): The DataFrame containing precipitation data.
    """
    # Filter the data for the selected admin2_name
    region_data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]

    # Set up the plot
    plt.figure(figsize=(8, 5))

    # Plot histogram for the selected region
    plt.hist(region_data['precipitation'], bins=20, color='skyblue', edgecolor='black')
    plt.title(f'{admin2_name} Rain Season')
    plt.xlabel('Precipitation')
    plt.ylabel('Frequency')

    # Show the plot
    plt.show()
    
    
def perform_ks_test(data, region_name):
    # Fit a gamma distribution to the data
    shape, loc, scale = gamma.fit(data, floc=0)  # floc=0 to ensure non-negative values

    # Perform Kolmogorov-Smirnov test
    test_stat, p_value = kstest(data, gamma(shape, loc, scale).cdf)

    # Print results for each region
    if p_value > 0.05:
        print(f"The data for {region_name} fits the gamma distribution well (p-value: {p_value:.4f}).")
    else:
        print(f"The gamma distribution may not be the best fit for {region_name} (p-value: {p_value:.4f}).")

        
        
def perform_ks_test_for_all(zambia_rain_df, pass_or_fail="pass"):
    """
    Perform Kolmogorov-Smirnov test for each admin2_name within Zambia.

    Parameters:
    zambia_rain_df (pd.DataFrame): The DataFrame containing precipitation data.
    pass_or_fail (str): Specify whether to print areas that pass or fail the test ('pass' or 'fail').

    Returns:
    None: Prints the names of admin2 areas that pass or fail the KS test.
    """
    # Initialize lists to hold the names of areas that pass or fail the test
    passing_admin2_names = []
    failing_admin2_names = []

    # Loop through each admin2_name in the dataset
    for admin2_name in zambia_rain_df['admin2_name'].unique():
        # Get the precipitation data for the current admin2_name
        data = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]['precipitation'].dropna()

        # Check if there is enough data to perform the test
        if len(data) < 2:
            continue

        # Fit a gamma distribution to the data
        shape, loc, scale = gamma.fit(data, floc=0)  # floc=0 to ensure non-negative values

        # Perform Kolmogorov-Smirnov test
        _, p_value = kstest(data, gamma(shape, loc, scale).cdf)

        # Determine if the admin2_name passes or fails based on the p-value
        if p_value > 0.05:
            passing_admin2_names.append(admin2_name)
        else:
            failing_admin2_names.append(admin2_name)

    # Print the results based on the pass_or_fail argument
    if pass_or_fail == "pass":
        if passing_admin2_names:
            print("Admin2 areas in Zambia that pass the KS test:")
            for name in passing_admin2_names:
                print(name)
        else:
            print("No admin2 areas in Zambia passed the KS test.")
    elif pass_or_fail == "fail":
        if failing_admin2_names:
            print("Admin2 areas in Zambia that fail the KS test:")
            for name in failing_admin2_names:
                print(name)
        else:
            print("No admin2 areas in Zambia failed the KS test.")
    else:
        print("Invalid argument for 'pass_or_fail'. Please use 'pass' or 'fail'.")


        
def interactive_qq_plot(admin2_name, zambia_rain_df):
    """
    Generates a QQ plot for the selected Admin Level 2 area using a gamma distribution.

    Parameters:
    admin2_name (str): The selected Admin 2 area.
    zambia_rain_df (pd.DataFrame): The DataFrame containing precipitation data.
    """
    # Filter the DataFrame based on the selected admin2_name
    filtered_df = zambia_rain_df[zambia_rain_df['admin2_name'] == admin2_name]

    if filtered_df.empty:
        print("No data available for the selected admin2_name.")
        return

    data = filtered_df['precipitation'].dropna()

    # Fit the gamma distribution to the data
    shape, loc, scale = gamma.fit(data, floc=0)

    # Generate QQ plot
    plt.figure(figsize=(8, 6))
    probplot(data, dist="gamma", sparams=(shape, loc, scale), plot=plt)
    plt.title(f"QQ Plot to Check Gamma Fit: {admin2_name}")
    plt.xlabel("Theoretical Quantiles")
    plt.ylabel("Ordered Values")
    plt.grid(True)
    plt.show()

    

def update_admin2_dropdown(zambia_rain_df, admin2_name_dropdown):
    """
    Updates the options in the Admin2 dropdown based on the dataset.

    Parameters:
    zambia_rain_df (pd.DataFrame): The DataFrame containing precipitation data.
    admin2_name_dropdown (Dropdown): The widget dropdown for Admin2 options.
    """
    admin2_options = zambia_rain_df['admin2_name'].unique()
    admin2_name_dropdown.options = admin2_options

        

def setup_interactive_widgets(zambia_rain_df):
    """
    Sets up and displays the interactive dropdown and QQ plot for the dataset.

    Parameters:
    zambia_rain_df (pd.DataFrame): The DataFrame containing precipitation data.
    """
    # Define the Admin2 dropdown widget
    admin2_name_dropdown = Dropdown(
        options=zambia_rain_df['admin2_name'].unique(),
        description='Select Admin2:',
        style={'description_width': 'initial'}
    )

    # Interactive QQ plot
    interact(
        lambda admin2_name: interactive_qq_plot(admin2_name, zambia_rain_df),
        admin2_name=admin2_name_dropdown
    )

    

    
    
    
    
    
    
    
    