import json
import os
from typing import List, Dict, Tuple

import google.cloud.pubsub_v1 as pubsub
from google.api_core.exceptions import DeadlineExceeded

from settings import SUBSCRIPTION_ID

PROJECT_ID = os.environ.get("GCP_PROJECT")


def pull_messages(n: int = 4) -> Tuple[List[Dict[str, str]], List[str]]:
    try:
        subscriber = pubsub.SubscriberClient()
        subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
        response = subscriber.pull(
            subscription=subscription_path, max_messages=n, timeout=3
        )

        messages = []
        for message in response.received_messages:
            print(f"Message ID: {message.message.message_id}")
            message = json.loads(message.message.data.decode("utf-8"))
            print(message)
            messages.append(message)

        ack_ids = [message.ack_id for message in response.received_messages]
    except DeadlineExceeded:
        print("no messages to pull")
        return [], []

    return messages, ack_ids


def ack_message_ids(msg_ids_to_ack: List[str]) -> None:
    if not msg_ids_to_ack:
        print(f"{msg_ids_to_ack=}, returning...")
        return
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    subscriber.acknowledge(subscription=subscription_path, ack_ids=msg_ids_to_ack)
