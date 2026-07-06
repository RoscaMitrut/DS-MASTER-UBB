import json

class LabelingService:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_question(self, text, q_type="boolean", options=""):
        conn = self.db.get_connection()
        conn.execute("INSERT INTO label_schema (question_text, input_type, options) VALUES (?, ?, ?)", 
                     (text, q_type, options))
        conn.commit()
        conn.close()

    def get_questions(self):
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT id, question_text, input_type, options FROM label_schema")
        questions = []
        for r in cursor.fetchall():
            questions.append({
                "id": r[0], 
                "text": r[1], 
                "type": r[2], 
                "options": r[3] if r[3] else ""
            })
        conn.close()
        return questions

    def get_next_unlabeled(self):
        conn = self.db.get_connection()
        cursor = conn.execute('''
            SELECT d.id, d.content, d.metadata 
            FROM dataset d
            LEFT JOIN annotations a ON d.id = a.dataset_id
            WHERE a.id IS NULL
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"id": row[0], "content": row[1], "metadata": json.loads(row[2])}
        return None

    def save_annotation(self, dataset_id, answers_dict):
        conn = self.db.get_connection()
        for q_id, val in answers_dict.items():
            conn.execute('''
                INSERT INTO annotations (dataset_id, question_id, answer_value)
                VALUES (?, ?, ?)
            ''', (dataset_id, q_id, str(val)))
        conn.commit()
        conn.close()

    def get_stats(self):
        conn = self.db.get_connection()
        total = conn.execute("SELECT COUNT(*) FROM dataset").fetchone()[0]
        labeled = conn.execute("SELECT COUNT(DISTINCT dataset_id) FROM annotations").fetchone()[0]
        conn.close()
        return labeled, total
