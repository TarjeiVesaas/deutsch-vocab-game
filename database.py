import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)

def get_connection():
    return psycopg2.connect(DATABASE_URL)
