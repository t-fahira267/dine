import io
import pandas as pd
from gcsfs import GCSFileSystem
from google.cloud import storage
from PIL import Image

from dine.params import *

# Instantiate the filesystem (handles authentication via Application Default Credentials)
fs = GCSFileSystem()

def load_labels_csv_from_gcs(bucket_name: str = GCS_BUCKET_NAME,
                             dataset_version: str = DATASET_VERSION) -> pd.DataFrame:
    """
    Load the labels.csv from GCS and return as a Pandas DataFrame
    """
    # Define the GCS URI
    gcs_uri = f"gs://{bucket_name}/{dataset_version}/labels.csv"

    # Load the data into a pandas DataFrame
    # The 'storage_options' argument passes the GCS filesystem handler
    df = pd.read_csv(gcs_uri, storage_options={'fs': fs})

    return df

def load_image_from_gcs(image_gcs_uri: str) -> Image.Image:
    """
    Load image from full GCS URI:
    gs://mmfood/v1-portion/images/apple/000000.jpg
    """

    with fs.open(image_gcs_uri, "rb") as f:
        image = Image.open(f).convert("RGB")

    return image


# Example usage
if __name__ == "__main__":

    df = load_labels_csv_from_gcs()

    img = load_image_from_gcs(df.loc[0, "image_path"])
    img.show()
