from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import get_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fide_id = request.form["fide_id"]
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO player_login (fide_id, username, password_hash) VALUES (%s, %s, %s)",
                (fide_id, username, hashed_pw),
            )
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect("/login")

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM player_login WHERE username=%s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user"] = username
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user"])


# ---------------- PLAYERS LIST ----------------
@app.route("/players")
def players():
    if "user" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.name, r.fed_code, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        ORDER BY r.standard_rating DESC
        LIMIT 50;
    """

    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    return render_template("players.html", players=data)


# ---------------- TOP 10 ----------------
@app.route("/top")
def top():
    if "user" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.name, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        ORDER BY r.standard_rating DESC
        LIMIT 10;
    """

    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    return render_template("top.html", players=data)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
