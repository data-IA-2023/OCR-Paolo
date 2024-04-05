import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# valiable et lien de connexion à la base de donnée
connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={os.environ.get('SERVER')};DATABASE={os.environ.get('DATABASE')};UID={os.environ.get('USERNAME')};PWD={os.environ.get('PASSWORD')}'
def monitoring(Code_API_Factures, ComVis_Result, ComVis_Status, QR_Code):
    # connection
    conn = pyodbc.connect( connectionString )

    SQL_QUERY = f"""
            INSERT INTO dbo.Monitoring (Timestamp, Code_API_factures, ComVis_result, ComVis_status, QR_result)
            VALUES (?, ?, ?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(SQL_QUERY, datetime.now(), Code_API_Factures, ComVis_Result, ComVis_Status, QR_Code)
    conn.commit()
    cursor.close()
    conn.close()