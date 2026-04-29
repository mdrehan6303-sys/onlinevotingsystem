# app_db.py
from mysql.connector import pooling
from flask import g
import os

db_pool = None

def init_db_pool():
    global db_pool
    db_pool = pooling.MySQLConnectionPool(
        pool_name="voting_pool",
        pool_size=10,
        pool_reset_session=True,
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", "root123"),
        database=os.environ.get("MYSQL_DATABASE", "voting_system")
    )

def get_db():
    if db_pool is None:
        init_db_pool()
    if 'db' not in g:
        g.db = db_pool.get_connection()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass
