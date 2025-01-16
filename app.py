from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
import sqlite3
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

def access_secret_version(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/pomelo-447821/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Fetch Client ID and Secret from GCP
GOOGLE_CLIENT_ID = access_secret_version("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = access_secret_version("GOOGLE_CLIENT_SECRET")

# Google OAuth setup
blueprint = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
        ]
)
app.register_blueprint(blueprint, url_prefix="/login")

# Make 'google' available in templates
@app.context_processor
def inject_google():
    return {'google': google}

# Database initialization
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY,
            text TEXT,
            datetime TEXT,
            is_jwt BOOLEAN
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not google.authorized:
            return redirect(url_for("google.login"))  # Redirect to Google login if not authorized
         
        text = request.form.get("text")  # Get input text
        datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if text is a valid JWT
        is_jwt = False  # Default is False (not a JWT)
        try:
            jwt.decode(text, PUBLIC_KEY, algorithms=["ES256"], options={"verify_exp": False})
            is_jwt = True  # Valid JWT
        except jwt.ExpiredSignatureError:
            print("JWT has expired")
        except jwt.InvalidSignatureError:
            print("Invalid JWT signature")
        except jwt.DecodeError:
            print("Error decoding JWT")
        except Exception as e:
            print(f"Unexpected error: {e}")

        # Save the text and its status (is_jwt) to the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO submissions (text, datetime, is_jwt) VALUES (?, ?, ?)",
            (text, datetime_now, is_jwt),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    # Retrieve all submissions
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions")
    submissions = cursor.fetchall()
    conn.close()

    return render_template("index.html", submissions=submissions)


# Logout route
@app.route("/logout")
def logout():
    # Clear the Flask-Dance session
    if "google_oauth_token" in session:
        del session["google_oauth_token"]

    # Redirect to Google's logout URL
    return redirect("/")

@app.route("/debug-token")
def debug_token():
    return jsonify(google.token)

if __name__ == "__main__":
    app.run(ssl_context=("cert.pem", "key.pem"), debug=True)
