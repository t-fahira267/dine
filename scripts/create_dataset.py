"""
PLEASE READ BEFORE RUNNING
Create dataset as a one-time artifact (or versioned occasionally)

Choose a save method (SAVE_MODE variable in params):
1. Local
2. Google Cloud Storage (GCS)

Both will save the following artifacts:
1. Images per class (PER_CLASS variable in params)
2. Labels (DISHES variable in params), and image path in a tabular CSV file
"""

import os
import io
import pandas as pd
import json
from datetime import datetime
from datasets import load_dataset
from google.cloud import storage

from params import *


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

    for dish in DISHES:
        print(f"\nProcessing {dish}...")

        dish_data = dataset.filter(
            lambda x: x["dish_name"].lower() == dish.lower()
        )

        dish_data = dish_data.shuffle(seed=42).select(
            range(min(PER_CLASS, len(dish_data)))
        )

        label = dish.lower().replace(" ", "_")

        for i, row in enumerate(dish_data):
            filename = f"{i:06d}.jpg"

            try:
                img = row["image"]

                if save_mode == "local":
                    image_path = save_local(img, label, filename)

                elif save_mode == "gcs":
                    image_path = save_gcs(img, label, filename, bucket)

                labels_rows.append({
                    "image_path": image_path,
                    "label": label
                })

            except Exception as e:
                print("Failed:", e)

    return labels_rows


if __name__ == "__main__":

    labels = create_dataset(save_mode=SAVE_MODE)
    labels_df = pd.DataFrame(labels)

    # Create metadata for reproducibility
    metadata = {
        "version": DATASET_VERSION,
        "created_at": datetime.now(datetime.timezone.utc).isoformat(),
        "dishes": DISHES,
        "per_class": PER_CLASS,
        "total_samples": len(labels_df),
        "class_distribution": labels_df["label"].value_counts().to_dict(),
        "source_dataset": "Codatta/MM-Food-100K",
        "seed": 42  # Don't change
    }

    if SAVE_MODE == "local":
        version_path = os.path.join(BASE_DATA_DIR, DATASET_VERSION)
        if os.path.exists(version_path):
            raise ValueError(f"Dataset version {DATASET_VERSION} already exists.")

        os.makedirs(os.path.join(BASE_DATA_DIR, DATASET_VERSION),exist_ok=True)

        labels_df.to_csv(
            os.path.join(BASE_DATA_DIR, DATASET_VERSION, "labels.csv"),
            index=False
        )

        # Save metadata json
        with open(os.path.join(BASE_DATA_DIR, DATASET_VERSION, "metadata.json"),"w") as f:
            json.dump(metadata, f, indent=4)

        print(f"✅ Local dataset created at {BASE_DATA_DIR}.")

    elif SAVE_MODE == "gcs":
        csv_buffer = io.StringIO()
        labels_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        bucket = storage.Client().bucket(GCS_BUCKET_NAME)
        if bucket.blob(f"{DATASET_VERSION}/labels.csv").exists():
            raise ValueError(f"Dataset version {DATASET_VERSION} already exists in GCS.")

        bucket.blob(f"{DATASET_VERSION}/labels.csv").upload_from_string(
            csv_buffer.getvalue(),
            content_type="text/csv"
        )

        # Save metadata json
        bucket.blob(f"{DATASET_VERSION}/metadata.json").upload_from_string(
            json.dumps(metadata, indent=4),
            content_type="application/json"
        )

        print(f"✅ Dataset uploaded to GCS at {GCS_BUCKET_NAME}.")
