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
                full_name TEXT,
                username TEXT,
                join_date TIMESTAMP,
                referrer_id INTEGER,
                downloads_today INTEGER DEFAULT 0,
                last_download_date DATE,
                pro_until TIMESTAMP,
                language TEXT DEFAULT 'uz'
            )
        ''')
        self.conn.commit()
        
        # Migratsiya: Eski bazada language ustuni yo'q bo'lsa qo'shib qo'yamiz
        try:
            self.cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "uz"')
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def add_user(self, telegram_id, full_name, username, referrer_id=None):
        """Yangi foydalanuvchini bazaga qo'shish"""
        try:
            self.cursor.execute('''
                INSERT INTO users (telegram_id, full_name, username, join_date, referrer_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (telegram_id, full_name, username, datetime.now(), referrer_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, telegram_id):
        self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        return self.cursor.fetchone()

    def get_language(self, telegram_id):
        self.cursor.execute('SELECT language FROM users WHERE telegram_id = ?', (telegram_id,))
        res = self.cursor.fetchone()
        return res[0] if res and res[0] else 'uz'

    def set_language(self, telegram_id, language):
        self.cursor.execute('UPDATE users SET language = ? WHERE telegram_id = ?', (language, telegram_id))
        self.conn.commit()

    def is_pro(self, telegram_id):
        self.cursor.execute('SELECT pro_until FROM users WHERE telegram_id = ?', (telegram_id,))
        res = self.cursor.fetchone()
        if res and res[0]:
            try:
                if isinstance(res[0], datetime):
                    return res[0] > datetime.now()
                pro_date = datetime.fromisoformat(str(res[0]))
                return pro_date > datetime.now()
            except Exception:
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
            self.add_user(telegram_id, "User", "", None)
            return True

        downloads_today, last_download_date = res
        today_str = datetime.now().date().isoformat()

        # Agar oxirgi yuklash kecha bo'lgan bo'lsa, limitni nolga tushiramiz
        if str(last_download_date) != today_str:
            self.cursor.execute('UPDATE users SET downloads_today = 0, last_download_date = ? WHERE telegram_id = ?', (today_str, telegram_id))
            self.conn.commit()
            downloads_today = 0

        # Kunlik 5 ta limit
        return (downloads_today or 0) < 5

    def add_download(self, telegram_id):
        today_str = datetime.now().date().isoformat()
        self.cursor.execute('UPDATE users SET downloads_today = downloads_today + 1, last_download_date = ? WHERE telegram_id = ?', (today_str, telegram_id))
        self.conn.commit()

    def count_users(self):
        self.cursor.execute('SELECT COUNT(id) FROM users')
        return self.cursor.fetchone()[0]

    def get_all_users(self):
        self.cursor.execute('SELECT telegram_id FROM users')
        return [row[0] for row in self.cursor.fetchall()]

db = Database()
