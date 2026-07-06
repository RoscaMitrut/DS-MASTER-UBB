INSERT INTO personal_data (
    id,
    name,
    title,
    date_of_birth,
    location,
    email,
    places_lived,
    languages,
    social_github,
    social_linkedin
)
VALUES (
    1,
    'Rosca Eduard-Mitrut',
    'Software Developer',
    'April 17, 2003',
    'Cluj-Napoca, Romania',
    'reduardmitrut@gmail.com',
    '["Cluj-Napoca, Romania", "Sarmas, Romania", "Darjiu, Romania", "asdf"]'::jsonb,
    '["Romanian (Native)", "English (Fluent)", "Hungarian (Elementary)"]'::jsonb,
    'https://github.com/RoscaMitrut',
    'https://www.linkedin.com/in/eduard-mitrut-rosca-329238225/'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    title = EXCLUDED.title,
    date_of_birth = EXCLUDED.date_of_birth,
    location = EXCLUDED.location,
    email = EXCLUDED.email,
    places_lived = EXCLUDED.places_lived,
    languages = EXCLUDED.languages,
    social_github = EXCLUDED.social_github,
    social_linkedin = EXCLUDED.social_linkedin;

INSERT INTO professional_data (
    id,
    experience,
    skills,
    certifications
)
VALUES (
    1,
    '[
        {"role": "Master''s in Data Science", "company": "Babes-Bolyai University", "period": "Oct 2025 - Present"},
        {"role": "Bachelor''s in Computer Science", "company": "Babes-Bolyai University", "period": "Oct 2022 - Jul 2025"}
    ]'::jsonb,
    '[
        {"category": "Programming Languages", "items": ["Python", "C/C++", "C#", "Java", "JavaScript"]},
        {"category": "Frameworks", "items": ["Spring", "React", "ASP.NET Core"]},
        {"category": "Machine Learning", "items": ["TensorFlow", "Keras", "NumPy", "Pandas", "Matplotlib"]},
        {"category": "Version Control", "items": ["Git", "GitHub"]},
        {"category": "Others", "items": ["SQL", "Linux", "Docker"]}
    ]'::jsonb,
    '[
        {"name": "CAE C1 Advanced English Certificate", "issuer": "Cambridge University Press & Assessment", "year": "2021"},
        {"name": "Digital Literacy Certificate - ECDL", "issuer": "ICDL Foundation", "year": "2021"}
    ]'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    experience = EXCLUDED.experience,
    skills = EXCLUDED.skills,
    certifications = EXCLUDED.certifications;

INSERT INTO hobbies_data (id, passions)
VALUES (
    1,
    '[
        {"icon": "🎵", "title": "Music", "description": "Listening to music, mostly Rap, but lately also Indie Rock and Heavy Metal."},
        {"icon": "🏔️", "title": "Hiking", "description": "Exploring what the Carpathians have to offer, mostly hiking by myself to clear my mind."},
        {"icon": "🎮", "title": "Gaming", "description": "Mostly MMORPGs when I am alone and all types of LAN games when I am with friends."},
        {"icon": "🛠️", "title": "Tinkering", "description": "Fixing and modifying things for relatives and around the house."}
    ]'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    passions = EXCLUDED.passions;
