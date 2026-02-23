import sqlite3
import os


class Database:
    _instance = None
    con = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "database.db")

            cls.con = sqlite3.connect(db_path)

        return cls._instance

    def __del__(self):
        if self.con:
            self.con.close()


db = Database()
