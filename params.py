import os

# =============================
# Dataset Parameters
# =============================

DISHES = ["Apple", "Fried Chicken", "Pizza", "Sushi", "Sushi Platter"
          "Mapo Tofu", "Egg Tart", "Boiled Eggs", "Grilled Steak",
          "Hamburger", "Oranges"]
PER_CLASS = 50
DATASET_VERSION = os.getenv("DATASET_VERSION")

BASE_DATA_DIR = os.getenv("BASE_DATA_DIR")
OUTPUT_DIR = f"{BASE_DATA_DIR}/{DATASET_VERSION}"


DEPLOYMENT=os.getenv("DEPLOYMENT")
GCS_BUCKET_NAME="dine-mmfood"
