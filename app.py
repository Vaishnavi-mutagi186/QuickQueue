from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ✅ AI MODEL IMPORT
from ml_model import predict_disease

app = Flask(__name__)

# -------------------- DATABASE SETUP --------------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------- MODEL --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    service = db.Column(db.String(100))
    token = db.Column(db.Integer)
    priority = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="waiting")
    time_joined = db.Column(db.String(20))
    waiting = db.Column(db.Integer)
    people_ahead = db.Column(db.Integer)

    # AI FIELDS
    symptoms = db.Column(db.String(200))
    recommendation = db.Column(db.String(200))

# -------------------- CREATE DATABASE --------------------

with app.app_context():
    db.create_all()

# -------------------- CORE LOGIC --------------------

def get_next_token(service):
    last_user = User.query.filter_by(service=service).order_by(User.token.desc()).first()
    return 1 if not last_user else last_user.token + 1

def sort_queue(users):
    return sorted(users, key=lambda x: (not x.priority, x.token))

def calculate_wait_time(users):
    BASE_TIME = 4

    for i, user in enumerate(users):
        multiplier = 0.4 if user.priority else 1
        user.waiting = int(i * BASE_TIME * multiplier)
        user.people_ahead = i
    return users

# -------------------- MAIN PAGE --------------------

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        name = request.form["name"]
        service = request.form["service"]
        priority = request.form.get("priority") == "on"

        # ✅ SYMPTOMS INPUT
        symptoms = request.form.get("symptoms", "")

        # 🤖 AI PREDICTION
        result = predict_disease(symptoms)
        recommendation = result["disease"]

        token_number = get_next_token(service)

        new_user = User(
            name=name,
            service=service,
            token=token_number,
            priority=priority,
            status="waiting",
            time_joined=datetime.now().strftime("%H:%M:%S"),

            symptoms=symptoms,
            recommendation=recommendation
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    services = db.session.query(User.service).distinct()

    data = {}
    for s in services:
        users = User.query.filter_by(service=s.service).all()
        users = sort_queue(users)
        users = calculate_wait_time(users)
        data[s.service] = users

    return render_template("index.html", services=data)

# -------------------- CALL NEXT USER --------------------

@app.route("/call/<service>")
def call_next(service):
    user = User.query.filter_by(service=service, status="waiting").first()

    if user:
        user.status = "called"
        db.session.commit()

    return redirect("/")

# -------------------- SERVE USER --------------------

@app.route("/serve/<service>")
def serve(service):
    user = User.query.filter_by(service=service).order_by(User.token).first()

    if user:
        user.status = "served"
        db.session.delete(user)
        db.session.commit()

    return redirect("/")

# -------------------- RESET SYSTEM --------------------

@app.route("/reset")
def reset():
    User.query.delete()
    db.session.commit()
    return redirect("/")

# -------------------- STATS API --------------------

@app.route("/stats/<service>")
def stats(service):
    users = User.query.filter_by(service=service).all()

    return jsonify({
        "total": len(users),
        "waiting": sum(1 for u in users if u.status == "waiting"),
        "called": sum(1 for u in users if u.status == "called"),
        "served": sum(1 for u in users if u.status == "served"),
        "priority": sum(1 for u in users if u.priority)
    })

# -------------------- ADMIN PAGE --------------------

@app.route("/admin")
def admin():
    users = User.query.order_by(User.token).all()
    return render_template("admin.html", users=users)

# -------------------- RUN APP --------------------

if __name__ == "__main__":
    app.run(debug=True)