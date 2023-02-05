import os
import pathlib

from gcp_wrappers.secret_manager import set_secret_env_var
from google.oauth2.service_account import Credentials

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


SERVICE_ACCOUNT_SECRET_PATH = os.path.join(
    pathlib.Path(__file__).parent, "client_secret_firebase_adminsdk.json"
)
sa_credentials_for_clients = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_SECRET_PATH
)

os.environ.setdefault("PRODUCTION", "True")
if os.environ.get("PRODUCTION"):
    set_secret_env_var(
        "wordblend-oauth-client-secret",
        env_key="OAUTH_CLIENT_KEY_CONFIG",
        credentials=sa_credentials_for_clients,
    )
