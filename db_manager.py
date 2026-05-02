import sqlite3
from datetime import datetime

class CeylonDB:
    def __init__(self, db_path='ceylonguide.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Table 1: Chat history log
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Table 2: Transit routes
        cursor.execute('''CREATE TABLE IF NOT EXISTS Transit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_location TEXT,
            end_location TEXT,
            transport_type TEXT,
            estimated_time TEXT,
            price TEXT
        )''')

        # Table 3: Dynamically learned facts (approved by admin)
        cursor.execute('''CREATE TABLE IF NOT EXISTS learned_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT NOT NULL,
            response TEXT NOT NULL
        )''')

        # Table 4: Pending reviews (user suggestions waiting for admin approval)
        cursor.execute('''CREATE TABLE IF NOT EXISTS pending_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            user_suggestion TEXT NOT NULL
        )''')

        self.conn.commit()

    # ---- Chat History ----
    def log_chat(self, user_query, bot_response):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO history (user_query, bot_response) VALUES (?, ?)',
            (user_query, bot_response)
        )
        self.conn.commit()

    def get_chat_history(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT user_query, bot_response, timestamp FROM history ORDER BY id DESC LIMIT ?',
            (limit,)
        )
        return cursor.fetchall()

    # ---- Learned Facts ----
    def add_learned_fact(self, pattern, response):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO learned_facts (pattern, response) VALUES (?, ?)',
            (pattern, response)
        )
        self.conn.commit()

    def get_all_learned_facts(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT pattern, response FROM learned_facts')
        return cursor.fetchall()

    def get_all_learned_facts_with_ids(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, pattern, response FROM learned_facts')
        return cursor.fetchall()

    def delete_learned_fact(self, fact_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM learned_facts WHERE id=?', (fact_id,))
        self.conn.commit()

    # ---- Pending Reviews (User Suggestions) ----
    def submit_for_review(self, user_query, user_suggestion):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO pending_reviews (user_query, user_suggestion) VALUES (?, ?)',
            (user_query, user_suggestion)
        )
        self.conn.commit()

    def get_all_pending_reviews(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, user_query, user_suggestion FROM pending_reviews')
        return cursor.fetchall()

    def approve_fact(self, review_id):
        """Promote a pending review to a learned fact (Admin action)."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT user_query, user_suggestion FROM pending_reviews WHERE id=?',
            (review_id,)
        )
        row = cursor.fetchone()
        if row:
            pattern, response = row
            self.add_learned_fact(pattern, response)
            cursor.execute('DELETE FROM pending_reviews WHERE id=?', (review_id,))
            self.conn.commit()
            return True
        return False

    def reject_review(self, review_id):
        """Delete a pending review without learning it."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM pending_reviews WHERE id=?', (review_id,))
        self.conn.commit()

    # ---- Transit ----
    def get_all_routes(self):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT start_location, end_location, transport_type, estimated_time, price FROM Transit'
        )
        return cursor.fetchall()