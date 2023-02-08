import uuid
from typing import List
import requests
from google.cloud import storage

BUCKET_NAME = "wordblend-ai-generated-pictures"


def upload_image_to_bucket(
    image_url: str, creators_email_list: List[str], description: str
):
    print(
        f"uploading to bucket picture of: {description}, created by: {creators_email_list}"
    )
    response = requests.get(image_url)
    image_data = response.content

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    blob = bucket.blob(str(uuid.uuid4()))
    blob.upload_from_string(image_data)

    blob.metadata = {
        "creators_email_list": ",".join(creators_email_list),
        "description": description,
    }
    blob.patch()
    print(f"upload successfully")
