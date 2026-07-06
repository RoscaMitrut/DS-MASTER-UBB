import os
import sqlite3

class DatabaseManager:
    def __init__(self, workspace_name):
        self.workspace_dir = "workspaces"
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
            
        safe_name = workspace_name.strip().replace(' ', '_').lower()
        self.db_path = os.path.join(self.workspace_dir, f"{safe_name}.db")
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dataset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                metadata TEXT,
                source TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS label_schema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT,
                input_type TEXT,
                options TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                question_id INTEGER,
                answer_value TEXT,
                FOREIGN KEY(dataset_id) REFERENCES dataset(id),
                FOREIGN KEY(question_id) REFERENCES label_schema(id)
            )
        ''')
        
        conn.commit()
        conn.close()