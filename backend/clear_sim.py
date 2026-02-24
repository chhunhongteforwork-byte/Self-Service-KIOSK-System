import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("DELETE FROM store_receiptitem WHERE receipt_id IN (SELECT id FROM store_receipt WHERE source='SIMULATED')")
cur.execute("DELETE FROM store_receipt WHERE source='SIMULATED'")
conn.commit()
print("Successfully deleted all SIMULATED receipts and their items.")
conn.close()
