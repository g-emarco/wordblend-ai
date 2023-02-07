import logging
import os
from google.oauth2.service_account import Credentials

from google.cloud import pubsub_v1


TOPIC_NAME = "words"

# logger = logging.getLogger()

def publish_word(
    email: str, word: str, word_document_id: str, credentials: Credentials
) -> None:
    print(f"publish_word enter")
    if not os.environ.get("PRODUCTION"):
        publisher = pubsub_v1.PublisherClient(credentials=credentials)
    else:
        publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ.get("GCP_PROJECT"), TOPIC_NAME)
    message = {"email": email, "word": word, "word_document_id": word_document_id}
    print(f"publishing {message=} to topic {topic_path}")
    publisher.publish(topic_path, data=str.encode(str(message)))
