import sqlite3
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                bot_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_ticket(self, user_message, bot_response):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tickets (user_message, bot_response) VALUES (?, ?)',
            (user_message, bot_response)
        )
        conn.commit()
        conn.close()
    
    def get_all_tickets(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows