"""
Create dataset as a one-time artifact (or versioned occasionally)

Choose a save method:
1. Local
2. Google Cloud Storage (GCS)

Both will save the following artifacts:
1. images per class (defined in PER_CLASS variable)
2. labels (defined in DISHES variable)
"""

import io
import pandas as pd
from datasets import load_dataset
from google.cloud import storage

from params import *

def save_local(img, label, filename):
    save_path = os.path.join(OUTPUT_DIR, "images", label, filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    img.save(save_path, format="JPEG", quality=90)

    return f"images/{label}/{filename}"

def save_gcs(img, label, filename, bucket):

    blob_path = f"images/{label}/{filename}"

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    blob = bucket.blob(blob_path)
    blob.upload_from_file(buffer, content_type="image/jpeg")

    return f"gs://{bucket.name}/{blob_path}"


def create_dataset(save_mode="local"):

    dataset = load_dataset("Codatta/MM-Food-100K", split="train")
    labels_rows = []

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

if __name__ == __main__:
    labels = create_dataset(save_mode="gcs")
    labels_df = pd.DataFrame(labels)
