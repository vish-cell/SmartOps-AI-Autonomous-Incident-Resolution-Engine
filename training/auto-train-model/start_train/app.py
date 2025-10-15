import os
import json
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib  # for saving model

# ====== PATHS ======
json_dir = r"AWS/ec2/"   #data\jsons\ec2_metrics
model_dir = r"models\anamoly"
anomaly_file = os.path.join(model_dir, "anomalies.json")
model_file = os.path.join(model_dir, "model.pkl")

# Create necessary folders if not exists
os.makedirs(model_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True) # Ensure the data input directory exists

# ====== LOAD ALL METRICS JSON FILES ======
all_data = []

# Check for files before proceeding
if not os.listdir(json_dir):
    print(f"Warning: Data directory {json_dir} is empty. No data loaded.")
else:
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

if df.empty:
    print("❌ Cannot proceed: No metric data found or loaded successfully.")
else:
    df.sort_values('timestamp', inplace=True)
    df.set_index('timestamp', inplace=True)

    # ====== TRAIN ISOLATION FOREST ======
    features = df[['cpu_usage', 'memory_usage', 'disk_usage']]
    model = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly'] = model.fit_predict(features)

    # ====== EXTRACT ANOMALY TIMESTAMPS ======
    anomalies = df[df['anomaly'] == -1]
    anomaly_timestamps = [str(ts) for ts in anomalies.index]

    print(f"✅ Found {len(anomaly_timestamps)} anomalies")

    # ====== SAVE MODEL ======
    joblib.dump(model, model_file)
    print(f"✅ Model saved to {model_file}")

    # ====== SAVE ANOMALY TIMESTAMPS ======
    with open(anomaly_file, 'w') as f:
        json.dump(anomaly_timestamps, f, indent=4)

    print(f"✅ Anomaly timestamps saved to {anomaly_file}")
    print("✅ PART 1 COMPLETE ✅")
