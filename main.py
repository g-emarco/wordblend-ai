from functools import wraps
import os
import pathlib

import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

app = Flask("Google Login App")
app.secret_key = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "client_secret_oauth.json"
)

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("client_secret_firebase_adminsdk.json")
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client(firebase_app)

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri="http://localhost/callback",
)


def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state

    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    # if not session["state"] == request.args["state"]:
    #     abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["idinfo"] = id_info

    user_info = session["idinfo"]

    users_ref = db.collection("users")
    query = users_ref.where("email", "==", user_info["email"]).get()
    if query:
        print("user exists, not writing in firestore")
        return redirect("/profile")

    doc_ref = db.collection("users").document(f'{user_info["email"]}')
    doc_ref.set(
        {
            "given_name": f'{user_info["given_name"]}',
            "family_name": f'{user_info["family_name"]}',
            "email": f'{user_info["email"]}',
            "picture": f'{user_info["picture"]}',
        }
    )

    return redirect("/profile")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    return "Hello World <a href='/login'><button>Login</button></a>"


@app.route("/profile")
@login_is_required
def profile():
    return render_template("user_info.html", idinfo=session["idinfo"])


@app.route("/word", methods=["GET"])
@login_is_required
def word():
    return """
        <form action="/add_word" method="post">
            <input type="text" name="text">
            <input type="submit" value="Submit">
        </form>
    """


@app.route("/add_word", methods=["POST"])
def add_word():
    # add what happens if no "idinfo"
    text = request.form["text"]
    user_info = session["idinfo"]

    user_ref = db.collection("users").document(f'{user_info["email"]}')
    words_ref = user_ref.collection("words")
    words_ref.add({"word": f"{text}", "generated_picture_url": None})

    return redirect("/profile")


@app.route("/words")
@login_is_required
def words():
    user_info = session["idinfo"]
    email = user_info["email"]

    user_ref = db.collection("users").document(email)
    words_ref = user_ref.collection("words")
    words = []
    docs = words_ref.stream()
    for doc in docs:
        words.append(doc.to_dict()["word"])

    return render_template("words.html", words=words)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
