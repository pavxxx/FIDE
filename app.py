from flask import Flask, render_template, request, redirect, url_for, session
from db_config import get_connection

app = Flask(__name__)
app.secret_key = "super_secret_key"


# ===============================
# HOME PAGE
# ===============================
@app.route("/")
def home():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM players")
    total_players = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT fed_code) as total FROM ratings")
    federations = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM ratings WHERE title_code='GM'")
    gms = cursor.fetchone()["total"]

    conn.close()

    return render_template(
        "index.html",
        total_players=total_players,
        federations=federations,
        gms=gms
    )


# ===============================
# SIGNUP
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        fide_id = request.form["fide_id"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # check if fide id exists
        cursor.execute("SELECT fide_id FROM players WHERE fide_id=%s", (fide_id,))
        player = cursor.fetchone()

        if not player:
            conn.close()
            return "Invalid FIDE ID"

        # check if username exists
        cursor.execute("SELECT * FROM player_login WHERE username=%s", (username,))
        if cursor.fetchone():
            conn.close()
            return "Username already exists"

        # insert login
        cursor.execute("""
            INSERT INTO player_login (fide_id, username, password_hash, role)
            VALUES (%s, %s, %s, 'player')
        """, (fide_id, username, password))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# ===============================
# LOGIN
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM player_login
            WHERE username=%s AND password_hash=%s
        """, (username, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["login_id"]
            session["fide_id"] = user["fide_id"]

            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")


# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("home"))


# ===============================
# DASHBOARD
# ===============================
@app.route("/dashboard")
def dashboard():

    if "fide_id" not in session:
        return redirect(url_for("login"))

    fide_id = session["fide_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.name,
               r.standard_rating,
               r.rapid_rating,
               r.blitz_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.fide_id=%s
    """, (fide_id,))

    player = cursor.fetchone()
    conn.close()

    return render_template("dashboard.html", player=player)


# ===============================
# GLOBAL RANKINGS
# ===============================
@app.route("/rankings")
def rankings():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.fide_id, p.name, r.standard_rating, r.fed_code
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        ORDER BY r.standard_rating DESC
        LIMIT 100
    """)

    players = cursor.fetchall()
    conn.close()

    return render_template("rankings.html", players=players)


# ===============================
# PLAYER PROFILE
# ===============================
@app.route("/player/<int:fide_id>")
def player_profile(fide_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.name, p.fide_id, p.birth_year, p.sex,
               r.standard_rating, r.rapid_rating, r.blitz_rating,
               r.standard_games, r.rapid_games, r.blitz_games,
               r.fed_code, r.title_code
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.fide_id = %s
    """, (fide_id,))

    player = cursor.fetchone()
    conn.close()

    return render_template("player_profile.html", player=player)


# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)