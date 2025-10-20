import json, os
import numpy as np
from sentence_transformers import SentenceTransformer, util

# === Load model ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Load error templates ===
with open("error_template/error.json") as f:
    templates = json.load(f)

template_texts = [f"{t['subcategory']} - {' '.join(t['examples'])}" for t in templates]
template_embeds = model.encode(template_texts, normalize_embeddings=True)

# === Load Lambda output ===
with open(r"AWS\Lambda\cpu_metrix-cloudwatch-fetch\hello-world\output\output.json") as f:
    data = json.load(f)

body = json.loads(data["body"])  # decode nested JSON string

results = []

# === Iterate all instances and logs ===
for instance_id, log_entries in body.items():
    for log in log_entries:
        log_text = log["msg"]
        log_embed = model.encode([log_text], normalize_embeddings=True)
        scores = util.cos_sim(log_embed, template_embeds)[0]
        best_idx = int(np.argmax(scores))
        best_template = templates[best_idx]
        confidence = float(scores[best_idx])

        results.append({
            "timestamp": log["timestamp"],
            "instance_id": instance_id,
            "log_msg": log["msg"],
            "matched_category": best_template["category"],
            "matched_subcategory": best_template["subcategory"],
            "confidence": round(confidence, 3),
            "recommended_actions": best_template["recommended_actions"],
            "priority": best_template["priority"],
            "auto_fix_possible": best_template["auto_fix_possible"],
            "trigger_ci_cd": best_template["trigger_ci_cd"]
        })

# === Group by instance ID ===
grouped = {}
for entry in results:
    grouped.setdefault(entry["instance_id"], []).append(entry)

# === Save structured output ===
os.makedirs("data/outputs", exist_ok=True)
with open("data/outputs/rca_decision_grouped.json", "w") as f:
    json.dump(grouped, f, indent=4)

print(f"✅ Processed {len(results)} logs across {len(grouped)} instances.")
print("✅ Output saved to data/outputs/rca_decision_grouped.json")
