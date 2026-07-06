import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

class DataIngestionService:
    def __init__(self, db_manager):
        self.db = db_manager

    def perform_demo_scrape(self, progress_callback):
        url = "https://realpython.github.io/fake-jobs/"
        progress_callback("Connecting to Demo Source...")
        
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            results = soup.find(id="ResultsContainer")
            job_cards = results.find_all("div", class_="card-content")
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            count = 0
            
            for index, card in enumerate(job_cards):
                title = card.find("h2", class_="title").text.strip()
                company = card.find("h3", class_="company").text.strip()
                location = card.find("p", class_="location").text.strip()
                desc_text = f"Job Title: {title}\nCompany: {company}\nLocation: {location}"
                
                meta = json.dumps({
                    "Title": title, 
                    "Company": company, 
                    "Location": location,
                    "Description": f"Full description for {title} at {company}..."
                })
                
                cursor.execute("SELECT id FROM dataset WHERE content = ?", (desc_text,))
                if cursor.fetchone() is None:
                    cursor.execute('''
                        INSERT INTO dataset (content, metadata, source)
                        VALUES (?, ?, ?)
                    ''', (desc_text, meta, "Demo: RealPython Jobs"))
                    count += 1
                
                progress_callback(f"Scraping: {int((index + 1) / len(job_cards) * 100)}%")

            conn.commit()
            conn.close()
            return f"Success! Added {count} demo records."

        except Exception as e:
            return f"Error: {str(e)}"

    def import_csv(self, filepath):
        try:
            df = pd.read_csv(filepath)
            if df.empty: return "Error: CSV is empty."

            text_col = df.columns[0]
            candidates = ['text', 'content', 'description', 'body', 'comment']
            for c in df.columns:
                if c.lower() in candidates:
                    text_col = c
                    break
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            count = 0

            for _, row in df.iterrows():
                content = str(row[text_col])
                meta = json.dumps(row.to_dict(), default=str)
                cursor.execute('''
                    INSERT INTO dataset (content, metadata, source)
                    VALUES (?, ?, ?)
                ''', (content, meta, "CSV Import"))
                count += 1

            conn.commit()
            conn.close()
            return f"Import Success! Added {count} rows."
        except Exception as e:
            return f"Import Failed: {str(e)}"

    def has_data(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dataset")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0