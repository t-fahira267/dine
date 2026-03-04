from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import numpy as np
import joblib
from PIL import Image
from pathlib import Path

# Lazy-import TF so startup errors are clear
try:
    import tensorflow as tf
    from tensorflow.keras.applications.efficientnet import preprocess_input
except ImportError as e:  # pragma: no cover
    raise RuntimeError("tensorflow package not found. Add tensorflow to requirements.txt") from e


BASE_DIR          = Path(__file__).resolve().parent.parent
MODEL_DIR         = Path(os.environ.get("MODEL_DIR", BASE_DIR / "api" / "model"))
GCS_BUCKET        = os.environ.get("GCS_BUCKET", "mmfood")
GCS_MODEL_PREFIX  = os.environ.get("GCS_MODEL_PREFIX", "models/v1")
IMAGE_SIZE        = (224, 224)   # must match training

MODEL_ARTIFACTS = [
    "multitask_v4.keras",
    "macro_scaler.pkl",
    "label_encoder.pkl",
]


def _maybe_download_from_gcs() -> None:
    """
    If any model artifact is missing from MODEL_DIR, download all of them
    from GCS (gs://{GCS_BUCKET}/{GCS_MODEL_PREFIX}/).

    In production (Cloud Run) the files are never checked in to git, so
    this function fetches them at container startup.  Locally, if the files
    already exist the function is a no-op.
    """
    missing = [f for f in MODEL_ARTIFACTS if not (MODEL_DIR / f).exists()]
    if not missing:
        return

    print(f"Model artifacts not found locally ({missing}). Downloading from GCS …")
    try:
        from google.cloud import storage as gcs
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-storage is required to fetch model artifacts. "
            "Add it to api/requirements.txt."
        ) from exc

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    client = gcs.Client()
    bucket = client.bucket(GCS_BUCKET)
    for filename in MODEL_ARTIFACTS:
        blob_name = f"{GCS_MODEL_PREFIX}/{filename}"
        dest_path = MODEL_DIR / filename
        print(f"  gs://{GCS_BUCKET}/{blob_name}  →  {dest_path}")
        bucket.blob(blob_name).download_to_filename(str(dest_path))
    print("Model artifacts downloaded.")


app = FastAPI(
    title="Nutrition Predictor API",
    description="Dish recognition and nutrition estimation API.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_model():
    """
    Load the Keras model + sklearn artifacts saved from Colab.

    Locally:      place the three files in api/model/ (they are gitignored).
    Production:   set GCS_BUCKET / GCS_MODEL_PREFIX env vars and the files
                  are downloaded automatically from GCS at container startup.

    Expected artifacts:
      multitask_v4.keras   — the trained e2e_model
      macro_scaler.pkl     — sklearn StandardScaler fitted on train macros
      label_encoder.pkl    — sklearn LabelEncoder fitted on train labels
    """
    _maybe_download_from_gcs()

    model_path  = MODEL_DIR / "multitask_v4.keras"
    scaler_path = MODEL_DIR / "macro_scaler.pkl"
    le_path     = MODEL_DIR / "label_encoder.pkl"

    app.state.model         = tf.keras.models.load_model(str(model_path))
    app.state.macro_scaler  = joblib.load(scaler_path)
    app.state.label_encoder = joblib.load(le_path)
    print(f"Model loaded from {model_path}")


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
        "Accepts a food image via multipart/form-data. "
        "Returns the predicted dish, confidence score, and estimated nutrition values "
        "using a multi-task EfficientNetB0 model."
    ),
)
def predict(
    image: UploadFile = File(..., description="Food image file"),
):
    """
    Prediction endpoint.

    Expected form-data:
    - image: uploaded food image

    Returns:
    - predicted dish
    - confidence score
    - estimated nutrition values (for a standard serving as seen in training data)
    """
    # ---- READ & PREPROCESS IMAGE ----
    try:
        img_bytes = image.file.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize(IMAGE_SIZE)
        img_array = np.array(img, dtype=np.float32)               # (224, 224, 3)
        img_array = preprocess_input(img_array)                   # EfficientNet normalisation
        img_batch = np.expand_dims(img_array, axis=0)             # (1, 224, 224, 3)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}")

    # ---- RUN MODEL ----
    preds = app.state.model.predict(img_batch, verbose=0)

    # ---- CLASSIFICATION HEAD → dish + confidence ----
    label_probs = preds["label"][0]                               # (NUM_CLASSES,)
    class_idx   = int(np.argmax(label_probs))
    confidence  = round(float(label_probs[class_idx]), 3)
    dish        = app.state.label_encoder.classes_[class_idx]

    # ---- REGRESSION HEADS → macros (inverse-transform StandardScaler) ----
    # Each head output is shape (1, 1); stack into (1, 4) for inverse_transform
    macros_scaled = np.array([[
        preds["fat_g"][0, 0],
        preds["protein_g"][0, 0],
        preds["calories_kcal"][0, 0],
        preds["carbohydrate_g"][0, 0],
    ]], dtype=np.float32)
    fat_g, protein_g, calories_kcal, carbohydrate_g = \
        app.state.macro_scaler.inverse_transform(macros_scaled)[0]

    nutrition = {
        "calories": int(round(float(calories_kcal))),
        "protein_g": round(float(protein_g), 1),
        "carbs_g":   round(float(carbohydrate_g), 1),
        "fat_g":     round(float(fat_g), 1),
    }

    return {
        "dish":       dish,
        "confidence": confidence,
        "nutrition":  nutrition,
    }
