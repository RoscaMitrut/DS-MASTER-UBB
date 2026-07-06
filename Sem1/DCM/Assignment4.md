# Assignment 4

- I used pgAdmin4

Created `dcm_user` using the GUI

Created a new connection `DCM Connection` using GUI

Created database `dcm_db` using GUI

Created the tables using the following querries:
```sql
CREATE TABLE public.year_recession_info
(
    "Year" integer PRIMARY KEY,
    "Is_Recession" boolean
);

CREATE TABLE public.genres
(
    "GenreID" serial PRIMARY KEY,
    "Name" text UNIQUE
);

CREATE TABLE public.movies
(
    "MovieID" serial PRIMARY KEY,
    "Title" text NOT NULL,
    "Year" integer,
    "Metascore" integer,
    "imdbRating" numeric(3, 1),
    "AdjustedBoxOffice" numeric(15, 2),
    "RottenTomatoes" integer,
    CONSTRAINT fk_year FOREIGN KEY ("Year") REFERENCES public.year_recession_info ("Year")
);

CREATE TABLE public.movie_genres
(
    "MovieID" integer REFERENCES public.movies ("MovieID"),
    "GenreID" integer REFERENCES public.genres ("GenreID"),
    PRIMARY KEY ("MovieID", "GenreID")
);
```
Created a new table that's meant to help with inputing the data from a CSV file.
```sql
CREATE TABLE public.movies_staging
(
    id serial PRIMARY KEY,
    "Title" text,
    "Year" integer,
    "Genre" text,
    "Metascore" integer,
    "imdbRating" numeric(3, 1),
    "Is_Recession" boolean,
    "AdjustedBoxOffice" numeric(15, 2),
    "RottenTomatoes" integer
);
```
Used PSQL since that's what pgAdmin suggested after a couple of failed attempts at using querries
```
\copy public.movies_staging ("Title", "Year", "Genre", "Metascore", "imdbRating", "Is_Recession", "AdjustedBoxOffice", "RottenTomatoes") FROM 'C:\Users\Redward\Desktop\ON_GIT\DS-MASTER-UBB\Sem1\DCM\data\ready\movies_with_inflation_data_ready.csv' DELIMITER ',' CSV HEADER;
```
Move the data from the staging table to their own tables
```sql
INSERT INTO public.year_recession_info ("Year", "Is_Recession")
SELECT DISTINCT "Year", "Is_Recession"
FROM public.movies_staging
ON CONFLICT ("Year") DO NOTHING;

INSERT INTO public.movies ("Title", "Year", "Metascore", "imdbRating", "AdjustedBoxOffice", "RottenTomatoes")
SELECT "Title", "Year", "Metascore", "imdbRating", "AdjustedBoxOffice", "RottenTomatoes"
FROM public.movies_staging;

INSERT INTO public.genres ("Name")
SELECT DISTINCT trim(unnest(string_to_array("Genre", ',')))
FROM public.movies_staging
ON CONFLICT ("Name") DO NOTHING;

INSERT INTO public.movie_genres ("MovieID", "GenreID")
SELECT m."MovieID", g."GenreID"
FROM public.movies_staging s
JOIN public.movies m ON s."Title" = m."Title" AND s."Year" = m."Year"
CROSS JOIN LATERAL unnest(string_to_array(s."Genre", ',')) AS s_genre
JOIN public.genres g ON trim(s_genre) = g."Name"
ON CONFLICT DO NOTHING;

-- DROP TABLE public.movies_staging;
-- DROP TABLE public.year_recession_info;
-- DROP TABLE public.movies;
-- DROP TABLE public.genres;
-- DROP TABLE public.movie_genres;
```
Display some data to make sure everything is okay
```sql
SELECT * FROM public.year_recession_info ORDER BY "Year" ASC LIMIT 25;

SELECT * FROM public.movies ORDER BY "MovieID" ASC LIMIT 25;

SELECT * FROM public.genres ORDER BY "GenreID" ASC LIMIT 25;

SELECT * FROM public.movie_genres ORDER BY "MovieID" ASC LIMIT 25;
```