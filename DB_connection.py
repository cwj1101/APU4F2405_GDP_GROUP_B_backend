import os
import psycopg2
from flask import Blueprint

# Define the blueprint
DB_connection = Blueprint("DB_connection", __name__, static_folder="static")


def get_db_connection():
    """
    Establishes and returns a new database connection using the DATABASE_URL from the environment.
    This should be used within an app context.
    """
    url = os.getenv("DATABASE_URL")

    try:
        conn = psycopg2.connect(url)
        print("DB connected")
        return conn
    except psycopg2.Error as e:
        print("Error from psycopg2", e)
        return None
