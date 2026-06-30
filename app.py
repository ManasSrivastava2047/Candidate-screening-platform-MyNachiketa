import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template

from routes.academic import academic_bp
from routes.auth import auth_bp
from routes.emails import emails_bp
from routes.evaluate import evaluate_bp
from routes.github import github_bp
from routes.health import health_bp
from routes.jd import jd_bp
from routes.pipeline import pipeline_bp
from routes.results import results_bp
from routes.rescore import rescore_bp
from routes.resume import resume_bp
from routes.schedule import schedule_bp
from routes.score import score_bp
from routes.shortlist import shortlist_bp
from routes.upload import upload_bp

# Load .env from project root; override stale system placeholders
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "visl-recruit-dev-key"

if os.getenv("RENDER") or os.getenv("FLASK_ENV") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.register_blueprint(upload_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(health_bp)
app.register_blueprint(jd_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(github_bp)
app.register_blueprint(academic_bp)
app.register_blueprint(score_bp)
app.register_blueprint(shortlist_bp)
app.register_blueprint(emails_bp)
app.register_blueprint(results_bp)
app.register_blueprint(rescore_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(pipeline_bp)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
