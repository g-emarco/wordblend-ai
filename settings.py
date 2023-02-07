import json
import os
import pathlib

from google.oauth2.service_account import Credentials
import firebase_admin
from firebase_admin import credentials, firestore

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

if os.environ.get("LOCAL"):
    SERVICE_ACCOUNT_SECRET_PATH = os.path.join(
        pathlib.Path(__file__).parent, "client_secret_firebase_adminsdk.json"
    )
    sa_credentials_for_clients = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_SECRET_PATH
    )

    OATH_KEY_JSON_PATH = os.path.join(
        pathlib.Path(__file__).parent, "client_secret_oauth.json"
    )

    with open(OATH_KEY_JSON_PATH) as file:
        client_secret_oauth = file.read()
        os.environ.setdefault("WORDBLEND_OAUTH_CLIENT_SECRET_JSON", client_secret_oauth)

    firebase_credentials = credentials.Certificate(
        "client_secret_firebase_adminsdk.json"
    )

if os.environ.get("PRODUCTION"):
    sa_credentials_for_clients = json.loads(
        os.environ.get("WORDBLEND_SERVICE_ACCOUNT_KEY_JSON")
    )

    firebase_credentials = credentials.Certificate(sa_credentials_for_clients)

GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")


firebase_app = firebase_admin.initialize_app(firebase_credentials)
db = firestore.client(firebase_app)
