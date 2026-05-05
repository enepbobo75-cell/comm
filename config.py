import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="ECOLE",
        user="postgres",
        password="postgres123"
    )
    return conn


