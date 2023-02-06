import json
import os
import pathlib

from gcp_wrappers.secret_manager import set_secret_env_var
from google.oauth2.service_account import Credentials

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

if os.environ.get("LOCAL"):
    SERVICE_ACCOUNT_SECRET_PATH = os.path.join(
        pathlib.Path(__file__).parent, "client_secret_firebase_adminsdk.json"
    )
    sa_credentials_for_clients = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_SECRET_PATH
    )

set_secret_env_var(
    "wordblend-oauth-client-secret",
    env_key="OAUTH_CLIENT_KEY_CONFIG",
)
set_secret_env_var(
    key_in_secret_manager="wordblend-service-account-key",
    env_key="SA_JSON_CREDENTIALS_FOR_CLIENTS",
)

if os.environ.get("PRODUCTION"):
    sa_credentials_for_clients = json.loads(
        os.environ.get("SA_JSON_CREDENTIALS_FOR_CLIENTS")
    )

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")


import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("client_secret_firebase_adminsdk.json")
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client(firebase_app)
