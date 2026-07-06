import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(database_url)


def run_sql(cursor, file_name):
    sql = (BASE_DIR / file_name).read_text(encoding="utf-8")
    cursor.execute(sql)


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            run_sql(cursor, "schema.sql")
            run_sql(cursor, "seed.sql")
        connection.commit()


if __name__ == "__main__":
    main()