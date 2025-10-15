import os
import json
import glob
from datetime import datetime

# --- Configuration ---
SOURCE_DIR = r"data\jsons\cloudwatch"
TARGET_DIR = r"AWS\cloudwatch"
FILE_PATTERN = "cloudwatch_*.json"

# Ensure the target directory exists
os.makedirs(TARGET_DIR, exist_ok=True)

# Function to process, split, and save data
def process_and_split_json_file(file_path):
    """
    Loads a JSON file (list of objects), splits the list into two equal parts, 
    and saves them to two new JSON files in the target directory.
    """
    try:
        # 1. Load the data from the source JSON file
        with open(file_path, 'r') as f:
            data_list = json.load(f)
            
    except FileNotFoundError:
        print(f"Error: Source file not found: {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from file: {file_path}")
        return

    # Determine the split point
    total_records = len(data_list)
    split_point = total_records // 2
    
    # 2. Split the list into two equal or near-equal parts
    part1 = data_list[:split_point]
    part2 = data_list[split_point:]
    
    # Extract the base date from the filename (e.g., '2025-07-21')
    base_filename = os.path.basename(file_path)
    date_str = base_filename.replace("cloudwatch_", "").replace(".json", "")

    print(f"\nProcessing file: {base_filename} ({total_records} records)")
    
    # 3. Save Part 1
    filename_part1 = os.path.join(TARGET_DIR, f"cloudwatch_{date_str}_part1.json")
    with open(filename_part1, 'w') as f:
        json.dump(part1, f, indent=4)
    print(f"-> Saved {len(part1)} records to {filename_part1}")

    # 4. Save Part 2
    filename_part2 = os.path.join(TARGET_DIR, f"cloudwatch_{date_str}_part2.json")
    with open(filename_part2, 'w') as f:
        json.dump(part2, f, indent=4)
    print(f"-> Saved {len(part2)} records to {filename_part2}")

# --- Main execution ---
# Find all matching files in the source directory
search_path = os.path.join(SOURCE_DIR, FILE_PATTERN)
all_files = glob.glob(search_path)

if not all_files:
    print(f"No files found matching the pattern '{FILE_PATTERN}' in '{SOURCE_DIR}'.")
else:
    for file_path in all_files:
        process_and_split_json_file(file_path)