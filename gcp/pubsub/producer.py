import os
from google.oauth2.service_account import Credentials

from google.cloud import pubsub_v1

from settings import SERVICE_ACCOUNT_SECRET_PATH

TOPIC_NAME = "words"



def publish_word(email: str, word: str, word_document_id: str):
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_SECRET_PATH)

    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    topic_path = publisher.topic_path(os.environ.get("GCP_PROJECT"), TOPIC_NAME)
    print(f"{topic_path=}")
    message = {"email": email, "word": word, "word_document_id": word_document_id}
    publisher.publish(topic_path, data=str.encode(str(message)))
