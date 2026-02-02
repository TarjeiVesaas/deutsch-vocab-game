import pandas as pd
from flask import Flask, request, session
from gameLogic import Noun, pick_random_noun, check_article,EXCEL_FILE,xl
import sqlite3
from datetime import datetime

DB_FILE = "scores.db"
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


# Make sure the table exists
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
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


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
            return "", 302, {"Location": "/select_sheet"}
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


def save_score(name, points, guesses):
    accuracy = round((points / guesses) * 100, 1) if guesses > 0 else 0
    timestamp = datetime.now().isoformat()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO scores (player_name, points, guesses, accuracy, timestamp) VALUES (?, ?, ?, ?, ?)",
        (name, points, guesses, accuracy, timestamp)
    )
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def home():
    player_name = session.get("player_name")
    if "player_name" not in session:
        return "", 302, {"Location": "/set_name"}

    if "nouns" not in session:
        return "", 302, {"Location": "/select_sheet"}

    # Initialize session values (first visit)
    if "points" not in session:
        session["points"] = 0
        session["guesses"] = 0

    if "current_noun" not in session:
            session["current_noun"] = pick_random_noun(session["nouns"]).__dict__

    feedback = ""
    current_noun = Noun(**session["current_noun"])

    if request.method == "POST":
        guess = request.form["article"]
        session["guesses"] += 1

        if check_article(current_noun, guess):
            session["points"] += 1
            feedback = "✅ Richtig!"
        else:
            feedback = f"❌ Falsch. Richtig ist: {current_noun.article} {current_noun.word}"

        session["current_noun"] = pick_random_noun(session["nouns"])
        current_noun = Noun(**session["current_noun"])

    accuracy = (
        round((session["points"] / session["guesses"]) * 100, 1)
        if session["guesses"] > 0 else 0
    )

    # CSS styling
    style = """<style>
    body {
        background-color: #121212; /* nice dark background */
        color: #ffffff; /* white text */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding: 50px;
    }

    h1 {
        font-size: 2.5em;
        margin-bottom: 20px;
    }

    button {
        font-size: 1.5em;
        margin: 10px;
        padding: 15px 30px;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        transition: transform 0.1s;
    }

    button:hover {
        transform: scale(1.1);
    }

    button[value="der"] { background-color: #3498db; color: white; }
    button[value="die"] { background-color: #e74c3c; color: white; }
    button[value="das"] { background-color: #2ecc71; color: white; }

    .feedback {
        font-size: 1.3em;
        margin: 20px 0;
    }

    .score {
        margin-top: 30px;
        font-size: 1.2em;
    }

    .restart {
        position: fixed;
        top: 20px;
        right: 20px;
        font-size: 2em;
        color: #ffffff;
        text-decoration: none;
    }

    .restart:hover {
        color: #e74c3c;
    }
</style>"""

    # Full HTML
    return f"""
    <html>
    <head>
        <title>German Articles Game</title>
        {style}
    </head>
    <body>
        <a href="/reset" class="restart">✖</a>

        <h1>Welcher Artikel, <h1>{player_name}?</h1>

        <p style="font-size:2em;"><strong>{current_noun.word}</strong></p>

        <form method="post">
            <button name="article" value="der">der</button>
            <button name="article" value="die">die</button>
            <button name="article" value="das">das</button>
        </form>

        <p class="feedback">{feedback}</p>

        <div class="score">
            <p>Punkte: {session["points"]}</p>
            <p>Versuche: {session["guesses"]}</p>
            <p>Genauigkeit: {accuracy}%</p>
        </div>
    </body>
    </html>
    """


@app.route("/reset")
def reset():
    # Save current score before resetting
    player_name = session.get("player_name")
    if player_name and "points" in session and "guesses" in session:
        save_score(player_name, session["points"], session["guesses"])

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
            return "", 302, {"Location": "/"}  # go to game
        else:
            feedback = "Bitte wähle einen gültigen Wortschatz aus!"
    else:
        feedback = ""

    # Build HTML options
    options_html = "".join(
        f'<button type="submit" name="sheet" value="{sheet}">{sheet}</button>'
        for sheet in sheets
    )

    return f"""
    <html>
    <head>
        <title>Wortschatz wählen</title>
        <style>
            body {{
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                padding: 50px;
            }}
            button {{
                font-size: 1.5em;
                padding: 15px 30px;
                margin: 10px;
                border-radius: 10px;
                border: none;
                cursor: pointer;
                transition: transform 0.1s;
            }}
            button:hover {{ transform: scale(1.05); }}
            .feedback {{ color: #e74c3c; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>{session.get('player_name', '')}, welchen Wortschatz möchtest du üben?</h1>
        <form method="post">
            {options_html}
        </form>
        <p class="feedback">{feedback}</p>
    </body>
    </html>
    """

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
