"""
PLEASE READ BEFORE RUNNING
Create dataset as a one-time artifact (or versioned occasionally)

Choose a save method; "SAVE_MODE":
1. Local
2. Google Cloud Storage (GCS)

Both will save the following artifacts:
1. Images per class; "PER_CLASS"
2. Labels; "DISHES", image path, and actual portion size in a tabular CSV file
3. Metadata of the dataset, in a JSON file
"""

import os
import io
import pandas as pd
import json
import requests
from PIL import Image
from datetime import datetime, timezone
from datasets import load_dataset
from google.cloud import storage
from tqdm import tqdm

from dine.params import *

def save_local(img, label, filename):
    save_path = os.path.join(
        BASE_DATA_DIR,
        DATASET_VERSION,
        "images",
        label,
        filename
    )

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    img.save(save_path, format="JPEG", quality=90)

    return f"{DATASET_VERSION}/images/{label}/{filename}"


def save_gcs(img, label, filename, bucket):
    blob_path = f"{DATASET_VERSION}/images/{label}/{filename}"

    buffer = io.BytesIO()

    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    blob = bucket.blob(blob_path)
    blob.upload_from_file(buffer, content_type="image/jpeg")

    return f"gs://{bucket.name}/{blob_path}"


def create_dataset(save_mode="local"):
    dataset = load_dataset(
        "Codatta/MM-Food-100K",
        split="train"
    )

    labels_rows = []

    bucket = None
    if save_mode == "gcs":
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)

    session = requests.Session() # Session reuse

    total_images = 0
    dish_subsets = {}

    for dish in DISHES:
        dish_data = dataset.filter(
            lambda x: isinstance(x["dish_name"], str)
            and x["dish_name"].lower() == dish.lower()
        )

        dish_data = dish_data.shuffle(seed=42).select(
            range(min(PER_CLASS, len(dish_data)))
        )

        dish_subsets[dish] = dish_data
        total_images += len(dish_data)

    print(f"\nTotal images to process: {total_images}\n")

    with tqdm(total=total_images, desc="Creating dataset") as pbar:

        for dish, dish_data in dish_subsets.items():

            label = dish.lower().replace(" ", "_")

            for i, row in enumerate(dish_data):
                filename = f"{i:06d}.jpg"

                try:
                    url = row.get("image_url")
                    if not isinstance(url, str):
                        pbar.update(1)
                        continue

                    response = session.get(url, timeout=15)
                    response.raise_for_status()

                    img = Image.open(io.BytesIO(response.content)).convert("RGB")

                    if save_mode == "local":
                        image_path = save_local(img, label, filename)
                    elif save_mode == "gcs":
                        image_path = save_gcs(img, label, filename, bucket)

                    portion_size = row.get("portion_size", None)
                    nutritional_profile = row.get("nutritional_profile", None)

                    labels_rows.append({
                        "image_path": image_path,
                        "label": label,
                        "portion_size": portion_size,
                        "nutritional_profile": nutritional_profile
                    })

                except Exception as e:
                    print("Failed:", e)

                finally:
                    pbar.update(1)

    session.close()

    return labels_rows


if __name__ == "__main__":

    # ---- Pre-check version existence ----
    if SAVE_MODE == "local":
        version_path = os.path.join(BASE_DATA_DIR, DATASET_VERSION)
        if os.path.exists(version_path):
            raise ValueError(f"Dataset version {DATASET_VERSION} already exists.")

    elif SAVE_MODE == "gcs":
        bucket = storage.Client().bucket(GCS_BUCKET_NAME)
        if bucket.blob(f"{DATASET_VERSION}/labels.csv").exists():
            raise ValueError(f"Dataset version {DATASET_VERSION} already exists in GCS.")

    # ---- Create dataset ----
    labels = create_dataset(save_mode=SAVE_MODE)
    labels_df = pd.DataFrame(labels)

    if labels_df.empty:
        raise ValueError("No samples were created. Check filtering or image downloads.")

    # ---- Metadata ----
    metadata = {
        "version": DATASET_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dishes": DISHES,
        "per_class": PER_CLASS,
        "total_samples": len(labels_df),
        "class_distribution": labels_df["label"].value_counts().to_dict(),
        "source_dataset": "Codatta/MM-Food-100K",
        "seed": 42  # Don't change
    }

    # ---- Save ----
    if SAVE_MODE == "local":
        os.makedirs(version_path, exist_ok=True)
        labels_df.to_csv(os.path.join(version_path, "labels.csv"), index=False)

        with open(os.path.join(version_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        print(f"✅ Local dataset created at {BASE_DATA_DIR}.")

    elif SAVE_MODE == "gcs":
        csv_buffer = io.StringIO()
        labels_df.to_csv(csv_buffer, index=False)

        bucket.blob(f"{DATASET_VERSION}/labels.csv").upload_from_string(
            csv_buffer.getvalue(),
            content_type="text/csv"
        )

        bucket.blob(f"{DATASET_VERSION}/metadata.json").upload_from_string(
            json.dumps(metadata, indent=4),
            content_type="application/json"
        )

        print(f"✅ Dataset uploaded to GCS at {GCS_BUCKET_NAME}.")
