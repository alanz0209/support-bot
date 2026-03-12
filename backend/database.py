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
        
        # Table tickets avec statut et priorité
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                bot_response TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                file_url TEXT,
                feedback_positive INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_ticket(self, user_message, bot_response, file_url=None, source="bot"):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Déterminer la priorité selon les mots-clés
        priority = 'normal'
        urgent_keywords = ['urgent', 'urgence', 'critique', 'bloqué', 'emergency']
        if any(kw in user_message.lower() for kw in urgent_keywords):
            priority = 'urgent'
        
        cursor.execute(
            '''INSERT INTO tickets (user_message, bot_response, priority, file_url, status) 
               VALUES (?, ?, ?, ?, ?)''',
            (user_message, bot_response, priority, file_url, 'open')
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def update_ticket_status(self, ticket_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?',
            (status, datetime.now(), ticket_id)
        )
        conn.commit()
        conn.close()
    
    def update_ticket_priority(self, ticket_id, priority):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tickets SET priority = ?, updated_at = ? WHERE id = ?',
            (priority, datetime.now(), ticket_id)
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
    
    def get_ticket_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total tickets
        cursor.execute('SELECT COUNT(*) FROM tickets')
        stats['total'] = cursor.fetchone()[0]
        
        # Par statut
        cursor.execute('SELECT status, COUNT(*) FROM tickets GROUP BY status')
        stats['by_status'] = dict(cursor.fetchall())
        
        # Par priorité
        cursor.execute('SELECT priority, COUNT(*) FROM tickets GROUP BY priority')
        stats['by_priority'] = dict(cursor.fetchall())
        
        # Feedback
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE feedback_positive = 1')
        stats['positive_feedback'] = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE feedback_positive = 0')
        stats['negative_feedback'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def save_feedback(self, positive):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO analytics (event_type, event_data) VALUES (?, ?)',
            ('feedback', 'positive' if positive else 'negative')
        )
        conn.commit()
        conn.close()
    
    def get_analytics(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Conversations par jour (7 derniers jours)
        cursor.execute('''
            SELECT DATE(created_at), COUNT(*) 
            FROM tickets 
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        ''')
        daily_conversations = cursor.fetchall()
        
        # Top questions
        cursor.execute('''
            SELECT user_message, COUNT(*) as count 
            FROM tickets 
            GROUP BY LOWER(user_message) 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_questions = cursor.fetchall()
        
        conn.close()
        return {
            'daily_conversations': daily_conversations,
            'top_questions': top_questions
        }
    
    def get_ticket(self, ticket_id):
        """Récupère un ticket par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
        row = cursor.fetchone()
        conn.close()
        return row