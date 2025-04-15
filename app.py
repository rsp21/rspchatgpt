from flask import Flask, render_template
from dotenv import load_dotenv
from flask_login import login_required
import os

from routes.transcribe import transcribe_bp
from auth import auth_bp, login_manager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Register Blueprints
app.register_blueprint(transcribe_bp)
app.register_blueprint(auth_bp)

# Initialize LoginManager
login_manager.init_app(app)

@app.route("/")
@login_required
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
