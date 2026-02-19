import os

# =============================
# Local file paths
# =============================

BASE_DATA_DIR = os.getenv("BASE_DATA_DIR")
DATASET_OUTPUT_DIR = f"{BASE_DATA_DIR}/"

# =============================
# Dataset Parameters
# =============================

SAVE_MODE = "gcs"  # "local" or "gcs"
DATASET_VERSION = "test_create"
DISHES = ["apple", "fried chicken", "pizza", "sushi", "ramen", "mapo tofu",
          "egg tart", "boiled eggs", "grilled steak", "hamburger"]
PER_CLASS = 1

# =============================
# Google Cloud Storage Parameters
# =============================

GCS_BUCKET_NAME="mmfood"
