from functools import wraps
import os
import json
import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from gcp_wrappers.producer import publish_word
from settings import sa_credentials_for_clients, GOOGLE_OAUTH_CLIENT_ID, db

app = Flask("Google Login App")
app.secret_key = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]


oauth_client_key_config = json.loads(
    os.environ.get("WORDBLEND_OAUTH_CLIENT_SECRET_JSON")
)
flow = Flow.from_client_config(
    client_config=oauth_client_key_config,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri=f"http{'s' if os.environ.get('PRODUCTION') else ''}://{os.environ.get('BASE_URL')}/callback",
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
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_OAUTH_CLIENT_ID,
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["idinfo"] = id_info

    user_info = session["idinfo"]

    users_ref = db.collection("users")
    query = users_ref.where("email", "==", user_info["email"]).get()
    if query:
        print(f"user {user_info['email']} exists, not writing in firestore")
        return redirect("/profile")

    doc_ref = db.collection("users").document(f'{user_info["email"]}')
    doc_ref.set(
        {
            "given_name": f'{user_info["given_name"]}',
            "family_name": f'{user_info["family_name"]}',
            "email": f'{user_info["email"]}',
            "picture": f'{user_info.get("picture") if user_info.get("picture") else ""}',
        }
    )

    return redirect("/profile")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    # return "Wordblend Login <a href='/login'><button>Login</button></a>"
    return render_template("login.html")


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
    if not text:
        return

    user_info = session["idinfo"]

    user_ref = db.collection("users").document(f'{user_info["email"]}')
    words_ref = user_ref.collection("words")
    added_word_ref = words_ref.add({"word": f"{text}", "generated_picture_url": None})

    publish_word(
        email=user_info["email"],
        word=text,
        word_document_id=added_word_ref[1].id,
        credentials=sa_credentials_for_clients,
    )

    return redirect("/profile")


@app.route("/words")
@login_is_required
def get_words():
    user_info = session["idinfo"]
    email = user_info["email"]

    user_ref = db.collection("users").document(email)
    words_ref = user_ref.collection("words")
    words = []
    docs = words_ref.stream()
    for doc in docs:
        words.append(doc.to_dict()["word"])

    return render_template("pictures.html", words=words)


@app.route("/profile")
def profile():
    user_info = session["idinfo"]
    email = user_info["email"]

    # get stats
    user_ref = db.collection("users").document(email)
    word_num = len(user_ref.collection("words").get())
    picture_url_num = len(
        user_ref.collection("words").where("generated_picture_url", "!=", "").get()
    )

    words_ref = user_ref.collection("words").where("generated_picture_url", "!=", "")
    docs = words_ref.stream()
    co_authors = set()
    for doc in docs:
        co_authors.update(doc.to_dict().get("co_authors", []))

    num_co_authors = len(co_authors)
    stats = {
        "word_num": word_num,
        "picture_url_num": picture_url_num,
        "num_co_authors": num_co_authors,
    }

    user_ref = db.collection("users").document(email)
    words_with_pictures = (
        user_ref.collection("words")
        .where("generated_picture_bucket_public_url", "!=", "")
        .get()
    )
    word_docs = [word_doc.to_dict() for word_doc in words_with_pictures]

    return render_template(
        "profile.html", stats=stats, idinfo=session["idinfo"], word_docs=word_docs
    )


@app.route("/pictures")
@login_is_required
def get_pictures():
    user_info = session["idinfo"]
    email = user_info["email"]

    user_ref = db.collection("users").document(email)
    words_with_pictures = (
        user_ref.collection("words")
        .where("generated_picture_bucket_public_url", "!=", "")
        .get()
    )
    word_docs = [word_doc.to_dict() for word_doc in words_with_pictures]
    return render_template(
        "pictures.html", word_docs=word_docs, idinfo=session["idinfo"]
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
