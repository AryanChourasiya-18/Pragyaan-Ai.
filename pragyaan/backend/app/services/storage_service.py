import os
import uuid

from app.config import settings


def save_upload(file_bytes: bytes, original_filename: str) -> str:
    """Saves the uploaded file and returns a path/key that pdf_service can read from.

    Local backend returns a filesystem path. S3 backend uploads and returns the key
    (the caller is responsible for downloading to a temp path before PDF parsing,
    since PyPDF2/pdf2image need a local file).
    """
    ext = os.path.splitext(original_filename)[1] or ".pdf"
    key = f"{uuid.uuid4()}{ext}"

    if settings.storage_backend == "s3":
        return _save_to_s3(file_bytes, key)

    os.makedirs(settings.local_storage_dir, exist_ok=True)
    path = os.path.join(settings.local_storage_dir, key)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def _save_to_s3(file_bytes: bytes, key: str) -> str:
    import boto3

    s3 = boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        endpoint_url=settings.s3_endpoint_url or None,
    )
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=file_bytes)

    # Download to a local temp path since PDF libraries need a filesystem path.
    local_tmp = os.path.join("/tmp", key)
    s3.download_file(settings.s3_bucket, key, local_tmp)
    return local_tmp
