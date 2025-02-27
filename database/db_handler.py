import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

class DatabaseHandler:
    def __init__(self):
        db_path = Path(__file__).parent.parent / 'data' / 'electricity_prices.db'
        self.db_path = str(db_path)

        backup_path = Path(__file__).parent.parent / 'data' / 'electricity_prices_backup.db'
        self.backup_path = str(backup_path)

    def initialize_db(self, path=None):
        if path is None:
            path = self.db_path
        if not Path(path).exists():
            with sqlite3.connect(path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS electricity_prices (
                        timestamp DATETIME PRIMARY KEY,
                        price FLOAT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

    def save_prices(self, df):
        with sqlite3.connect(self.db_path) as conn:
            # Convert DataFrame timestamps to string format SQLite can handle
            df_to_save = df.copy()
            df_to_save['timestamp'] = df_to_save['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S%z')
            
            # Use pandas to_sql with "replace" mode for handling duplicates
            df_to_save.to_sql('electricity_prices', conn, 
                            if_exists='replace', 
                            index=False)

    def get_latest_prices(self, target_date=None, limit=24):
        with sqlite3.connect(self.db_path) as conn:
            if target_date is None:
                query = f'''
                    SELECT * FROM electricity_prices 
                    ORDER BY timestamp DESC 
                    LIMIT {limit}
                '''
                params = []
            else:
                # Convert target_date to string format with timezone consideration
                query = '''
                    SELECT * FROM electricity_prices 
                    WHERE substr(timestamp, 1, 10) = ?
                    ORDER BY timestamp ASC
                '''
                params = [target_date.strftime('%Y-%m-%d')]

            df = pd.read_sql_query(query, conn, params=params)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S%z')
            return df

if __name__ == "__main__":
    db = DatabaseHandler()
    db.initialize_db()
    db.initialize_db(path=db.backup_path)

    print(db.get_latest_prices(limit=1000))