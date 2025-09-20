import sqlite3
from sigma_partial import sigma_partial

def lookup_partial(conn, partial: str):
    """Busca palavras cujo σ começa com 'partial'"""
    cur = conn.cursor()
    # LIKE começa com partial
    cur.execute("SELECT lang, lemma, conf FROM gama WHERE scode LIKE ?", (partial + '%',))
    return cur.fetchall()