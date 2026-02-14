from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI(
    title="Nutrition Predictor API",
    description="Mock API for dish recognition and nutrition estimation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_XLSX_PATH = "docs/nutrition.xlsx"

@app.get(
    "/health",
    summary="Health check",
    description="Simple endpoint used to verify that the API service is running.",
)
def health():
    """
    Returns the health status of the API.
    """
    return {"status": "ok"}


@app.post(
    "/predict",
    summary="Predict dish and nutrition from image",
    description=(
        "Accepts a food image and portion size via multipart/form-data. "
        "Returns the predicted dish, confidence score, and estimated nutrition values. "
        "This is currently a mock implementation."
    ),
)
def predict(
    image: UploadFile = File(..., description="Food image file"),
    portion: float = Form(..., description="Portion size in grams"),
):
    """
    Prediction endpoint.

    Expected form-data:
    - image: uploaded food image
    - portion: portion size in grams (float)

    Returns:
    - predicted dish
    - confidence score
    - nutrition estimates scaled by portion
    """

     # ---- MOCK LOGIC FOR FETCHING IMAGE/PORTION FROM REQUEST ----
    _ = image.file.read()
    base_portion = 200.0

    # ---- MOCK LOGIC FOR MODEL PREDICTION ----
    dish = random.choice(["ramen", "sushi", "curry", "pizza"])
    confidence = round(random.uniform(0.80, 0.98), 2)


    # ---- LOOKUP IN EXCEL ----
    row = app.state.nutrition.loc[dish]

    # ---- SCALE BY PORTION ----
    scale = portion / base_portion

    # ---- ADJUSTING NUTRITION VALUES ----
    nutrition = {
        "calories": int(round(float(row["calories_kcal"]) * scale)),
        "protein_g": round(float(row["protein_g"]) * scale, 1),
        "carbs_g": round(float(row["carbohydrate_g"]) * scale, 1),
        "fat_g": round(float(row["fat_g"]) * scale, 1),
    }

    return {
        "dish": dish,
        "confidence": confidence,
        "portion": portion,
        "nutrition": nutrition,
    }
