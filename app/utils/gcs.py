from google.cloud import storage
import uuid
import os
from fastapi import UploadFile
from datetime import timedelta

GCS_CREDENTIALS = "app\core\drop-cars-473714-b5e0ebd5f0ab.json"
GCS_BUCKET_NAME = "drop-cars-test-bucket"

client = storage.Client.from_service_account_json(GCS_CREDENTIALS)
# client = storage.Client()
bucket = client.bucket(GCS_BUCKET_NAME)

def upload_image_to_gcs(file: UploadFile, folder: str = "vehicle_owner_details/aadhar") -> str:
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{folder}/{uuid.uuid4()}{ext}"

    blob = bucket.blob(filename)
    blob.upload_from_file(file.file, content_type=file.content_type)

    # No blob.make_public() call

    # If your bucket is public, this will be accessible
    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"


def delete_gcs_file_by_url(public_url: str) -> None:
    """Delete a GCS object given its public URL. No error is raised if delete fails."""
    try:
        prefix = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/"
        if not public_url.startswith(prefix):
            return
        blob_name = public_url[len(prefix):]
        if not blob_name:
            return
        blob = bucket.blob(blob_name)
        blob.delete()
    except Exception:
        # Best-effort cleanup; ignore failures
        return


def generate_signed_url_from_gcs(path_or_url: str, expires_minutes: int = 60) -> str:
    """Generate a time-limited signed URL for a GCS object.

    Accepts either a blob path (e.g., "folder/file.png"), a public URL
    like "https://storage.googleapis.com/<bucket>/<blob>", or a gs:// URL.
    """
    if not path_or_url:
        return path_or_url

    http_prefix = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/"
    gs_prefix = f"gs://{GCS_BUCKET_NAME}/"

    if path_or_url.startswith(http_prefix):
        blob_name = path_or_url[len(http_prefix):]
    elif path_or_url.startswith(gs_prefix):
        blob_name = path_or_url[len(gs_prefix):]
    else:
        blob_name = path_or_url.lstrip('/')

    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(expiration=timedelta(minutes=expires_minutes), method="GET")
