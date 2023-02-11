import uuid
from typing import Dict, Any
import requests
from google.cloud import storage

BUCKET_NAME = "wordblend-ai-generated-pictures-public"


def upload_image_to_bucket(
    image_url: str, bucket_object_meta_data: Dict[str, Any], description: str
):
    bucket_object_meta_data.pop("emails")  # don't want pii in public bucket
    print(f"uploading to bucket picture of: {description}, {bucket_object_meta_data=}")
    response = requests.get(image_url)
    image_data = response.content

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    blob = bucket.blob(str(uuid.uuid4()))
    blob.upload_from_string(image_data)

    bucket_object_meta_data["description"] = description
    blob.metadata = bucket_object_meta_data
    blob.patch()
    print(f"upload successfully")
