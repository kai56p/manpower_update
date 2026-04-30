import sqlite3
import pandas as pd
from io import BytesIO

DB_PATH = 'site_management.db'

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────

def init_dummy_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Supervisor roster with planned headcount
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deployments (
            Supervisor TEXT PRIMARY KEY,
            Site_Location TEXT,
            Planned_Workers INTEGER DEFAULT 0
        )
    ''')

    supervisors = [
        ('Suman_Structure',          'TMJP',  30),
        ('Alim_Lifting',             'Brani',  8),
        ('Junayed_Scaffolding',      'Brani',  4),
        ('Kanaja_MEP',               'TMJP',   3),
        ('Sheak_Safety',             'TMJP',   6),
        ('Aung_Surveyor',            'TMJP',   1),
        ('Kasthurisaravana_General', 'TMJP',   4),
        ('Nannu_Supply',             'TMJP',   7),
        ('Shahalom_Archi',           'TMJP',   4),
        ('Sala_HB',                  'TMJP',   1),
        ('Matubbar Kajol_Facade',    'TMJP',   5),
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO deployments (Supervisor, Site_Location, Planned_Workers)
        VALUES (?, ?, ?)
    ''', supervisors)

    # Daily manpower logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            date TEXT,
            supervisor TEXT,
            workers INTEGER,
            remarks TEXT DEFAULT '',
            UNIQUE(date, supervisor)
        )
    ''')

    # Overtime logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS overtime_logs (
            date TEXT,
            supervisor TEXT,
            ot_workers INTEGER,
            remarks TEXT DEFAULT '',
            UNIQUE(date, supervisor)
        )
    ''')

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# LOOKUPS
# ─────────────────────────────────────────────

def get_all_supervisors():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT Supervisor, Site_Location, Planned_Workers FROM deployments ORDER BY Supervisor",
        conn
    )
    conn.close()
    return df

def get_supervisor_list():
    return get_all_supervisors()['Supervisor'].tolist()

def get_planned(supervisor):
    conn = get_connection()
    row = conn.execute(
        "SELECT Planned_Workers FROM deployments WHERE Supervisor = ?", (supervisor,)
    ).fetchone()
    conn.close()
    return row[0] if row else 0

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def log_daily_deployment(log_date, supervisor, workers, remarks=''):
    conn = get_connection()
    conn.execute('''
        INSERT OR REPLACE INTO daily_logs (date, supervisor, workers, remarks)
        VALUES (?, ?, ?, ?)
    ''', (log_date, supervisor, workers, remarks))
    conn.commit()
    conn.close()

def log_overtime(log_date, supervisor, ot_workers, remarks=''):
    conn = get_connection()
    conn.execute('''
        INSERT OR REPLACE INTO overtime_logs (date, supervisor, ot_workers, remarks)
        VALUES (?, ?, ?, ?)
    ''', (log_date, supervisor, ot_workers, remarks))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# SUMMARIES
# ─────────────────────────────────────────────

def get_todays_summary(log_date):
    conn = get_connection()
    roster = get_all_supervisors()

    logged = pd.read_sql(f"""
        SELECT supervisor AS Supervisor, workers AS Workers, remarks AS Remarks
        FROM daily_logs WHERE date = '{log_date}'
    """, conn)
    conn.close()

    merged = roster.merge(logged, on='Supervisor', how='left')
    merged['Status']   = merged['Workers'].apply(lambda x: '✅ Logged' if pd.notna(x) else '⏳ Pending')
    merged['Workers']  = merged['Workers'].fillna(0).infer_objects(copy=False).astype(int)
    merged['Remarks']  = merged['Remarks'].fillna('')
    merged['Variance'] = merged.apply(
        lambda r: int(r['Workers'] - r['Planned_Workers']) if r['Status'] == '✅ Logged' else None,
        axis=1
    )

    filled_df = merged[merged['Status'] == '✅ Logged'][[
        'Supervisor', 'Site_Location', 'Workers', 'Planned_Workers', 'Variance', 'Remarks'
    ]].rename(columns={'Site_Location': 'Site', 'Planned_Workers': 'Planned'})

    status_df = merged[[
        'Supervisor', 'Workers', 'Remarks', 'Status'
    ]]

    total    = int(filled_df['Workers'].sum()) if not filled_df.empty else 0
    unfilled = merged[merged['Status'] == '⏳ Pending']['Supervisor'].tolist()

    return filled_df, total, status_df, unfilled


def get_todays_ot_summary(log_date):
    conn = get_connection()
    roster = get_all_supervisors()

    logged = pd.read_sql(f"""
        SELECT supervisor AS Supervisor, ot_workers AS OT_Workers, remarks AS Remarks
        FROM overtime_logs WHERE date = '{log_date}'
    """, conn)
    conn.close()

    merged = roster.merge(logged, on='Supervisor', how='left')
    merged['Status']     = merged['OT_Workers'].apply(lambda x: '✅ Logged' if pd.notna(x) else '⏳ Pending')
    merged['OT_Workers'] = merged['OT_Workers'].fillna(0).infer_objects(copy=False).astype(int)
    merged['Remarks']    = merged['Remarks'].fillna('')

    filled_df = merged[merged['Status'] == '✅ Logged'][[
        'Supervisor', 'Site_Location', 'OT_Workers', 'Remarks'
    ]].rename(columns={'Site_Location': 'Site', 'OT_Workers': 'OT Workers'})

    status_df = merged[[
        'Supervisor', 'OT_Workers', 'Remarks', 'Status'
    ]].rename(columns={'OT_Workers': 'OT Workers'})

    total    = int(filled_df['OT Workers'].sum()) if not filled_df.empty else 0
    unfilled = merged[merged['Status'] == '⏳ Pending']['Supervisor'].tolist()

    return filled_df, total, status_df, unfilled

# ─────────────────────────────────────────────
# EXCEL EXPORT
# ─────────────────────────────────────────────

def export_daily_excel(log_date):
    """Returns BytesIO Excel with Manpower + Overtime sheets."""
    conn = get_connection()
    roster = get_all_supervisors()

    mp_logged = pd.read_sql(f"""
        SELECT supervisor AS Supervisor, workers AS Workers, remarks AS Remarks
        FROM daily_logs WHERE date = '{log_date}'
    """, conn)

    ot_logged = pd.read_sql(f"""
        SELECT supervisor AS Supervisor, ot_workers AS OT_Workers, remarks AS Remarks
        FROM overtime_logs WHERE date = '{log_date}'
    """, conn)
    conn.close()

    # Manpower sheet
    mp = roster.merge(mp_logged, on='Supervisor', how='left')
    mp['Workers']  = mp['Workers'].fillna(0).astype(int)
    mp['Remarks']  = mp['Remarks'].fillna('')
    mp['Variance'] = mp['Workers'] - mp['Planned_Workers']
    mp['Status']   = mp['Workers'].apply(lambda x: 'Logged' if x > 0 else 'Pending')
    mp_out = mp[['Supervisor', 'Site_Location', 'Planned_Workers', 'Workers', 'Variance', 'Remarks', 'Status']].rename(
        columns={'Site_Location': 'Site', 'Planned_Workers': 'Planned', 'Workers': 'Actual'}
    )

    # Overtime sheet
    ot = roster.merge(ot_logged, on='Supervisor', how='left')
    ot['OT_Workers'] = ot['OT_Workers'].fillna(0).astype(int)
    ot['Remarks']    = ot['Remarks'].fillna('')
    ot['Status']     = ot['OT_Workers'].apply(lambda x: 'Logged' if x > 0 else 'Pending')
    ot_out = ot[['Supervisor', 'Site_Location', 'OT_Workers', 'Remarks', 'Status']].rename(
        columns={'Site_Location': 'Site', 'OT_Workers': 'OT Workers'}
    )

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        mp_out.to_excel(writer, sheet_name='Manpower', index=False)
        ot_out.to_excel(writer, sheet_name='Overtime', index=False)

        for sheet_name, df in [('Manpower', mp_out), ('Overtime', ot_out)]:
            ws = writer.sheets[sheet_name]
            for i, col in enumerate(df.columns, 1):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 3
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max_len, 40)

    buf.seek(0)
    return buf
