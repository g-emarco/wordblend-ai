import os
from google.oauth2.service_account import Credentials


def access_secret_version(key: str, credentials: Credentials = None) -> str:
    from google.cloud import secretmanager

    if credentials:
        client = secretmanager.SecretManagerServiceClient(credentials=credentials)
    else:
        client = secretmanager.SecretManagerServiceClient()
    secret_id = (
        f"projects/{os.environ.get('GCP_PROJECT_NUMBER')}/secrets/{key}/versions/latest"
    )
    response = client.access_secret_version(request={"name": secret_id})
    secret = response.payload.data.decode("UTF-8")

    return secret


def set_secret_env_var(
    key_in_secret_manager: str,
    env_key: str,
    credentials: Credentials = None,
) -> None:
    secret = access_secret_version(key=key_in_secret_manager, credentials=credentials)
    if env_key:
        os.environ.setdefault(env_key, secret)
    else:
        os.environ.setdefault(key_in_secret_manager, secret)
