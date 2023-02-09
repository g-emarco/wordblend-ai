from google.cloud import firestore
from google.cloud import storage


def firestore_updater_cloud_function(data, context):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(data["bucket"])
    blob = bucket.get_blob(data["name"])
    metadata = blob.metadata

    emails = metadata.get("emails", [])
    doc_ids = metadata.get("doc_ids", [])
    description = metadata.get("description", "")

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
                "generated_picture_url": blob.generate_signed_url(expiration=3600),
                "co_authors": co_authors,
            }
        )
        doc_ref.set(doc)
