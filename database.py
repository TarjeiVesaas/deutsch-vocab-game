import psycopg2
import os

DATABASE_URL = os.environ.get("postgresql://db_users_scores_user:OshPNsIguxJLk2lxpGpP8BqjVCUHJEcD@dpg-d7ub750sfn5c73fhvco0-a/db_users_scores")

def get_connection():
    return psycopg2.connect(DATABASE_URL)