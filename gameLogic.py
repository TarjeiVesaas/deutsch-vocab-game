import random
from dataclasses import dataclass
import pandas as pd

EXCEL_FILE = "AlleLernwortschatze.xlsx"
xl = pd.ExcelFile(EXCEL_FILE)

@dataclass
class Noun:
    word: str
    article: str
    gender: str
    plural: str
    meaning: str


GENDER_MAP = {
    "der": "masculine",
    "die": "feminine",
    "das": "neuter"
}


def pick_random_noun(nouns: list[Noun]) -> Noun:
    return random.choice(nouns)


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


def check_article(noun: Noun, guess: str) -> bool:
    return guess.lower() == noun.article.lower()

