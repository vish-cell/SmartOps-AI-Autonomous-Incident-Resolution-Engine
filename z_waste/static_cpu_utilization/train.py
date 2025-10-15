import os
import json
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

# Directory containing JSON files
json_dir = r"data\jsons\ec2_metrics"

# Combine all JSON files into a single DataFrame
all_data = []

for file in os.listdir(json_dir):
    if file.endswith(".json"):
        with open(os.path.join(json_dir, file), 'r') as f:
            data = json.load(f)
            for date, times in data.items():
                for time_str, metrics in times.items():
                    timestamp = f"{date} {time_str}"
                    all_data.append({
                        "timestamp": pd.to_datetime(timestamp),
                        "cpu_usage": metrics["cpu_usage"],
                        "memory_usage": metrics["memory_usage"],
                        "disk_usage": metrics["disk_usage"]
                    })

# Convert to DataFrame
df = pd.DataFrame(all_data)
df.sort_values('timestamp', inplace=True)
df.set_index('timestamp', inplace=True)

# Features for anomaly detection
features = df[['cpu_usage', 'memory_usage', 'disk_usage']]

# Train Isolation Forest
model = IsolationForest(contamination=0.05, random_state=42)
df['anomaly'] = model.fit_predict(features)

# -1 means anomaly, 1 means normal
anomalies = df[df['anomaly'] == -1]

# Plot CPU usage with anomalies
plt.figure(figsize=(12,6))
plt.plot(df.index, df['cpu_usage'], label='CPU Usage')
plt.scatter(anomalies.index, anomalies['cpu_usage'], color='red', label='Anomalies')
plt.xlabel('Timestamp')
plt.ylabel('CPU Usage')
plt.title('EC2 CPU Usage with Anomalies')
plt.legend()
plt.show()

print(f"Found {len(anomalies)} anomalies")
