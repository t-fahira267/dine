# =============================
# Dataset Parameters
# =============================

DISHES = [
    "apple",
    "fried chicken",
    "pizza",
    "sushi",
    "ramen",
    "mapo tofu",
    "egg tart",
    "boiled eggs",
    "grilled steak",
    "hamburger",
]

PER_CLASS = 200
DATASET_VERSION = "v1"

BASE_DATA_DIR = "data/mmfood100k"
OUTPUT_DIR = f"{BASE_DATA_DIR}/{DATASET_VERSION}"
OUTPUT_FILENAME = "candidates.csv"
LABELS_FILENAME = "labels.csv"
GCS_BUCKET = "gs://mmfood"
GCS_PREFIX = "mmfood100k"
