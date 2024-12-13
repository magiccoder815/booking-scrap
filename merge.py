import os
import pandas as pd

# Define the folder containing the Excel files and the output file name
input_folder = 'scraping'
output_file = 'Total_accommodations.xlsx'

# Initialize an empty list to hold the dataframes
all_dataframes = []

# Iterate over all files in the scraping folder
for file_name in os.listdir(input_folder):
    # Create the full file path
    file_path = os.path.join(input_folder, file_name)

    # Check if the file is an Excel file
    if file_name.endswith(('.xlsx', '.xls')):
        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file_path)
            
            # Append the DataFrame to the list
            all_dataframes.append(df)
        except Exception as e:
            print(f"Could not read {file_name}: {e}")

# Concatenate all the dataframes into one
if all_dataframes:
    merged_df = pd.concat(all_dataframes, ignore_index=True)

    # Save the merged DataFrame to a new Excel file outside the folder
    merged_df.to_excel(output_file, index=False)
    print(f"Merged file saved as {output_file}")
else:
    print("No Excel files found to merge.")
