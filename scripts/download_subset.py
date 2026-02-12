import os
import requests
import pandas as pd
from tqdm import tqdm
from PIL import Image
from io import BytesIO
from datasets import load_dataset
from params import DISHES, PER_CLASS, OUTPUT_DIR


# ----------------------------
# Helper
# ----------------------------

def download_image(url, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content)).convert("RGB")
    img.save(save_path, format="JPEG", quality=90)


# ----------------------------
# Main
# ----------------------------

print("Loading dataset...")
dataset = load_dataset("Codatta/MM-Food-100K", split="train")
df = dataset.to_pandas()

labels_rows = []

for dish in DISHES:
    print(f"\nDownloading {dish}...")

    dish_df = df[df["dish_name"].str.lower() == dish.lower()]
    dish_df = dish_df.sample(min(PER_CLASS, len(dish_df)), random_state=42)

    label = dish.lower().replace(" ", "_")

    for i, (_, row) in enumerate(tqdm(dish_df.iterrows(), total=len(dish_df))):
        filename = f"{i:06d}.jpg"
        save_path = os.path.join(OUTPUT_DIR, "images", label, filename)

        try:
            download_image(row["image_url"], save_path)

            labels_rows.append({
                "image_path": f"images/{label}/{filename}",
                "label": label
            })

        except Exception as e:
            print("Failed:", e)

# Save labels.csv
labels_df = pd.DataFrame(labels_rows)
labels_df.to_csv(os.path.join(OUTPUT_DIR, "labels.csv"), index=False)

print("\nDone!")
print(f"Total images: {len(labels_df)}")
