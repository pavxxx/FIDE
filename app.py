from flask import Flask, render_template, request, redirect, url_for, session
from db_config import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

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

    cursor.execute("""
        SELECT p.fide_id, p.name, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id=r.fide_id
        ORDER BY r.standard_rating DESC
        LIMIT 10
    """)
    top_players = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        total_players=total_players,
        federations=federations,
        gms=gms,
        top_players=top_players
    )
@app.route("/federations")
def federations():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT fed_code,
    COUNT(*) as players,
    AVG(standard_rating) as avg_rating
    FROM ratings
    GROUP BY fed_code
    ORDER BY avg_rating DESC
    LIMIT 20
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("federations.html", data=data)
@app.route("/compare", methods=["GET","POST"])
def compare_players():

    if request.method=="POST":

        p1=request.form["p1"]
        p2=request.form["p2"]

        conn=get_connection()
        cursor=conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT p.name,r.*
        FROM players p
        JOIN ratings r ON p.fide_id=r.fide_id
        WHERE p.fide_id=%s
        """,(p1,))

        player1=cursor.fetchone()

        cursor.execute("""
        SELECT p.name,r.*
        FROM players p
        JOIN ratings r ON p.fide_id=r.fide_id
        WHERE p.fide_id=%s
        """,(p2,))

        player2=cursor.fetchone()

        conn.close()

        return render_template("compare.html",
        p1=player1,
        p2=player2)

    return render_template("compare.html")
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
            return render_template("signup.html", error="Invalid FIDE ID")

        # check username
        cursor.execute("SELECT * FROM player_login WHERE username=%s", (username,))
        if cursor.fetchone():
            conn.close()
            return render_template("signup.html", error="Username already exists")

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO player_login (fide_id, username, password_hash, role)
            VALUES (%s, %s, %s, 'player')
        """, (fide_id, username, hashed_password))

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

        cursor.execute("SELECT * FROM player_login WHERE username=%s", (username,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user["password_hash"], password):

            session["user_id"] = user["login_id"]
            session["fide_id"] = user["fide_id"]

            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("home"))

@app.route("/search_players")
def search_players():

    term = request.args.get("q")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT fide_id,name
    FROM players
    WHERE name LIKE %s
    LIMIT 10
    """, (f"%{term}%",))

    results = cursor.fetchall()

    conn.close()

    return {"players": results}
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
        SELECT p.fide_id, p.name, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        ORDER BY r.standard_rating DESC
        LIMIT 100
    """)

    players = cursor.fetchall()
    conn.close()

    return render_template("rankings.html", players=players)

@app.route("/search")
def search():

    query = request.args.get("q")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.fide_id, p.name, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.name LIKE %s
        ORDER BY r.standard_rating DESC
        LIMIT 50
    """, ("%" + query + "%",))

    players = cursor.fetchall()

    conn.close()

    return render_template("search.html", players=players, query=query)

@app.route("/federation/<fed>")
def federation_players(fed):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.fide_id, p.name, r.standard_rating
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE r.fed_code=%s
        ORDER BY r.standard_rating DESC
        LIMIT 50
    """, (fed,))

    players = cursor.fetchall()

    conn.close()

    return render_template("federation.html", players=players, fed=fed)

@app.route("/api/search")
def api_search():

    q = request.args.get("q")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.fide_id, p.name
        FROM players p
        WHERE p.name LIKE %s
        LIMIT 10
    """, ("%" + q + "%",))

    results = cursor.fetchall()
    conn.close()

    return {"results": results}
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

@app.route("/compare", methods=["GET", "POST"])
def compare():

    if request.method == "POST":
        pid1 = request.form["p1"]
        pid2 = request.form["p2"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM ratings WHERE fide_id=%s", (pid1,))
        p1 = cursor.fetchone()

        cursor.execute("SELECT * FROM ratings WHERE fide_id=%s", (pid2,))
        p2 = cursor.fetchone()

        conn.close()

        return render_template("compare.html", p1=p1, p2=p2)

    return render_template("compare.html")

@app.route("/top10")
def top10():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
      SELECT p.fide_id, p.name, r.standard_rating
      FROM players p
      JOIN ratings r ON p.fide_id=r.fide_id
      ORDER BY r.standard_rating DESC
      LIMIT 10
    """)

    players = cursor.fetchall()
    conn.close()

    return render_template("top10_widget.html", players=players)
# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)