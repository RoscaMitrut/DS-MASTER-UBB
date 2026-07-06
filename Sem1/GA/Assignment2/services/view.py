import json

class ViewService:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all_data(self):
        conn = self.db.get_connection()
        
        data_cursor = conn.execute("SELECT id, source, content, metadata FROM dataset")
        
        rows = []
        for r in data_cursor.fetchall():
            row_id = r[0]
            
            meta_dict = json.loads(r[3]) if r[3] else {}
            
            row_data = {
                "id": row_id, 
                "source": r[1], 
                "content_preview": r[2], 
                "metadata": meta_dict
            }

            
            lbl_cursor = conn.execute('''
                SELECT s.question_text, a.answer_value 
                FROM annotations a
                JOIN label_schema s ON a.question_id = s.id
                WHERE a.dataset_id = ?
            ''', (row_id,))
            
            labels = {}
            for lbl in lbl_cursor.fetchall():
                labels[lbl[0]] = lbl[1]
            
            row_data["labels"] = labels
            rows.append(row_data)
        
        conn.close()
        return rows