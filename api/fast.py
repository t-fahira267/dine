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
    from tensorflow.keras.applications import EfficientNetB0
    from tensorflow.keras import layers, models
except ImportError as e:  # pragma: no cover
    raise RuntimeError("tensorflow package not found. Add tensorflow to requirements.txt") from e

from api.model_config import (
    MODEL_VERSION, MODEL_CONFIGS, GCS_BUCKET,
    ATWATER_FAT, ATWATER_PROTEIN, ATWATER_CARBS,
)

BASE_DIR   = Path(__file__).resolve().parent.parent
MODEL_DIR  = Path(os.environ.get("MODEL_DIR", BASE_DIR / "api" / "model"))
IMAGE_SIZE = (224, 224)


def _get_config():
    """Return the config dict for the active MODEL_VERSION."""
    if MODEL_VERSION not in MODEL_CONFIGS:
        available = ", ".join(sorted(MODEL_CONFIGS.keys()))
        raise ValueError(
            f"Unknown MODEL_VERSION '{MODEL_VERSION}'. Available: {available}"
        )
    return MODEL_CONFIGS[MODEL_VERSION]


def _artifact_dir() -> Path:
    """Each version gets its own subdirectory to avoid filename clashes."""
    return MODEL_DIR / MODEL_VERSION


def _maybe_download_from_gcs(config: dict) -> None:
    """Download missing artifacts from GCS for the active model version."""
    dest_dir = _artifact_dir()
    artifact_files = list(config["artifacts"].values())
    missing = [f for f in artifact_files if not (dest_dir / f).exists()]
    if not missing:
        return

    print(f"[{MODEL_VERSION}] Downloading artifacts from GCS ({missing}) …")
    try:
        from google.cloud import storage as gcs_lib
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-storage is required to fetch model artifacts. "
            "Add it to api/requirements.txt."
        ) from exc

    dest_dir.mkdir(parents=True, exist_ok=True)
    client = gcs_lib.Client()
    bucket = client.bucket(GCS_BUCKET)
    for filename in artifact_files:
        blob_name = f"{config['gcs_prefix']}/{filename}"
        dest_path = dest_dir / filename
        print(f"  gs://{GCS_BUCKET}/{blob_name}  →  {dest_path}")
        bucket.blob(blob_name).download_to_filename(str(dest_path))
    print("Download complete.")


app = FastAPI(
    title="Nutrition Predictor API",
    description="Dish recognition and nutrition estimation API.",
    version="0.2.0",
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
    Load model artifacts for the configured MODEL_VERSION.

    Supports three architecture modes:
      legacy    — single end-to-end multitask model (v1)
      joint     — classifier + single 3-output regressor (demo_v3–v10)
      per_macro — classifier + 3 separate regressors (demo_v11+)

    Head-only models (input_type="embeddings") also load an EfficientNetB0
    feature extractor for the image → 1280-dim embedding step.
    """
    config = _get_config()
    _maybe_download_from_gcs(config)

    art_dir   = _artifact_dir()
    artifacts = config["artifacts"]
    mode      = config["mode"]

    # --- Feature extractor (for head-only models) ---
    if config["input_type"] == "embeddings":
        base = EfficientNetB0(
            weights="imagenet", include_top=False,
            input_shape=(*IMAGE_SIZE, 3),
        )
        base.trainable = False
        app.state.feature_extractor = models.Sequential(
            [base, layers.GlobalAveragePooling2D()],
            name="feature_extractor",
        )
        print(f"[{MODEL_VERSION}] Feature extractor loaded (EfficientNetB0 → GAP → 1280)")
    else:
        app.state.feature_extractor = None

    # --- Load models by mode ---
    if mode == "legacy":
        app.state.model = tf.keras.models.load_model(
            str(art_dir / artifacts["model"])
        )
    elif mode == "joint":
        app.state.classifier = tf.keras.models.load_model(
            str(art_dir / artifacts["classifier"])
        )
        app.state.regressor = tf.keras.models.load_model(
            str(art_dir / artifacts["regressor"])
        )
    elif mode == "per_macro":
        app.state.classifier = tf.keras.models.load_model(
            str(art_dir / artifacts["classifier"])
        )
        app.state.regressor_fat = tf.keras.models.load_model(
            str(art_dir / artifacts["regressor_fat"])
        )
        app.state.regressor_protein = tf.keras.models.load_model(
            str(art_dir / artifacts["regressor_protein"])
        )
        app.state.regressor_carbs = tf.keras.models.load_model(
            str(art_dir / artifacts["regressor_carbs"])
        )

    # --- Common artifacts ---
    app.state.label_encoder = joblib.load(art_dir / artifacts["label_encoder"])
    app.state.macro_scaler  = joblib.load(art_dir / artifacts["macro_scaler"])
    app.state.config        = config

    print(f"[{MODEL_VERSION}] Model loaded (mode={mode}, "
          f"log={config['log_transform']}, atwater={config['atwater']})")


@app.get(
    "/health",
    summary="Health check",
    description="Simple endpoint used to verify that the API service is running.",
)
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.post(
    "/predict",
    summary="Predict dish and nutrition from image",
    description=(
        "Accepts a food image via multipart/form-data. "
        "Returns the predicted dish, confidence score, and estimated nutrition values."
    ),
)
def predict(
    image: UploadFile = File(..., description="Food image file"),
):
    config = app.state.config
    mode   = config["mode"]

    # ---- READ & PREPROCESS IMAGE ----
    try:
        img_bytes = image.file.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize(IMAGE_SIZE)
        img_array = preprocess_input(np.array(img, dtype=np.float32))
        img_batch = np.expand_dims(img_array, axis=0)             # (1, 224, 224, 3)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}")

    # ---- EXTRACT FEATURES (head-only models) ----
    if app.state.feature_extractor is not None:
        model_input = app.state.feature_extractor.predict(img_batch, verbose=0)
    else:
        model_input = img_batch

    # ---- CLASSIFICATION ----
    if mode == "legacy":
        preds       = app.state.model.predict(model_input, verbose=0)
        label_probs = preds["label"][0]
    elif mode == "joint":
        label_probs = app.state.classifier.predict(model_input, verbose=0)[0]
    else:  # per_macro
        label_probs = app.state.classifier.predict(model_input, verbose=0)[0]

    class_idx  = int(np.argmax(label_probs))
    confidence = round(float(label_probs[class_idx]), 3)
    dish       = app.state.label_encoder.classes_[class_idx]

    # ---- REGRESSION ----
    if mode == "legacy":
        # Legacy model: named outputs, scaler has 4 cols [fat, protein, cal, carbs]
        macros_scaled = np.array([[
            preds["fat_g"][0, 0],
            preds["protein_g"][0, 0],
            preds["calories_kcal"][0, 0],
            preds["carbohydrate_g"][0, 0],
        ]], dtype=np.float32)
        macros_raw = app.state.macro_scaler.inverse_transform(macros_scaled)[0]
        fat_g, protein_g, calories_kcal, carbs_g = macros_raw

    else:
        # joint / per_macro: scaler has 3 cols [fat, protein, carbs]
        if mode == "joint":
            macros_scaled = app.state.regressor.predict(model_input, verbose=0)
        else:  # per_macro
            pred_fat  = app.state.regressor_fat.predict(model_input, verbose=0)
            pred_prot = app.state.regressor_protein.predict(model_input, verbose=0)
            pred_carb = app.state.regressor_carbs.predict(model_input, verbose=0)
            macros_scaled = np.hstack([pred_fat, pred_prot, pred_carb])

        # Inverse transform: scaler → (optional exp) → raw
        macros = app.state.macro_scaler.inverse_transform(macros_scaled)
        if config["log_transform"]:
            macros = np.expm1(macros)       # exp(y) - 1
        macros = np.maximum(macros, 0.0)

        fat_g, protein_g, carbs_g = macros[0]

        if config["atwater"]:
            calories_kcal = (ATWATER_FAT * fat_g
                           + ATWATER_PROTEIN * protein_g
                           + ATWATER_CARBS * carbs_g)
        else:
            calories_kcal = 0.0             # shouldn't happen for supported versions

    nutrition = {
        "calories":  int(round(float(calories_kcal))),
        "protein_g": round(float(protein_g), 1),
        "carbs_g":   round(float(carbs_g), 1),
        "fat_g":     round(float(fat_g), 1),
    }

    return {
        "dish":          dish,
        "confidence":    confidence,
        "nutrition":     nutrition,
        "model_version": MODEL_VERSION,
    }
