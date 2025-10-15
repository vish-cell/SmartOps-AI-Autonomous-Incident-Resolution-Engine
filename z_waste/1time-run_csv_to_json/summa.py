import pandas as pd
import json
from datetime import datetime
import os
import numpy as np

# Load CSV
df = pd.read_csv(r"data\cpu_resource\system_performance_metrics.csv", parse_dates=['timestamp'])

# Create a new column with date only
df['date'] = df['timestamp'].dt.date

# Ensure target directory exists
output_dir = r"AWS\ec2"
os.makedirs(output_dir, exist_ok=True)

# Group by date
grouped = df.groupby('date')

# Function to process and save a data chunk
def save_metrics_to_json(data_chunk, date, suffix):
    """Processes a chunk of data and saves it to a JSON file."""
    day_metrics = {}
    for _, row in data_chunk.iterrows():
        time_str = row['timestamp'].strftime('%H:%M:%S')
        day_metrics[time_str] = {
            "cpu_usage": row['cpu_usage'],
            "memory_usage": row['memory_usage'],
            "disk_usage": row['disk_usage']
        }
    
    # JSON structure: { "2025-07-21": { "HH:MM:SS": {metrics} } }
    json_data = {str(date): day_metrics}
    
    # JSON filename with date and a suffix (e.g., _part1, _part2)
    filename = os.path.join(output_dir, f"metrics_{date}_{suffix}.json")
    
    # Save JSON
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=4)
    
    print(f"Saved {filename} with {len(day_metrics)} metrics")

# Iterate through each day and split data into two parts
for date, group in grouped:
    # 1. Determine the split point (middle index)
    split_point = len(group) // 2
    
    # 2. Split the group into two parts
    # The data is split based on the order of timestamps (which is the natural order in the group)
    part1 = group.iloc[:split_point]
    part2 = group.iloc[split_point:]
    
    # 3. Save the first part (Part 1)
    save_metrics_to_json(part1, date, 'part1')
    
    # 4. Save the second part (Part 2)
    save_metrics_to_json(part2, date, 'part2')