import sqlite3
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_file=None):
        if db_file is None:
            # Railway kabi serverlar uchun doimiy xotira papkasi
            if os.path.exists('/app/data'):
                db_file = '/app/data/database.db'
            else:
                db_file = 'database.db'
                
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                downloads_today INTEGER DEFAULT 0,
                last_download_date TEXT,
                language TEXT DEFAULT 'uz',
                pro_until TIMESTAMP,
                referrer_id INTEGER
            )
        ''')
        self.conn.commit()

    def add_user(self, telegram_id, referrer_id=None):
        self.cursor.execute('INSERT OR IGNORE INTO users (telegram_id, referrer_id) VALUES (?, ?)', (telegram_id, referrer_id))
        self.conn.commit()

    def get_language(self, telegram_id):
        self.cursor.execute('SELECT language FROM users WHERE telegram_id = ?', (telegram_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 'uz'

    def set_language(self, telegram_id, language):
        self.cursor.execute('UPDATE users SET language = ? WHERE telegram_id = ?', (language, telegram_id))
        self.conn.commit()

    def is_pro(self, telegram_id):
        self.cursor.execute('SELECT pro_until FROM users WHERE telegram_id = ?', (telegram_id,))
        res = self.cursor.fetchone()
        if res and res[0]:
            try:
                # fromisoformat handles both with and without microseconds
                pro_date = datetime.fromisoformat(res[0])
                return pro_date > datetime.now()
            except ValueError:
                pass
        return False

    def grant_pro(self, telegram_id, days=7):
        new_date = datetime.now() + timedelta(days=days)
        self.cursor.execute('UPDATE users SET pro_until = ? WHERE telegram_id = ?', (new_date, telegram_id))
        self.conn.commit()

    def get_referral_count(self, telegram_id):
        self.cursor.execute('SELECT COUNT(id) FROM users WHERE referrer_id = ?', (telegram_id,))
        return self.cursor.fetchone()[0]

    def check_limit(self, telegram_id):
        # 1. Pro bo'lsa limit yo'q
        if self.is_pro(telegram_id):
            return True

        self.cursor.execute('SELECT downloads_today, last_download_date FROM users WHERE telegram_id = ?', (telegram_id,))
        res = self.cursor.fetchone()
        if not res:
            return False

        downloads_today, last_download_date = res
        today_str = datetime.now().date().isoformat()

        # Agar oxirgi yuklash kecha bo'lgan bo'lsa, limitni nolga tushiramiz
        if last_download_date != today_str:
            self.cursor.execute('UPDATE users SET downloads_today = 0, last_download_date = ? WHERE telegram_id = ?', (today_str, telegram_id))
            self.conn.commit()
            downloads_today = 0

        # Kunlik 5 ta limit
        return downloads_today < 5

    def add_download(self, telegram_id):
        today_str = datetime.now().date().isoformat()
        self.cursor.execute('UPDATE users SET downloads_today = downloads_today + 1, last_download_date = ? WHERE telegram_id = ?', (today_str, telegram_id))
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute('SELECT telegram_id FROM users')
        return [row[0] for row in self.cursor.fetchall()]

db = Database()
