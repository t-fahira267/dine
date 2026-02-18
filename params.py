import os

# =============================
# Local file paths
# =============================

BASE_DATA_DIR = os.getenv("BASE_DATA_DIR")
DATASET_OUTPUT_DIR = f"{BASE_DATA_DIR}/"

# =============================
# Dataset Parameters
# =============================

SAVE_MODE = "local"  # or "gcs"
DISHES = ["Apple", "Fried Chicken", "Pizza", "Sushi", "Sushi Platter"
          "Mapo Tofu", "Egg Tart", "Boiled Eggs", "Grilled Steak",
          "Hamburger", "Oranges"]
PER_CLASS = 1

# =============================
# Google Cloud Storage Parameters
# =============================

GCS_BUCKET_NAME="dine-mmfood"
