import pandas as pd
from flask import Flask, request, session
from gameLogic import Noun, pick_random_noun, check_article,EXCEL_FILE,xl
import sqlite3
import time
from datetime import datetime

DB_FILE = "scores.db"

def game_type_html(game_type):
    if game_type == "plural":
        return """
        <form method="post">
            <input type="text" name="plural"
                   placeholder="Plural eingeben"
                   style="font-size:1.5em; padding:12px; border-radius:10px;
                          border:none; text-align:center;">
            <br><br>
            <button type="submit"
                    style="font-size:1.5em; padding:12px 30px;
                           border-radius:10px; border:none;
                           background-color:#f1c40f;">
                Prüfen
            </button>
        </form>
        """
    else:
        return """
        <form method="post">
            <button class="article" name="article" value="der">der</button>
            <button class="article" name="article" value="die">die</button>
            <button class="article" name="article" value="das">das</button>
        </form>
        """


def normalise(text: str) -> str:
    return "".join(text.lower().split())

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            points INTEGER NOT NULL,
            guesses INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            final_time REAL DEFAULT 0,
            sheet_name TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

GENDER_MAP = {
    "der": "masculine",
    "die": "feminine",
    "das": "neuter"
}


def load_nouns(sheet_name: str, ):
    if sheet_name is None:
        sheet_name = xl.sheet_names[0]
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    nouns = []
    for _, row in df.iterrows():
        nouns.append(Noun(
            word=row["Nomen"],
            article=row["Artikel"],
            gender=GENDER_MAP.get(row["Artikel"].lower()),
            plural=str(row["Plural"]),
            meaning=str(row["Übersetzung"])
        ))
    return nouns


# Call it once on startup
init_db()

app = Flask("DeutschA1.1")
app.secret_key = "super-secret-key-for-learning"

sheet_name = "Unit 4"
# TEMPORARY
nouns = load_nouns(sheet_name)

current_noun = pick_random_noun(nouns)


@app.route("/set_name", methods=["GET", "POST"])
def set_name():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            session["player_name"] = name
            # Initialize game session if not done already
            if "points" not in session:
                session["points"] = 0
                session["guesses"] = 0
            return "", 302, {"Location": "/select_game"}
        else:
            feedback = "Bitte gib einen Namen ein!"
    else:
        feedback = ""

    return f"""
    <html>
    <head>
        <title>Deutsch A1.1 - Name eingeben</title>
        <style>
            body {{
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                padding: 50px;
            }}
            input {{
                font-size: 1.5em;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }}
            button {{
                font-size: 1.5em;
                padding: 10px 20px;
                border-radius: 10px;
                margin-top: 20px;
                cursor: pointer;
                background-color: #3498db;
                color: white;
                border: none;
            }}
            button:hover {{ transform: scale(1.05); }}
            .feedback {{ color: #e74c3c; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Willkommen! Wie heißt du?</h1>
        <form method="post">
            <input type="text" name="name" placeholder="Dein Name">
            <br>
            <button type="submit">Start!</button>
        </form>
        <p class="feedback">{feedback}</p>
    </body>
    </html>
    """


@app.route("/select_game", methods=["GET", "POST"])
def select_game():
    if request.method == "POST":
        game_type = request.form.get("game_type")
        if game_type in ["gender", "plural"]:
            session["game_type"] = game_type
            return "", 302, {"Location": "/select_sheet"}

    return """
    <html>
    <head>
        <title>Was möchtest du üben?</title>
        <style>
            body {
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                text-align: center;
                padding: 50px;
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 40px;
            }
            button {
                font-size: 2em;
                padding: 25px 50px;
                margin: 20px;
                border-radius: 20px;
                border: none;
                cursor: pointer;
                transition: transform 0.15s;
            }
            button:hover {
                transform: scale(1.08);
            }
            .gender {
                background: linear-gradient(135deg, #3498db, #9b59b6);
                color: white;
            }
            .plural {
                background: linear-gradient(135deg, #2ecc71, #f1c40f);
                color: black;
            }
        </style>
    </head>
    <body>
        <h1>Was möchtest du üben?</h1>
        <form method="post">
            <button class="gender" name="game_type" value="gender">
                🧠 Artikel
            </button>
            <button class="plural" name="game_type" value="plural">
                🔁 Plural
            </button>
        </form>
    </body>
    </html>
    """


def save_score():
    """Save the current session score to the database."""
    player_name = session.get("player_name")
    sheet_name = session.get("sheet_name", "Unknown")
    points = session.get("points", 0)
    guesses = session.get("guesses", 0)
    accuracy = round((points / guesses) * 100, 1) if guesses > 0 else 0
    final_time = session.get("final_time", 0)  # will be 0 if free practice
    timestamp = datetime.now().isoformat()

    if not player_name:
        return  # nothing to save

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO scores (player_name, points, guesses, accuracy, final_time, sheet_name, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (player_name, points, guesses, accuracy, final_time, sheet_name, timestamp))
    conn.commit()
    conn.close()

@app.route("/select_mode", methods=["GET", "POST"])
def select_mode():
    if request.method == "POST":
        mode = request.form.get("mode")
        if mode in ["practice", "challenge"]:
            session["mode"] = mode
            session["remaining_nouns"] = session["nouns"].copy()
            session["current_noun"] = pick_random_noun(session["remaining_nouns"])

            if mode == "challenge":
                session["start_time"] = time.time()
                session["remaining_nouns"] = session["nouns"].copy()
                session["current_noun"] = pick_random_noun(session["remaining_nouns"])
            return "", 302, {"Location": "/"}

    return f"""
    <html>
    <head>
        <title>Modus wählen</title>
        <style>
            body {{
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                text-align: center;
                padding: 50px;
            }}
            button {{
                font-size: 2em;
                padding: 20px 40px;
                margin: 20px;
                border-radius: 15px;
                border: none;
                cursor: pointer;
            }}
            .practice {{ background-color: #2ecc71; }}
            .challenge {{ background-color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>Wie möchtest du üben?</h1>
        <form method="post">
            <button class="practice" name="mode" value="practice">
                Freies Üben
            </button>
            <button class="challenge" name="mode" value="challenge">
                Herausforderung
            </button>
        </form>
    </body>
    </html>
    """


@app.route("/", methods=["GET", "POST"])
def home():
    game_type = session.get("game_type", "gender")
    mode = session.get("mode", "practice")
    player_name = session.get("player_name")
    REQUIRED_SESSION_KEYS = [
        "player_name",
        "game_type",
        "sheet_name",
        "nouns",
        "mode",
    ]

    for key in REQUIRED_SESSION_KEYS:
        if key not in session:
            session.clear()
            return "", 302, {"Location": "/set_name"}

    if "remaining_nouns" not in session:
        session["remaining_nouns"] = session["nouns"].copy()

    if "current_noun" not in session:
        session["current_noun"] = pick_random_noun(session["remaining_nouns"])

    # Initialize session values (first visit)
    if "points" not in session:
        session["points"] = 0
        session["guesses"] = 0

    if "current_noun" not in session:
        if mode == "challenge":
            session["current_noun"] = pick_random_noun(session["remaining_nouns"])
        else:
            session["current_noun"] = pick_random_noun(session["nouns"])

    current_noun = Noun(**session["current_noun"])
    title_text = (
        f"Was ist der Plural, {player_name}?"
        if game_type == "plural"
        else f"Welcher Artikel, {player_name}?"
    )
    feedback = ""

    # Words left (for challenge mode)
    words_left_text = ""
    if mode == "challenge":
        words_left_text = f"Wörter übrig: {len(session['remaining_nouns'])}"

    # Handle POST (guess submission)
    if request.method == "POST":
        session["guesses"] += 1

        if game_type == "plural":
            guess = request.form.get("plural", "")
            user_answer = normalise(guess)
            correct_answer = normalise(current_noun.plural)

            correct = user_answer == correct_answer

            if correct:
                session["points"] += 1
                feedback = f"✅ Richtig! Die Antwort ist: <strong>{current_noun.plural}</strong>"
            else:
                feedback = f"❌ Falsch. Richtig ist: <strong>{current_noun.plural}</strong>"

            if mode == "challenge":
                session["remaining_nouns"].remove(session["current_noun"])

            if mode == "challenge" and not session["remaining_nouns"]:
                session["final_time"] = round(time.time() - session["start_time"], 1)
                save_score()
                return "", 302, {"Location": "/challenge_result"}

            session["current_noun"] = pick_random_noun(session["remaining_nouns"])
            current_noun = Noun(**session["current_noun"])

        else:
            guess = request.form.get("article", "")
            correct = check_article(current_noun, guess)

            if correct:
                session["points"] += 1
                feedback = f"✅ Richtig! {current_noun.article} {current_noun.word}"
                if mode == "challenge":
                    session["remaining_nouns"].remove(session["current_noun"])
            else:
                feedback = f"❌ Falsch. Richtig ist: {current_noun.article} {current_noun.word}"
                if mode == "challenge":
                    if session["current_noun"] not in session["remaining_nouns"]:
                        session["remaining_nouns"].append(session["current_noun"])
            # Next noun
            if mode == "challenge" and not session["remaining_nouns"]:
                    # Challenge finished — save score
                    session["final_time"] = round(time.time() - session["start_time"], 1)
                    save_score()  # <-- save here only
                    return "", 302, {"Location": "/challenge_result"}
            else:
                session["current_noun"] = pick_random_noun(session["remaining_nouns"])

            current_noun = Noun(**session["current_noun"])

    accuracy = (
        round((session["points"] / session["guesses"]) * 100, 1)
        if session["guesses"] > 0 else 0
    )
    # Timer JS for challenge mode
    timer_script = ""
    if mode == "challenge":
        timer_script = f"""
        <div id="timer" style="position:fixed; top:20px; left:20px; font-size:1.5em; color:white;">
            ⏱️ 00:00:00
        </div>
        <script>
            const startTime = """ + str(session['start_time']) + """;
        
            function updateTimer() {
                let elapsed = Math.floor(Date.now()/1000 - startTime);
                let hours = Math.floor(elapsed / 3600).toString().padStart(2,'0');
                let minutes = Math.floor((elapsed % 3600)/60).toString().padStart(2,'0');
                let seconds = (elapsed % 60).toString().padStart(2,'0');
                document.getElementById('timer').textContent = `⏱️ ${hours}:${minutes}:${seconds}`;
            }
        
            setInterval(updateTimer, 1000);
            updateTimer();
        </script>
        """

    # CSS
    style = """
        <style>
            body {
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                padding: 50px;
            }
            h1 { font-size: 2.5em; margin-bottom: 20px; }
            button.article {
                font-size: 1.5em;
                margin: 10px;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
                cursor: pointer;
                transition: transform 0.1s;
            }
            .noun-word {
                font-size: 3.2em;
                font-weight: 800;
                margin: 30px 0;
                color: #f1c40f;
                text-shadow:
                    0 0 10px rgba(241, 196, 15, 0.6),
                    0 0 25px rgba(241, 196, 15, 0.4);
            }
            button.article:hover { transform: scale(1.1); }
            button.article[value="der"] { background-color: #3498db; color: white; }
            button.article[value="die"] { background-color: #e74c3c; color: white; }
            button.article[value="das"] { background-color: #2ecc71; color: white; }
            .feedback { font-size: 1.3em; margin: 20px 0; }
            .score { margin-top: 30px; font-size: 1.2em; }
            .restart {
                position: fixed;
                top: 20px;
                right: 20px;
                font-size: 2em;
                color: #ffffff;
                text-decoration: none;
            }
            .restart:hover { color: #e74c3c; }
        </style>
        """

    # Full HTML
    return f"""
        <html>
        <head>
            <title>German Articles Game</title>
            {style}
        </head>
        <body>
            {timer_script}
            <a href="/reset" class="restart">✖</a>
            <h1>{title_text}</h1>
            <p class="noun-word">{current_noun.word}</p>
            {game_type_html(game_type)}
            <p class="feedback">{feedback}</p>
        """


@app.route("/challenge_result")
def challenge_result():
    time_taken = session.get("final_time", 0)
    if float(time_taken) > 60:
        minutes_taken = str(int(float(time_taken) // 60))
        seconds_taken = int(float(time_taken) - float(minutes_taken) * 60)
        time_message = f"{minutes_taken} Minuten und {seconds_taken} Sekunden"
    else:
        time_message = f"{int(time_taken)} Sekunden"
    name = session.get("player_name", "")
    unit = session.get("sheet_name", "")

    return f"""
    <html>
    <head>
        <title>Ergebnis</title>
        <style>
            body {{
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                text-align: center;
                padding: 50px;
            }}
        </style>
    </head>
    <body>
        <h1>🎉 Geschafft, {name}!</h1>
        <h2>Unit: <strong>{unit}</strong>
        <p style="font-size:2em;">Zeit: <strong>{time_message}</strong></p>
        <a href="/full_reset" style="color:#3498db;">Nochmal spielen</a>
    </body>
    </html>
    """


@app.route("/reset")
def reset():
    # Clear session but keep player name so they don’t have to re-enter it
    player_name = session.get("player_name")
    session.clear()
    if player_name:
        session["player_name"] = player_name

    return "", 302, {"Location": "/select_sheet"}


@app.route("/full_reset")
def full_reset():
    session.clear()
    return "", 302, {"Location": "/set_name"}


@app.route("/scores")
def scores():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT player_name, points, guesses, accuracy, timestamp FROM scores ORDER BY accuracy DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    rows_html = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}%</td><td>{r[4][:19]}</td></tr>"
        for r in rows
    )

    return f"""
    <html>
    <head>
        <title>High Scores</title>
        <style>
            body {{
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                padding: 50px;
            }}
            table {{
                margin: auto;
                border-collapse: collapse;
                width: 80%;
            }}
            th, td {{
                border: 1px solid #ffffff;
                padding: 10px;
            }}
            th {{
                background-color: #3498db;
            }}
        </style>
    </head>
    <body>
        <h1>Top Scores</h1>
        <table>
            <tr><th>Name</th><th>Punkte</th><th>Versuche</th><th>Genauigkeit</th><th>Datum</th></tr>
            {rows_html}
        </table>
        <p><a href="/">Zurück zum Spiel</a></p>
    </body>
    </html>
    """


@app.route("/select_sheet", methods=["GET", "POST"])
def select_sheet():
    xl = pd.ExcelFile(EXCEL_FILE)
    sheets = xl.sheet_names

    if request.method == "POST":
        choice = request.form.get("sheet")
        if choice in sheets:
            session["sheet_name"] = choice
            # Load nouns for this sheet
            session["nouns"] = [n.__dict__ for n in load_nouns(choice)]
            # Initialize first noun
            session["current_noun"] = pick_random_noun(session["nouns"])
            # Reset score and guesses
            session["points"] = 0
            session["guesses"] = 0
            return "", 302, {"Location": "/select_mode"}  # go to select mode
        else:
            feedback = "Bitte wähle einen gültigen Wortschatz aus!"
    else:
        feedback = ""

    # Build sheet buttons and leaderboards
    sheet_html = ""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    for sheet in sheets:
        # Sheet button
        sheet_html += f"""
        <div class="sheet-card">
            <h2>{sheet}</h2>
            <form method="post">
                <button type="submit" name="sheet" value="{sheet}">
                    📘 {sheet}
                </button>
            </form>
        """

        # Leaderboard for this sheet (challenge mode only)
        c.execute("""
            SELECT player_name, final_time, accuracy
            FROM scores
            WHERE sheet_name = ?
            ORDER BY final_time ASC
            LIMIT 3
        """, (sheet,))
        rows = c.fetchall()

        if rows:
            sheet_html += "<div class='leaderboard'>"
            sheet_html += "<div class='leaderboard-title'>🏆 LEADERBOARD</div><ul>"
            for r in rows:
                name = r[0]
                total_seconds = int(r[1])
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                accuracy = r[2]
                sheet_html += f"<li>{name} – {minutes}m {seconds}s ({accuracy}%)</li>"
            sheet_html += "</ul></div>"
        else:
            sheet_html += "<div class='leaderboard'><em>No scores yet</em></div>"

        sheet_html += "</div>"

    conn.close()

    return f"""
    <html>
    <head>
        <title>Wortschatz wählen</title>
        <style>
            body {{
                background: radial-gradient(circle at top, #1e1e2f, #121212);
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                text-align: center;
                padding: 40px;
            }}
    
            h1 {{
                font-size: 2.6em;
                margin-bottom: 40px;
            }}
    
            h2 {{
                margin-top: 30px;
                font-size: 1.8em;
                color: #f1c40f;
            }}
    
            .sheet-card {{
                background: linear-gradient(145deg, #1f2937, #111827);
                border-radius: 20px;
                padding: 25px;
                margin: 25px auto;
                width: 70%;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            }}
    
            .sheet-card button {{
                font-size: 1.4em;
                padding: 15px 40px;
                border-radius: 15px;
                border: none;
                cursor: pointer;
                background: linear-gradient(135deg, #3498db, #9b59b6);
                color: white;
                transition: transform 0.15s;
                margin-top: 10px;
            }}
    
            .sheet-card button:hover {{
                transform: scale(1.08);
            }}
    
            .leaderboard {{
                margin-top: 20px;
                background-color: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 15px;
            }}
    
            .leaderboard-title {{
                font-weight: bold;
                color: #2ecc71;
                margin-bottom: 10px;
            }}
    
            ul {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
    
            li {{
                margin: 6px 0;
                font-size: 1.1em;
            }}
        
            .restart {{
                position: fixed;
                top: 20px;
                right: 20px;
                font-size: 2em;
                color: white;
                text-decoration: none;
            }}
        
            .restart:hover {{color: #e74c3c;}}
        </style>

    </head>
    <body>
        <a href="/full_reset" class="restart">✖</a>
        <h1>{session.get('player_name', '')}, welchen Wortschatz möchtest du üben?</h1>
        {sheet_html}
        <p class="feedback">{feedback}</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)