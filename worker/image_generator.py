import os
from typing import List, Optional, Tuple, Dict
import requests
import random
from gcp_wrappers.consumer import pull_messages, ack_message_ids
from gcp_wrappers.storage import upload_image_to_bucket

QUERY_URL = "https://api.openai.com/v1/images/generations"


def generate_picture(words: List["str"]) -> Tuple[Optional[str], str]:
    sentence = " ".join(words)
    print(f"generating picture from sentence: {sentence}")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('IMAGE_GEN_API_KEY')}",
    }

    model = "image-alpha-001"
    data = {
        "model": model,
        "prompt": sentence,
        "num_images": 1,
        "size": "512x512",
        "response_format": "url",
    }

    resp = requests.post(QUERY_URL, headers=headers, json=data)

    if resp.status_code != 200:
        raise ValueError("Failed to generate image")

    response_text = resp.json()
    return response_text["data"][0]["url"], sentence


def _create_metadata_for_storage_object(
    messages: List[Dict[str, str]], generated_picture_url: str
) -> Dict:
    emails = []
    doc_ids = []
    for message in messages:
        email = message.get("email")
        doc_id = message.get("word_document_id")
        emails.append(email)
        doc_ids.append(doc_id)
    return {
        "emails": emails,
        "doc_ids": doc_ids,
        "generated_picture_url": generated_picture_url,
    }


def _store_email_by_doc_id_in_redis(doc_ids: List[str], emails: List[str]) -> None:
    print(f"store_email_by_doc_id_in_redis enter, {doc_ids=}, {emails=}")
    import redis

    redis_instance = redis.Redis(host=os.environ.get("REDIS_IP"), port=6379, db=0)
    for i in range(len(doc_ids)):
        redis_instance.set(doc_ids[i], emails[i])

    print("Emails successfully stored for respective doc_ids in Redis")


def main():
    number_of_words = random.randint(3, 5)
    print(f"generating a picture from {number_of_words=}")
    messages, ack_ids = pull_messages(n=number_of_words)
    if not messages:
        return
    words = [message.get("word") for message in messages]
    emails = [message.get("email") for message in messages]
    unique_emails = list(set(emails))
    generated_picture_url, description = generate_picture(words=words)
    print(f"users {unique_emails} generated {generated_picture_url}")

    bucket_object_meta_data = _create_metadata_for_storage_object(
        messages=messages, generated_picture_url=generated_picture_url
    )

    _store_email_by_doc_id_in_redis(
        bucket_object_meta_data.get("doc_ids"),
        emails=bucket_object_meta_data.get("emails"),
    )

    ack_message_ids(msg_ids_to_ack=ack_ids)
    upload_image_to_bucket(
        image_url=generated_picture_url,
        description=description,
        bucket_object_meta_data=bucket_object_meta_data,
    )


if __name__ == "__main__":
    main()
