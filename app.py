import os
from flask import Flask, render_template, request, redirect, url_for, session
from db_config import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_dev_key")

# Jinja2 filter: federation code → flag emoji
_FLAG_MAP = {
    "RUS": "🇷🇺", "USA": "🇺🇸", "CHN": "🇨🇳", "IND": "🇮🇳", "AZE": "🇦🇿",
    "ARM": "🇦🇲", "GEO": "🇬🇪", "UKR": "🇺🇦", "NED": "🇳🇱", "GER": "🇩🇪",
    "POL": "🇵🇱", "HUN": "🇭🇺", "CZE": "🇨🇿", "SRB": "🇷🇸", "ESP": "🇪🇸",
    "FRA": "🇫🇷", "ITA": "🇮🇹", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "SWE": "🇸🇪", "NOR": "🇳🇴",
    "DEN": "🇩🇰", "FIN": "🇫🇮", "ISR": "🇮🇱", "TUR": "🇹🇷", "IRN": "🇮🇷",
    "EGY": "🇪🇬", "BRA": "🇧🇷", "ARG": "🇦🇷", "CUB": "🇨🇺", "MEX": "🇲🇽",
    "KAZ": "🇰🇿", "UZB": "🇺🇿", "AUS": "🇦🇺", "CAN": "🇨🇦", "BEL": "🇧🇪",
    "AUT": "🇦🇹", "POR": "🇵🇹", "ROU": "🇷🇴", "BUL": "🇧🇬", "SVK": "🇸🇰",
    "CRO": "🇭🇷", "LAT": "🇱🇻", "LTU": "🇱🇹", "EST": "🇪🇪", "BLR": "🇧🇾",
    "GRE": "🇬🇷", "SLO": "🇸🇮", "VIE": "🇻🇳", "PHI": "🇵🇭", "RSA": "🇿🇦",
}

@app.template_filter("fed_flag")
def fed_flag(code):
    return _FLAG_MAP.get(code, "🏳")


# ===============================
# HOME PAGE
# ===============================
@app.route("/")
def home():

    # Lat/Lng for major FIDE federation codes
    FED_COORDS = {
        "RUS": (61.5, 105.3), "USA": (37.1, -95.7), "CHN": (35.9, 104.2),
        "IND": (20.6, 78.9), "AZE": (40.1, 47.6), "ARM": (40.1, 45.0),
        "GEO": (42.3, 43.4), "UKR": (48.4, 31.2), "NED": (52.1, 5.3),
        "GER": (51.2, 10.5), "POL": (52.1, 19.1), "HUN": (47.2, 19.5),
        "CZE": (49.8, 15.5), "SRB": (44.0, 21.0), "ESP": (40.5, -3.7),
        "FRA": (46.2, 2.2), "ITA": (41.9, 12.6), "ENG": (52.4, -1.9),
        "SWE": (60.1, 18.6), "NOR": (60.5, 8.5), "DEN": (56.3, 9.5),
        "FIN": (61.9, 25.7), "ISR": (31.0, 34.9), "TUR": (38.9, 35.2),
        "IRN": (32.4, 53.7), "EGY": (26.8, 30.8), "BRA": (-14.2, -51.9),
        "ARG": (-38.4, -63.6), "CUB": (21.5, -80.0), "MEX": (23.6, -102.6),
        "VEN": (6.4, -66.6), "COL": (4.6, -74.1), "PER": (-9.2, -75.0),
        "KAZ": (48.0, 66.9), "UZB": (41.4, 64.6), "MNG": (46.9, 103.8),
        "VIE": (14.1, 108.3), "PHI": (12.9, 121.8), "BAN": (23.7, 90.4),
        "PAK": (30.4, 69.3), "SRI": (7.9, 80.7), "NIG": (9.1, 8.7),
        "RSA": (-30.6, 22.9), "AUS": (-25.3, 133.8), "CAN": (56.1, -106.3),
        "BEL": (50.5, 4.5), "AUT": (47.5, 14.6), "POR": (39.4, -8.2),
        "GRE": (39.1, 21.8), "ROU": (45.9, 24.9), "BUL": (42.7, 25.5),
        "SVK": (48.7, 19.7), "SLO": (46.2, 14.9), "CRO": (45.1, 15.2),
        "BIH": (43.9, 17.7), "LAT": (56.9, 24.6), "LTU": (55.2, 23.9),
        "EST": (58.6, 25.0), "BLR": (53.7, 27.9), "MKD": (41.6, 21.7),
        "ALB": (41.2, 20.2), "KGZ": (41.2, 74.8), "TAJ": (38.9, 71.3),
        "TKM": (38.9, 59.6), "MON": (43.7, 7.4), "ISL": (64.9, -18.0),
        "IRL": (53.1, -8.2), "MLT": (35.9, 14.4), "CYP": (35.1, 33.4),
    }

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

    cursor.execute("""
        SELECT fed_code, COUNT(*) as player_count, ROUND(AVG(standard_rating)) as avg_rating
        FROM ratings
        WHERE fed_code IS NOT NULL AND fed_code != ''
        GROUP BY fed_code
        ORDER BY player_count DESC
    """)
    raw_feds = cursor.fetchall()
    conn.close()

    # Merge with coordinates, skip unknown feds
    fed_data = []
    for row in raw_feds:
        code = row["fed_code"]
        if code in FED_COORDS:
            lat, lng = FED_COORDS[code]
            fed_data.append({
                "code": code,
                "lat": lat,
                "lng": lng,
                "count": row["player_count"],
                "avg": int(row["avg_rating"] or 0)
            })

    return render_template(
        "index.html",
        total_players=total_players,
        federations=federations,
        gms=gms,
        top_players=top_players,
        fed_data=fed_data
    )
@app.route("/federations")
def federations():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        r.fed_code,
        COUNT(*) AS players,
        ROUND(AVG(r.standard_rating)) AS avg_rating,
        SUM(CASE WHEN r.title_code = 'GM' THEN 1 ELSE 0 END) AS gm_count
    FROM ratings r
    WHERE r.fed_code IS NOT NULL AND r.fed_code != ''
    GROUP BY r.fed_code
    ORDER BY avg_rating DESC
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

        user_id = request.form["user_id"]
        password = request.form["password"]
        role = request.form.get("role", "player")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if role == "admin":
            # Admin signup logic
            cursor.execute("SELECT * FROM admin WHERE username=%s", (user_id,))
            if cursor.fetchone():
                conn.close()
                return render_template("signup.html", error="Admin Username already exists")

            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO admin (username, password_hash) VALUES (%s, %s)", (user_id, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))

        else:
            # check if fide id exists
            cursor.execute("SELECT fide_id FROM players WHERE fide_id=%s", (user_id,))
            player = cursor.fetchone()

            if not player:
                conn.close()
                return render_template("signup.html", error="User ID (FIDE ID) not found")

            # check username
            cursor.execute("SELECT * FROM player_login WHERE fide_id=%s", (user_id,))
            if cursor.fetchone():
                conn.close()
                return render_template("signup.html", error="User ID already registered")

            hashed_password = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO player_login (fide_id, username, password_hash, role)
                VALUES (%s, %s, %s, 'player')
            """, (user_id, user_id, hashed_password))

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

        user_id = request.form["user_id"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # First, check if it's an admin logging in
        cursor.execute("SELECT * FROM admin WHERE username=%s", (user_id,))
        admin_user = cursor.fetchone()

        if admin_user and check_password_hash(admin_user["password_hash"], password):
            session["user_id"] = admin_user["admin_id"]
            session["role"] = "admin"
            conn.close()
            return redirect(url_for("admin_dashboard"))

        # If not an admin, check player_login
        cursor.execute("SELECT * FROM player_login WHERE fide_id=%s", (user_id,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user["password_hash"], password):

            session["user_id"] = user["fide_id"]
            session["fide_id"] = user["fide_id"]
            session["role"] = user["role"]

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
        SELECT p.name, p.birth_year, p.sex,
               r.standard_rating, r.rapid_rating, r.blitz_rating,
               r.standard_games, r.rapid_games, r.blitz_games,
               r.fed_code, r.title_code
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        WHERE p.fide_id = %s
    """, (fide_id,))
    player = cursor.fetchone()

    # Global rank: how many players have a higher standard rating
    if player and player["standard_rating"]:
        cursor.execute("""
            SELECT COUNT(*) + 1 AS rank_position
            FROM ratings
            WHERE standard_rating > %s
        """, (player["standard_rating"],))
        rank_row = cursor.fetchone()
        global_rank = rank_row["rank_position"] if rank_row else "N/A"
    else:
        global_rank = "N/A"

    conn.close()

    return render_template("dashboard.html", player=player, global_rank=global_rank, fide_id=fide_id)


# ===============================
# GLOBAL RANKINGS
# ===============================
@app.route("/rankings")
def rankings():

    fed_filter  = request.args.get("fed", "")
    title_filter = request.args.get("title", "")
    sort_by     = request.args.get("sort", "standard")

    # Whitelist sort column
    sort_col_map = {
        "standard": "r.standard_rating",
        "rapid":    "r.rapid_rating",
        "blitz":    "r.blitz_rating",
    }
    sort_col = sort_col_map.get(sort_by, "r.standard_rating")

    conditions = []
    params     = []

    if fed_filter:
        conditions.append("r.fed_code = %s")
        params.append(fed_filter)
    if title_filter:
        conditions.append("r.title_code = %s")
        params.append(title_filter)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"""
        SELECT p.fide_id, p.name,
               r.standard_rating, r.rapid_rating, r.blitz_rating,
               r.fed_code, r.title_code
        FROM players p
        JOIN ratings r ON p.fide_id = r.fide_id
        {where_clause}
        ORDER BY {sort_col} DESC
        LIMIT 200
    """, params)
    players = cursor.fetchall()

    # Dropdown options
    cursor.execute("SELECT DISTINCT fed_code FROM ratings WHERE fed_code IS NOT NULL AND fed_code != '' ORDER BY fed_code")
    feds = [row["fed_code"] for row in cursor.fetchall()]

    titles = ["GM", "WGM", "IM", "WIM", "FM", "WFM", "CM", "WCM"]

    conn.close()

    return render_template(
        "rankings.html",
        players=players,
        feds=feds,
        titles=titles,
        selected_fed=fed_filter,
        selected_title=title_filter,
        selected_sort=sort_by
    )

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

        query = """
            SELECT p.fide_id, p.name,
                   r.standard_rating, r.rapid_rating, r.blitz_rating,
                   r.standard_games, r.rapid_games, r.blitz_games,
                   r.fed_code, r.title_code
            FROM players p
            JOIN ratings r ON p.fide_id = r.fide_id
            WHERE p.fide_id = %s
        """

        cursor.execute(query, (pid1,))
        p1 = cursor.fetchone()

        cursor.execute(query, (pid2,))
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
# ADMIN MODULE
# ===============================
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("home"))
    
    page = request.args.get('page', 1, type=int)
    per_page = 100
    offset = (page - 1) * per_page
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get total count for pagination
    cursor.execute("SELECT COUNT(*) as total FROM players")
    total_players = cursor.fetchone()['total']
    total_pages = (total_players + per_page - 1) // per_page
    
    cursor.execute("""
        SELECT p.fide_id, p.name, p.sex, r.fed_code AS fed, r.standard_rating 
        FROM players p 
        LEFT JOIN ratings r ON p.fide_id = r.fide_id
        ORDER BY p.fide_id ASC LIMIT %s OFFSET %s
    """, (per_page, offset))
    players = cursor.fetchall()
    conn.close()
    
    return render_template("admin_dashboard.html", players=players, page=page, total_pages=total_pages)

@app.route("/admin/add_player", methods=["GET", "POST"])
def add_player():
    if session.get("role") != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":
        fide_id = request.form["fide_id"]
        name = request.form["name"]
        fed = request.form["fed"]
        sex = request.form["sex"]
        
        birth_year = request.form.get("birth_year", "")
        birth_year = int(birth_year) if birth_year.strip() else None
        
        std_rating = request.form.get("std_rating", "")
        std_rating = int(std_rating) if str(std_rating).strip() else 0
        
        std_games = request.form.get("std_games", "")
        std_games = int(std_games) if str(std_games).strip() else 0
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO players (fide_id, name, sex, birth_year)
                VALUES (%s, %s, %s, %s)
            """, (fide_id, name, sex, birth_year))
            
            cursor.execute("""
                INSERT INTO ratings (fide_id, standard_rating, standard_games, fed_code)
                VALUES (%s, %s, %s, %s)
            """, (fide_id, std_rating, std_games, fed))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            return render_template("add_player.html", error=str(e))
        finally:
            conn.close()
            
        return redirect(url_for("admin_dashboard"))

    return render_template("add_player.html")

@app.route("/admin/edit_player/<int:fide_id>", methods=["GET", "POST"])
def edit_player(fide_id):
    if session.get("role") != "admin":
        return redirect(url_for("home"))
        
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == "POST":
        name = request.form["name"]
        fed = request.form["fed"]
        sex = request.form["sex"]
        
        birth_year = request.form.get("birth_year", "")
        birth_year = int(birth_year) if birth_year.strip() else None
        
        std_rating = request.form.get("std_rating", "")
        std_rating = int(std_rating) if str(std_rating).strip() else 0
        
        std_games = request.form.get("std_games", "")
        std_games = int(std_games) if str(std_games).strip() else 0
        
        title_code = request.form.get("title_code", "")
        if not title_code.strip():
            title_code = None
        
        try:
            cursor.execute("""
                UPDATE players SET name=%s, sex=%s, birth_year=%s
                WHERE fide_id=%s
            """, (name, sex, birth_year, fide_id))
            
            # Check if rating exists
            cursor.execute("SELECT fide_id FROM ratings WHERE fide_id=%s", (fide_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE ratings SET standard_rating=%s, standard_games=%s, fed_code=%s, title_code=%s
                    WHERE fide_id=%s
                """, (std_rating, std_games, fed, title_code, fide_id))
            else:
                cursor.execute("""
                    INSERT INTO ratings (fide_id, standard_rating, standard_games, fed_code, title_code)
                    VALUES (%s, %s, %s, %s, %s)
                """, (fide_id, std_rating, std_games, fed, title_code))
                
            conn.commit()
            conn.close()
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            conn.rollback()
            # If an error happens, we re-fetch the player so the template has context to display
            pass
        
    cursor.execute("""
        SELECT p.*, r.standard_rating, r.standard_games, r.title_code 
        FROM players p LEFT JOIN ratings r ON p.fide_id=r.fide_id WHERE p.fide_id=%s
    """, (fide_id,))
    player = cursor.fetchone()
    conn.close()
    
    return render_template("edit_player.html", player=player)


# ===============================
# ERROR HANDLERS
# ===============================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                admin_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Startup DB check error: {e}")

    app.run(debug=True)