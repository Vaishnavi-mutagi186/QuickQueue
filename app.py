from flask import Flask, render_template, request, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "queue.json"

# -------------------- DATA HANDLING --------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"services": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------- CORE LOGIC --------------------

def get_next_token(queue):
    if not queue:
        return 1
    return max(user["token"] for user in queue) + 1

def sort_queue(queue):
    # Priority first, then by token (fair ordering)
    return sorted(queue, key=lambda x: (not x["priority"], x["token"]))

def calculate_wait_time(queue):
    BASE_TIME = 5  # minutes per person

    for i, user in enumerate(queue):
        multiplier = 0.5 if user["priority"] else 1
        user["waiting"] = int(i * BASE_TIME * multiplier)
        user["people_ahead"] = i

    return queue

# -------------------- ROUTES --------------------

@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()

    if request.method == "POST":
        name = request.form["name"]
        service = request.form["service"]
        priority = request.form.get("priority") == "on"

        if service not in data["services"]:
            data["services"][service] = []

        queue = data["services"][service]

        token_number = get_next_token(queue)

        new_user = {
            "name": name,
            "service": service,
            "token": token_number,
            "priority": priority,
            "time_joined": datetime.now().strftime("%H:%M:%S")
        }

        queue.append(new_user)

        # Smart sorting
        queue = sort_queue(queue)

        data["services"][service] = queue
        save_data(data)

        return redirect("/")

    # Process all queues
    for service in data["services"]:
        queue = data["services"][service]
        queue = sort_queue(queue)
        queue = calculate_wait_time(queue)
        data["services"][service] = queue

    return render_template("index.html", services=data["services"])

# -------------------- ADMIN --------------------

@app.route("/serve/<service>")
def serve(service):
    data = load_data()

    if service in data["services"] and data["services"][service]:
        served = data["services"][service].pop(0)
        print(f"Served: {served['name']} (Token {served['token']})")

    save_data(data)
    return redirect("/")

# -------------------- RESET (BONUS) --------------------

@app.route("/reset")
def reset():
    save_data({"services": {}})
    return redirect("/")

# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run(debug=True)