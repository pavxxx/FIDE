from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import get_connection

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"


# ===============================
# PUBLIC HOME PAGE
# ===============================
@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Total players
    cursor.execute("SELECT COUNT(*) AS total FROM players")
    total_players = cursor.fetchone()["total"]

    # Total federations
    cursor.execute("SELECT COUNT(*) AS total FROM federations")
    total_federations = cursor.fetchone()["total"]

    # Active GMs (rating >= 2500 example)
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
# PUBLIC RANKINGS PAGE
# ===============================
@app.route("/rankings")
def rankings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.fide_id, p.name, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        ORDER BY r.standard_rating DESC
        LIMIT 50
    """)

    players = cursor.fetchall()
    conn.close()

    return render_template("rankings.html", players=players)


# ===============================
# PUBLIC PLAYER PROFILE
# ===============================
@app.route("/player/<int:fide_id>")
def player_profile(fide_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.name, p.birth_year, p.sex,
               r.standard_rating, r.rapid_rating, r.blitz_rating,
               r.fed_code
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.fide_id = %s
    """, (fide_id,))

    player = cursor.fetchone()
    conn.close()

    if not player:
        return "Player not found"

    return render_template("player_profile.html", player=player)


# ===============================
# SIGNUP
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        fide_id = request.form["fide_id"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if fide_id exists
        cursor.execute("SELECT * FROM players WHERE fide_id = %s", (fide_id,))
        if not cursor.fetchone():
            conn.close()
            error = "Invalid FIDE ID."
            return render_template("signup.html", error=error)

        # Check if username already exists
        cursor.execute("SELECT * FROM player_login WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            error = "Username already taken."
            return render_template("signup.html", error=error)

        hashed_pw = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO player_login (fide_id, username, password_hash)
            VALUES (%s, %s, %s)
        """, (fide_id, username, hashed_pw))

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
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM player_login WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["fide_id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

        error = "Invalid credentials"

    return render_template("login.html", error=error)


# ===============================
# PLAYER DASHBOARD (PRIVATE)
# ===============================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    fide_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.name, p.birth_year, p.sex,
               r.standard_rating, r.rapid_rating, r.blitz_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.fide_id = %s
    """, (fide_id,))

    player = cursor.fetchone()

    # Dashboard stats
    cursor.execute("SELECT COUNT(*) AS total FROM players")
    total_players = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ratings
        WHERE standard_rating >= 2500
    """)
    active_gms = cursor.fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        player=player,
        total_players=total_players,
        active_gms=active_gms
    )


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
