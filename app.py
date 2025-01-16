from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_dance.contrib.google import make_google_blueprint, google
import jwt
import datetime
from google.cloud import secretmanager

# Public Key for JWT
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEEVs/o5+uQbTjL3chynL4wXgUg2R9
q9UU8I5mEovUf86QZ7kOBIjJwqnzD1omageEHWwHdBO6B+dFabmdT9POxg==
-----END PUBLIC KEY-----"""

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Store submissions in memory
submissions = []


def access_secret_version(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/pomelo-447821/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Fetch Client ID, Secret, and JWT PUBLIC KEY from GCP
GOOGLE_CLIENT_ID = access_secret_version("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = access_secret_version("GOOGLE_CLIENT_SECRET")
# PUBLIC_KEY = access_secret_version("JWT_PUBLIC_KEY")

# Google OAuth setup
blueprint = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
)
app.register_blueprint(blueprint, url_prefix="/login")

# Make 'google' available in templates
@app.context_processor
def inject_google():
    return {'google': google}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Verify Google authorization
            if not google.authorized:
                print("User not authorized.")
                return redirect(url_for("google.login"))

            # Get the submitted text
            text = request.form.get("text")
            print(f"Received text: {text}")

            # Capture current datetime
            datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if the text is a valid JWT
            is_jwt = False
            if text and text.count(".") == 2:  # Basic check for JWT format
                try:
                    jwt.decode(
                        text,
                        PUBLIC_KEY,
                        algorithms=["ES256"],
                        options={"verify_exp": False},
                    )
                    is_jwt = True
                    print("Valid JWT detected.")
                except jwt.ExpiredSignatureError:
                    print("JWT expired.")
                except jwt.InvalidSignatureError:
                    print("Invalid JWT signature.")
                except jwt.DecodeError:
                    print("Not a valid JWT.")
                except Exception as e:
                    print(f"Unexpected JWT decoding error: {e}")

            # Append submission to in-memory list
            submissions.append({
                "text": text,
                "datetime": datetime_now,
                "is_jwt": is_jwt
            })
            print("Submission added to in-memory list.")

        except Exception as e:
            print(f"Error during submission: {e}")
            return "An error occurred.", 500

        return redirect(url_for("index"))

    return render_template("index.html", submissions=submissions)


@app.route("/logout")
def logout():
    # Clear the Flask-Dance session
    if "google_oauth_token" in session:
        del session["google_oauth_token"]

    return redirect(url_for("index"))

@app.route("/debug-secrets")
def debug_secrets():
    try:
        client_id = access_secret_version("GOOGLE_CLIENT_ID")
        client_secret = access_secret_version("GOOGLE_CLIENT_SECRET")
        return jsonify({"client_id": client_id, "client_secret": client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug-submissions")
def debug_submissions():
    return jsonify(submissions)


if __name__ == "__main__":
    app.run(ssl_context=("cert.pem", "key.pem"), debug=True)
