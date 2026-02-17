import os
import pandas as pd
from datasets import load_dataset
from params import DISHES, OUTPUT_DIR, OUTPUT_FILENAME

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ds = load_dataset("Codatta/MM-Food-100K", split="train")
    df = ds.to_pandas()

    # Keep only rows where dish_name matches one of our DISHES (case-insensitive)
    df["dish_name"] = df["dish_name"].astype(str).str.strip().str.lower()
    keep = {d.strip().lower() for d in DISHES}
    df = df[df["dish_name"].isin(keep)].copy()

    # Clean image_url: drop rows with missing/invalid URLs
    df = df.dropna(subset=["image_url"])
    df["image_url"] = df["image_url"].astype(str).str.strip()
    df = df[df["image_url"].str.startswith("http")]

    # Save candidates to CSV. We will download images later in a separate step
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    df[["dish_name", "image_url"]].to_csv(out_path, index=False)
    print("✅ wrote:", out_path, "rows:", len(df))

if __name__ == "__main__":
    main()
