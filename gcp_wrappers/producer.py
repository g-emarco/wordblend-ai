import json
import logging
import os
from google.oauth2.service_account import Credentials

from google.cloud import pubsub_v1

from settings import TOPIC_NAME

logger = logging.getLogger()


def publish_word(
    email: str, word: str, word_document_id: str, credentials: Credentials
) -> None:
    logger.info(f"publish_word enter")
    if not os.environ.get("PRODUCTION"):
        publisher = pubsub_v1.PublisherClient(credentials=credentials)
    else:
        publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ.get("GCP_PROJECT"), TOPIC_NAME)
    message = {"email": email, "word": word, "word_document_id": word_document_id}
    logger.info(f"publishing {message=} to topic {topic_path}")
    publisher.publish(topic_path, data=json.dumps(message).encode("utf-8"))
