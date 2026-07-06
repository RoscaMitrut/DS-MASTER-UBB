CREATE TABLE IF NOT EXISTS personal_data (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    location TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    places_lived JSONB NOT NULL,
    languages JSONB NOT NULL,
    social_github TEXT NOT NULL,
    social_linkedin TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS professional_data (
    id SERIAL PRIMARY KEY,
    experience JSONB NOT NULL,
    skills JSONB NOT NULL,
    certifications JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS hobbies_data (
    id SERIAL PRIMARY KEY,
    passions JSONB NOT NULL
);
