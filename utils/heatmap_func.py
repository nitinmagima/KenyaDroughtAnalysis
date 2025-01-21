import os

def save_html_heatmap(html_content, folder_name, output_file_name):
    """
    Save an HTML string to a specified folder and file name.

    Parameters:
    - html_content (str): The HTML content to be saved.
    - folder_name (str): The name of the folder where the file will be saved.
    - output_file_name (str): The name of the output HTML file.

    Returns:
    - None: Saves the file in the specified folder.
    """
    os.makedirs(folder_name, exist_ok=True)
    output_file = os.path.join(folder_name, output_file_name)

    with open(output_file, "w") as f:
        f.write(html_content)

    print(f"Heatmap saved to {output_file}")
    
    

