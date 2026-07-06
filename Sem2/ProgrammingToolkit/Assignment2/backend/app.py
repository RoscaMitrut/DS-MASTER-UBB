import json
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify
from psycopg2.extras import RealDictCursor


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(database_url)


def to_python_json(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def fetch_one(query):
    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            return cursor.fetchone()


@app.get("/api/personal")
def get_personal_data():
    row = fetch_one(
        """
        SELECT
            name,
            title,
            date_of_birth,
            location,
            email,
            phone,
            places_lived,
            languages,
            social_github,
            social_linkedin
        FROM personal_data
        ORDER BY id
        LIMIT 1
        """
    )

    if not row:
        return jsonify({"error": "No personal data found."}), 404

    return jsonify(
        {
            "name": row["name"],
            "title": row["title"],
            "dateOfBirth": row["date_of_birth"],
            "location": row["location"],
            "email": row["email"],
            "phone": row["phone"],
            "placesLived": to_python_json(row["places_lived"]),
            "languages": to_python_json(row["languages"]),
            "social": {
                "github": row["social_github"],
                "linkedin": row["social_linkedin"],
            },
        }
    )


@app.get("/api/professional")
def get_professional_data():
    row = fetch_one(
        """
        SELECT
            experience,
            skills,
            certifications
        FROM professional_data
        ORDER BY id
        LIMIT 1
        """
    )

    if not row:
        return jsonify({"error": "No professional data found."}), 404

    return jsonify(
        {
            "experience": to_python_json(row["experience"]),
            "skills": to_python_json(row["skills"]),
            "certifications": to_python_json(row["certifications"]),
        }
    )


@app.get("/api/hobbies")
def get_hobbies_data():
    row = fetch_one(
        """
        SELECT
            passions
        FROM hobbies_data
        ORDER BY id
        LIMIT 1
        """
    )

    if not row:
        return jsonify({"error": "No hobbies data found."}), 404

    return jsonify({"passions": to_python_json(row["passions"])})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
