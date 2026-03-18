"""
Model version configuration for the Dine API.

Change MODEL_VERSION to switch which model the API loads.
Override via env var: MODEL_VERSION=demo_v11.0

Each config specifies:
  gcs_prefix:     path under gs://mmfood/ for artifact download
  mode:           "legacy" | "joint" | "per_macro"
                    legacy   = single end-to-end multitask model (pre-demo)
                    joint    = classifier.keras + regressor.keras (1 regressor, 3 outputs)
                    per_macro = classifier.keras + 3 separate regressor_*.keras
  input_type:     "image" (end-to-end model) | "embeddings" (head-only, needs backbone)
  log_transform:  whether regression targets use log(1+y) transform
  atwater:        whether calories are derived via Atwater (True) or predicted directly (False)
  artifacts:      dict mapping artifact keys to filenames in GCS
"""

import os

# =====================================================================
#  Model version — set via Cloud Build substitution variable _MODEL_VERSION
#  which passes MODEL_VERSION env var to Cloud Run.
#  For local dev: export MODEL_VERSION=demo_v11.0 (or add to .envrc)
# =====================================================================
MODEL_VERSION = os.environ.get("MODEL_VERSION", "demo_v11.0")

# Atwater conversion factors: cal = 9*fat + 4*protein + 4*carbs
ATWATER_FAT     = 9.0
ATWATER_PROTEIN = 4.0
ATWATER_CARBS   = 4.0

# GCS bucket
GCS_BUCKET = os.environ.get("GCS_BUCKET", "mmfood")


# -- Helper builders (reduce boilerplate) ------------------------------------

_COMMON_ARTIFACTS = {
    "label_encoder": "label_encoder.pkl",
    "macro_scaler":  "macro_scaler.pkl",
}

def _joint(version, log_transform):
    """Config for classifier + single 3-output regressor."""
    return {
        "gcs_prefix":    f"models/{version}",
        "mode":          "joint",
        "input_type":    "embeddings",
        "log_transform": log_transform,
        "atwater":       True,
        "artifacts":     {
            "classifier": "classifier.keras",
            "regressor":  "regressor.keras",
            **_COMMON_ARTIFACTS,
        },
    }

def _per_macro(version, log_transform, *, input_type="embeddings", prefix=""):
    """Config for classifier + 3 separate single-output regressors."""
    return {
        "gcs_prefix":    f"models/{version}",
        "mode":          "per_macro",
        "input_type":    input_type,
        "log_transform": log_transform,
        "atwater":       True,
        "artifacts":     {
            "classifier":        f"{prefix}classifier.keras",
            "regressor_fat":     f"{prefix}regressor_fat.keras",
            "regressor_protein": f"{prefix}regressor_protein.keras",
            "regressor_carbs":   f"{prefix}regressor_carbs.keras",
            **_COMMON_ARTIFACTS,
        },
    }


# =====================================================================
#  Model version registry
# =====================================================================
MODEL_CONFIGS = {

    # ---- Legacy (pre-demo series) ----------------------------------------
    # Single end-to-end multitask model with named outputs.
    # Scaler has 4 columns: [fat, protein, cal, carbs].
    "v1": {
        "gcs_prefix":    "models/v1",
        "mode":          "legacy",
        "input_type":    "image",
        "log_transform": False,
        "atwater":       False,
        "artifacts":     {
            "model": "multitask_v4.keras",
            **_COMMON_ARTIFACTS,
        },
    },

    # ---- Demo series: joint regressor (classifier + 1 regressor) ---------
    # Head-only models trained on frozen EfficientNetB0 GAP embeddings.
    # Scaler has 3 columns: [fat, protein, carbs].

    # No log-transform
    "demo_v3.0":  _joint("demo_v3.0",  log_transform=False),
    "demo_v4.0":  _joint("demo_v4.0",  log_transform=False),

    # Log-transform: model outputs log-scaled values
    "demo_v7.0":  _joint("demo_v7.0",  log_transform=True),
    "demo_v8.0":  _joint("demo_v8.0",  log_transform=True),
    "demo_v10.0": _joint("demo_v10.0", log_transform=True),

    # ---- Demo series: per-macro regressors (3 separate models) -----------
    # Head-only, log-transform, Atwater.
    "demo_v11.0": _per_macro("demo_v11.0", log_transform=True),
    "demo_v12.0": _per_macro("demo_v12.0", log_transform=True),

    # ---- Phase B: fine-tuned end-to-end models ---------------------------
    # End-to-end models (image input, backbone included), log-transform, Atwater.
    "demo_v13.0": _per_macro("demo_v13.0", log_transform=True,
                              input_type="image", prefix="ft_"),
}

# Versions NOT included (need special handling or are historical):
#   demo_v1.0, demo_v2.0 — no Atwater, 4-output regressor, different scaler shape
#   demo_v5.0            — fine-tuned (end-to-end), but unsure of saved artifact format
#   demo_v6.0            — multi-task shared Dense(256), non-standard architecture
#   demo_v9.0            — class-conditional (regressor takes [embeddings|probs], 1292-dim input)
#   v5_0, v6_0           — old pre-demo fine-tuned models, non-standard
