from flask import Flask, request, render_template, redirect, url_for, session
import PyPDF2
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

app = Flask(__name__)
app.secret_key = "secret123"

USER_FILE = "users.json"

# Create file if not exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

# Load users
def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

# Save users
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# Extract text
def extract_text(pdf_file):
    text = ""
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text.lower()

# Analyze
def analyze_resume(resume, job_desc):
    resume = resume.lower()
    job_desc = job_desc.lower()

    cv = CountVectorizer(stop_words='english')
    vectors = cv.fit_transform([resume, job_desc])
    similarity = cosine_similarity(vectors)[0][1]

    skills = ["python", "sql", "machine learning", "flask", "api"]

    matched = []
    missing = []

    for s in skills:
        if s in job_desc:
            if s in resume:
                matched.append(s)
            else:
                missing.append(s)

    skill_score = len(matched) / len(skills) if skills else 0
    final_score = (similarity * 0.6 + skill_score * 0.4) * 100

    suggestions = []
    if missing:
        suggestions.append("Add skills: " + ", ".join(missing))
    if final_score < 50:
        suggestions.append("Improve resume content.")

    return round(final_score, 2), matched, missing, suggestions

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return "User already exists!"

        users[username] = password
        save_users(users)

        return redirect(url_for("login"))

    return render_template("register.html")

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid login!"

    return render_template("login.html")

# HOME
@app.route("/home", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    score = None
    matched = []
    missing = []
    suggestions = []

    if request.method == "POST":
        file = request.files["resume"]
        job_desc = request.form["job"]

        if file and job_desc:
            resume_text = extract_text(file)
            score, matched, missing, suggestions = analyze_resume(resume_text, job_desc)

    return render_template("index.html", score=score, matched=matched, missing=missing, suggestions=suggestions)

# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)