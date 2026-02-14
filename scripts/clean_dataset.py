"""
Before run, Don't forget to check DEPLOYMENT in params.py

Converts the MM-Food-100K dataset into a clean CSV format for training.

Two columns:
1. image_path: Path to image file (if local) or GCS path (if GCP)
2. label: Label for image
"""

import os
import io
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm
from google.cloud import storage

from params import *
from download_subset import download_image


# =========================
# LOAD DATASET (streaming safe)
# =========================
print("Loading dataset...")
dataset = load_dataset("Codatta/MM-Food-100K", split="train")

labels_rows = []


# =========================
# LOCAL TRAINING
# =========================
if DEPLOYMENT == "local":

    for dish in DISHES:
        print(f"\nProcessing {dish}...")

        # Filter dataset
        dish_data = dataset.filter(
            lambda x: x["dish_name"].lower() == dish.lower()
        )

        # Shuffle and limit
        dish_data = dish_data.shuffle(seed=42).select(
            range(min(PER_CLASS, len(dish_data)))
        )

        label = dish.lower().replace(" ", "_")

        for i, row in enumerate(tqdm(dish_data)):
            filename = f"{i:06d}.jpg"
            save_path = os.path.join(OUTPUT_DIR, "images", label, filename)

            try:
                # Use your existing URL downloader
                download_image(row["image_url"], save_path)

                labels_rows.append({
                    "image_path": f"images/{label}/{filename}",
                    "label": label
                })

            except Exception as e:
                print("Failed:", e)

    # Save CSV locally
    labels_df = pd.DataFrame(labels_rows)
    labels_df.to_csv(os.path.join(OUTPUT_DIR, "labels.csv"), index=False)

    print("✅ Local dataset prepared.")
