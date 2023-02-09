from google.cloud import firestore
from google.cloud import storage
import json


def firestore_updater_cloud_function(data, context):
    print("firestore_updater_cloud_function, enter")
    storage_client = storage.Client()
    print(f"eden, debug data['bucket']= {data['bucket']} ")
    bucket = storage_client.get_bucket(data["bucket"])
    blob = bucket.get_blob(data["name"])
    metadata = blob.metadata

    emails = json.loads(metadata.get("emails").replace("'", '"'))
    doc_ids = json.loads(metadata.get("doc_ids").replace("'", '"'))
    description = metadata.get("description", "")
    print(f"type of emails: {type(emails)}")

    print(f"{emails=}, {doc_ids=}, {description=}")

    assert len(emails) == len(
        doc_ids
    ), "emails and doc_ids lists must have the same length"

    firestore_client = firestore.Client()

    for email, doc_id in zip(emails, doc_ids):
        doc_path = f"users/{email}/words/{doc_id}"
        doc_ref = firestore_client.document(doc_path)
        doc = doc_ref.get().to_dict()
        co_authors = [e for e in emails if e != email]
        doc.update(
            {
                "entire_description": description,
                "generated_picture_url": blob.public_url,
                "co_authors": co_authors,
            }
        )
        doc_ref.set(doc)
    print("finished updating firestore")
