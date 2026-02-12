from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import get_connection

app = Flask(__name__)
app.secret_key = "change_this_secret_key"


# ===============================
# HOME
# ===============================
@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM players")
    total_players = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM federations")
    total_federations = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ratings
        WHERE standard_rating >= 2500
    """)
    active_gms = cursor.fetchone()["total"]

    conn.close()

    return render_template(
        "home.html",
        total_players=total_players,
        total_federations=total_federations,
        active_gms=active_gms
    )


# ===============================
# SIGNUP
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        fide_id = request.form.get("fide_id")
        username = request.form.get("username")
        password = request.form.get("password")

        if not fide_id or not username or not password:
            return render_template("signup.html", error="All fields required")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if FIDE ID exists
        cursor.execute("SELECT * FROM players WHERE fide_id = %s", (fide_id,))
        player_exists = cursor.fetchone()

        if not player_exists:
            conn.close()
            return render_template("signup.html", error="Invalid FIDE ID")

        # Check username uniqueness
        cursor.execute("SELECT * FROM player_login WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            return render_template("signup.html", error="Username already taken")

        # Hash password properly
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO player_login (fide_id, username, password_hash)
            VALUES (%s, %s, %s)
        """, (fide_id, username, hashed_password))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html", error=error)


# ===============================
# LOGIN
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM player_login WHERE username = %s", (username,))
        user = cursor.fetchone()

        conn.close()

        if not user:
            return render_template("login.html", error="User not found")

        # Check password correctly
        if check_password_hash(user["password_hash"], password):
            session["user_id"] = user["fide_id"]
            session["username"] = user["username"]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid password")

    return render_template("login.html", error=error)


# ===============================
# DASHBOARD
# ===============================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    fide_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.name,
               r.standard_rating,
               r.rapid_rating,
               r.blitz_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.fide_id = %s
    """, (fide_id,))

    player = cursor.fetchone()
    conn.close()

    return render_template("dashboard.html", player=player)


# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
