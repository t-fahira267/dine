import os

# =============================
# Local file paths
# =============================

BASE_DATA_DIR = os.getenv("BASE_DATA_DIR")
DATASET_OUTPUT_DIR = f"{BASE_DATA_DIR}/"

# =============================
# Dataset Parameters
# =============================

DISHES = ["apple", "fried chicken", "pizza", "sushi", "ramen", "mapo tofu",
          "egg tart", "boiled eggs", "grilled steak", "hamburger"]
PER_CLASS = 200
DATASET_VERSION = "v1"

# --- Only when running `make clean_dataset`
SAVE_MODE = "local"  # or "gcs"

# --- Only when running `make dataset` ---
OUTPUT_FILENAME = "candidates.csv"
LABELS_FILENAME = "labels.csv"

# =============================
# Google Cloud Storage Parameters
# =============================

GCS_BUCKET_NAME="mmfood"
