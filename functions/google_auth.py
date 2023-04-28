import json
import os
import pathlib

from google_auth_oauthlib.flow import Flow


def get_flow():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    cwd = os.path.dirname(os.path.abspath(__file__))

    GOOGLE_CLIENT_ID = \
        json.load(open(os.path.join(cwd, "../client_secret.json"), "r"))["web"][
            "client_id"]
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent,
                                       os.path.join(cwd, "../client_secret.json"))

    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri="http://127.0.0.1:5000/callback"
    )

    return flow, GOOGLE_CLIENT_ID
