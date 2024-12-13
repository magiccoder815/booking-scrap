import os
import pandas as pd
from datetime import datetime

# Define the folder containing the Excel files and the output file name
input_folder = 'scraping'
output_file = 'Total_accommodations.xlsx'

# Initialize an empty list to hold the dataframes along with file creation dates
file_data = []

# Function to validate phone numbers
def clean_phone_numbers(df, column_name):
    if column_name in df.columns:
        # Replace incomplete phone numbers (e.g., less than 10 digits) with "N/A"
        df[column_name] = df[column_name].apply(
            lambda x: "N/A" if pd.notna(x) and (not str(x).isdigit() or len(str(x)) < 10) else x
        )
    return df

# Iterate over all files in the scraping folder
for file_name in os.listdir(input_folder):
    # Create the full file path
    file_path = os.path.join(input_folder, file_name)

    # Check if the file is an Excel file
    if file_name.endswith(('.xlsx', '.xls')):
        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file_path)

            # Get the file creation or modification date
            if os.name == 'nt':  # Windows
                created_timestamp = os.path.getctime(file_path)
            else:  # Unix-based systems (fallback to modification time)
                created_timestamp = os.path.getmtime(file_path)

            # Convert timestamp to a datetime object
            created_date = datetime.fromtimestamp(created_timestamp)

            # Clean phone numbers if the column exists
            df = clean_phone_numbers(df, column_name="phone number")

            # Append the DataFrame and its creation date to the list
            file_data.append((created_date, df))

            # Debug: Print file name and creation date
            print(f"File: {file_name}, Created Date: {created_date}")
        except Exception as e:
            print(f"Could not read {file_name}: {e}")

# Sort the files by creation date
file_data.sort(key=lambda x: x[0])  # Ensure sorting by datetime

# Merge the dataframes in the order of file creation date
all_dataframes = [df for _, df in file_data]

# Concatenate all the dataframes into one
if all_dataframes:
    merged_df = pd.concat(all_dataframes, ignore_index=True)

    # Fill empty cells with "N/A"
    merged_df.fillna("N/A", inplace=True)

    # Save the merged DataFrame to a new Excel file outside the folder
    merged_df.to_excel(output_file, index=False)
    print(f"Merged file saved as {output_file}")
else:
    print("No Excel files found to merge.")
