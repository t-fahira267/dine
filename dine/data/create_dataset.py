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

Caching is also available
"""

import os
import io
import re
import pandas as pd
import json
import requests
from PIL import Image
from datetime import datetime, timezone
from datasets import load_dataset
from google.cloud import storage
from tqdm import tqdm

from dine.params import *

# --- Helper ---
def count_existing_images(label):
    dish_dir = os.path.join(
        BASE_DATA_DIR,
        DATASET_VERSION,
        "images",
        label
    )

    if not os.path.exists(dish_dir):
        return 0

    return len([
        f for f in os.listdir(dish_dir)
        if f.endswith(".jpg")
    ])

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

    labels_csv_path = os.path.join(
        BASE_DATA_DIR,
        DATASET_VERSION,
        "labels.csv"
    )

    metadata_path = os.path.join(
        BASE_DATA_DIR,
        DATASET_VERSION,
        "metadata.json"
    )

    labels_rows = []

    bucket = None
    if save_mode == "gcs":
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)

    session = requests.Session()

    total_images = 0
    dish_subsets = {}

    # -----------------------------------
    # Build subsets + compute total work
    # -----------------------------------
    total_target = 0
    total_cached = 0
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
        total_target += len(dish_data)

        label = dish.lower().replace(" ", "_")

        if save_mode == "local":
            existing = count_existing_images(label)
            total_cached += min(existing, len(dish_data))

        elif save_mode == "gcs":
            for i in range(len(dish_data)):
                filename = f"{i:06d}.jpg"
                blob_path = f"{DATASET_VERSION}/images/{label}/{filename}"
                blob = bucket.blob(blob_path)
                if blob.exists():
                    total_cached += 1

    total_to_download = total_target - total_cached

    print("\nDataset summary:")
    print(f"Total target images:      {total_target}")
    print(f"Already cached images:    {total_cached}")
    print(f"Images left to download:  {total_to_download}\n")

    with tqdm(total=total_to_download, desc="Downloading images") as pbar:

        for dish, dish_data in dish_subsets.items():

            label = dish.lower().replace(" ", "_")

            # -----------------------------------
            # PER-DISH RESUME CHECK
            # -----------------------------------
            if save_mode == "local":
                existing_count = count_existing_images(label)
                if existing_count >= PER_CLASS:
                    print(f"Skipping {dish} (already complete)")
                    pbar.update(len(dish_data))
                    continue

            for i, row in enumerate(dish_data):
                filename = f"{i:06d}.jpg"

                # Build image path first (for BOTH cached & new images)
                if save_mode == "local":
                    image_path = f"{DATASET_VERSION}/images/{label}/{filename}"
                    image_local_path = os.path.join(
                        BASE_DATA_DIR,
                        image_path
                    )
                    cached = os.path.exists(image_local_path)

                else:  # gcs
                    blob_path = f"{DATASET_VERSION}/images/{label}/{filename}"
                    image_path = f"gs://{bucket.name}/{blob_path}"
                    blob = bucket.blob(blob_path)
                    cached = blob.exists()

                try:
                    # -----------------------------
                    # Download ONLY if not cached
                    # -----------------------------
                    if not cached:
                        url = row.get("image_url")
                        if not isinstance(url, str):
                            pbar.update(1)
                            continue

                        response = session.get(url, timeout=15)
                        response.raise_for_status()

                        img = Image.open(io.BytesIO(response.content)).convert("RGB")

                        if save_mode == "local":
                            save_local(img, label, filename)
                        else:
                            save_gcs(img, label, filename, bucket)

                        pbar.update(1)

                    # -----------------------------
                    # ALWAYS append label row
                    # -----------------------------
                    labels_rows.append({
                        "image_path": image_path,
                        "label": label,
                        "portion_size": row.get("portion_size", None),
                        "nutritional_profile": row.get("nutritional_profile", None)
                    })

                except Exception as e:
                    print("Failed:", e)
                    if not cached:
                        pbar.update(1)
    session.close()

    return labels_rows

def clean_labels_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean labels dataframe:
    - Expand nutritional_profile JSON into flat columns
    - Parse portion_size and compute portion_grams
    - Drop raw JSON columns
    """

    df = df.copy()

    # -----------------------------------
    # 1. Expand "nutritional_profile" JSON
    # -----------------------------------
    def safe_json_load(x):
        if isinstance(x, str):
            try:
                return json.loads(x)
            except Exception:
                return {}
        elif isinstance(x, dict):
            return x
        return {}

    df["nutritional_profile"] = df["nutritional_profile"].apply(safe_json_load)

    nutri_df = pd.json_normalize(df["nutritional_profile"])

    df = pd.concat(
        [df.drop(columns=["nutritional_profile"]), nutri_df],
        axis=1
    )

    # -----------------------------------
    # 2. Clean "portion_size"
    # -----------------------------------
    def safe_list_load(x):
        if isinstance(x, str):
            try:
                return json.loads(x)
            except Exception:
                return []
        elif isinstance(x, list):
            return x
        return []

    df["portion_size"] = df["portion_size"].apply(safe_list_load)

    def sum_grams(ingredients):
        total = 0.0
        for item in ingredients:
            match = re.search(r"(\d+(?:\.\d+)?)g", str(item))
            if match:
                total += float(match.group(1))
        return total

    df["portion_grams"] = df["portion_size"].apply(sum_grams)

    df = df.drop(columns=["portion_size"])

    return df


if __name__ == "__main__":

    # ---- Pre-check version existence ----
    if SAVE_MODE == "local":
        version_path = os.path.join(BASE_DATA_DIR, DATASET_VERSION)

    elif SAVE_MODE == "gcs":
        bucket = storage.Client().bucket(GCS_BUCKET_NAME)

    # ---- Create dataset ----
    labels = create_dataset(save_mode=SAVE_MODE)
    labels_df = pd.DataFrame(labels)

    if labels_df.empty:
        raise ValueError("No samples were created. Check filtering or image downloads.")

    labels_df = clean_labels_dataframe(labels_df)

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
