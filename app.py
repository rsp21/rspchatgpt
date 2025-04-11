from flask import Flask, render_template
from dotenv import load_dotenv
import os

from routes.transcribe import transcribe_bp
from routes.user import user_bp  # ⬅️ new

load_dotenv()

app = Flask(__name__)
app.register_blueprint(transcribe_bp)
app.register_blueprint(user_bp)  # ⬅️ new

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
