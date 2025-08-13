from google.cloud import storage
import uuid
import os
from fastapi import UploadFile

GCS_CREDENTIALS = "app/core/drop-cars-468718-d08441443ada.json"
GCS_BUCKET_NAME = "drop-cars-files"

client = storage.Client.from_service_account_json(GCS_CREDENTIALS)
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
