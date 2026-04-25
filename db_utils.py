import sqlite3
import pandas as pd

def get_connection():
    return sqlite3.connect('site_management.db', check_same_thread=False)

def init_dummy_db():
    conn = get_connection()
    
    # 1. Static lookup data (Deployment_Code removed)
    dummy_data = pd.DataFrame({
        'Supervisor': ['Sheng Hui', 'Edrey', 'Faiz', 'Kaung'],
        'Site_Location': ['TMJP', 'Brani', 'Brani', 'Brani'],
    })
    dummy_data.to_sql('deployments', conn, if_exists='replace', index=False)
    
    # 2. Daily logs table (deployment_code column removed)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            date TEXT,
            supervisor TEXT,
            site_location TEXT,
            workers INTEGER,
            UNIQUE(date, supervisor) 
        )
    ''')
    conn.commit()
    return conn

def get_dropdown_options(column_name):
    conn = get_connection()
    query = f"SELECT DISTINCT {column_name} FROM deployments"
    return pd.read_sql(query, conn)[column_name].tolist()

def log_daily_deployment(log_date, supervisor, site, workers):
    """Inserts a new record or overwrites if the supervisor already logged today."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO daily_logs (date, supervisor, site_location, workers)
        VALUES (?, ?, ?, ?)
    ''', (log_date, supervisor, site, workers))
    conn.commit()

def get_todays_summary(log_date):
    """Returns today's deployment dataframe and the sum of workers."""
    conn = get_connection()
    query = f"""
        SELECT supervisor AS Supervisor, 
               site_location AS 'Site Location', 
               workers AS Workers 
        FROM daily_logs 
        WHERE date = '{log_date}'
    """
    df = pd.read_sql(query, conn)
    
    total_workers = df['Workers'].sum() if not df.empty else 0
    return df, total_workers