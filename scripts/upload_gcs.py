import subprocess

from params import OUTPUT_DIR, DATASET_VERSION, GCS_BUCKET, GCS_PREFIX


def gcs_destination() -> str:
    """
    Where to upload this dataset version in GCS.
    Update the bucket/prefix here once and everyone uses the same path.
    """
    return f"{GCS_BUCKET}/{GCS_PREFIX}/{DATASET_VERSION}"


def upload_dir_to_gcs(src_dir: str, dst_uri: str) -> None:
    """
    Upload a local directory to GCS using gsutil rsync.
    """
    cmd = ["gsutil", "-m", "rsync", "-r", src_dir, dst_uri]
    subprocess.run(cmd, check=True)


def main() -> None:
    dst = gcs_destination()
    print(f"Uploading:\n  local: {OUTPUT_DIR}\n  gcs:   {dst}\n")
    upload_dir_to_gcs(OUTPUT_DIR, dst)
    print("✅ Upload complete")


if __name__ == "__main__":
    main()
