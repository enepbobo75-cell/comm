import psycopg2
import os

def get_connection():
    database_url = os.environ.get('DATABASE_URL', 
        'postgresql://commerce_6snn_user:cRU7C4jx204dTe3vhIDaBW4c9FveiwXA@dpg-d7t8ae1kh4rs73df2t3g-a.ohio-postgres.render.com/commerce_6snn')
    conn = psycopg2.connect(database_url)
    return conn