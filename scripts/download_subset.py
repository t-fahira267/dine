import os
from io import BytesIO
import pandas as pd
import requests
from PIL import Image
from tqdm import tqdm
from params import DISHES, PER_CLASS, OUTPUT_DIR, OUTPUT_FILENAME, LABELS_FILENAME


def download_image(url: str, save_path: str, timeout: int = 20) -> None:
    """
    Download image bytes from `url`, verify it's a valid image, and save to `save_path`.
    Raises an exception if download fails or image is invalid.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    bio = BytesIO(r.content)

    # verify integrity (requires reopen)
    Image.open(bio).verify()
    bio.seek(0)

    Image.open(bio).convert("RGB").save(save_path, format="JPEG", quality=90)


def load_candidates() -> pd.DataFrame:
    """
    Load and normalize OUTPUT_DIR/candidates.csv.
    Expected columns: dish_name, image_url
    """
    path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    df = pd.read_csv(path)[["dish_name", "image_url"]].dropna()

    df["dish_name"] = df["dish_name"].astype(str).str.strip().str.lower()
    df["image_url"] = df["image_url"].astype(str).str.strip()

    return df


def download_subset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    For each dish in DISHES, download up to PER_CLASS valid images into:
      OUTPUT_DIR/images/<label>/000000.jpg ...
    Returns (labels_df, failures_df).
    """
    rows, failures = [], []
    images_root = os.path.join(OUTPUT_DIR, "images")

    for dish in [d.strip().lower() for d in DISHES]:
        label = dish.replace(" ", "_")
        dish_df = df[df["dish_name"] == dish].sample(frac=1.0, random_state=42).reset_index(drop=True)

        if dish_df.empty:
            print(f"⚠️ No candidates for '{dish}'")
            continue

        saved = 0
        for url in tqdm(dish_df["image_url"], desc=label, total=len(dish_df)):
            if saved >= PER_CLASS:
                break

            filename = f"{saved:06d}.jpg"
            save_path = os.path.join(images_root, label, filename)

            try:
                download_image(url, save_path)
                rows.append({"image_path": f"images/{label}/{filename}", "label": label})
                saved += 1
            except Exception:
                failures.append({"dish_name": dish, "image_url": url})

        if saved < PER_CLASS:
            print(f"⚠️ {label}: only saved {saved}/{PER_CLASS}")

    return pd.DataFrame(rows), pd.DataFrame(failures)


def main() -> None:
    df = load_candidates()
    labels_df, failures_df = download_subset(df)

    labels_path = os.path.join(OUTPUT_DIR, LABELS_FILENAME)
    labels_df.to_csv(labels_path, index=False)
    print(f"\n✅ labels saved: {labels_path} | total images: {len(labels_df)}")
    if not labels_df.empty:
        print(labels_df["label"].value_counts())

    if not failures_df.empty:
        fail_path = os.path.join(OUTPUT_DIR, "failures.csv")
        failures_df.to_csv(fail_path, index=False)
        print(f"\n⚠️ failures saved: {fail_path} ({len(failures_df)})")


if __name__ == "__main__":
    main()
