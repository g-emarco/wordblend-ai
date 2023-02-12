import os
from typing import List

from google.cloud import firestore
from google.cloud import storage
import json
import redis

redis_instance = redis.Redis(host=os.environ.get("REDIS_IP"), port=6379, db=0)


def _retrieve_emails_by_doc_ids(doc_ids: List[str]) -> List[str]:
    print(f"_retrieve_emails_by_doc_ids enter, {doc_ids=}")
    emails = []
    for doc_id in doc_ids:
        email = redis_instance.get(doc_id)
        emails.append(email.decode("utf-8"))
        redis_instance.delete(doc_id)

    return emails


def firestore_updater_cloud_function(data, context):
    print("firestore_updater_cloud_function, enter")
    storage_client = storage.Client()
    print(f"eden, debug data['bucket']= {data['bucket']} ")
    bucket = storage_client.get_bucket(data["bucket"])
    blob = bucket.get_blob(data["name"])
    metadata = blob.metadata

    doc_ids = json.loads(metadata.get("doc_ids").replace("'", '"'))
    description = metadata.get("description", "")
    generated_picture_url = metadata.get("generated_picture_url", "")

    emails = _retrieve_emails_by_doc_ids(doc_ids=doc_ids)

    assert len(emails) == len(
        doc_ids
    ), "emails and doc_ids lists must have the same length"
    print(f"{emails=}, {doc_ids=}, {description=}")

    firestore_client = firestore.Client()

    for email, doc_id in zip(emails, doc_ids):
        doc_path = f"users/{email}/words/{doc_id}"
        doc_ref = firestore_client.document(doc_path)
        doc = doc_ref.get().to_dict()
        co_authors = [e for e in emails if e != email]
        doc.update(
            {
                "entire_description": description,
                "generated_picture_bucket_public_url": blob.public_url,
                "co_authors": list(set(co_authors)),
                "generated_picture_url": generated_picture_url,
            }
        )
        doc_ref.set(doc)
