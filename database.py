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

def infotodb(facture_json):
    # connection
    conn = pyodbc.connect( connectionString )
    
    ID_Facture = facture_json['ID Facture']
    Date = facture_json["Date d'émision"]
    Nom = facture_json['Client'] 
    Adresse = facture_json['Adresse']
    Commande = facture_json['Commande'] 
    Total = facture_json['Total']
    ID_Client = facture_json['Id_Client']
    Categorie = facture_json['Client_Category']

    QUERY_CLIENTS = f"""
            MERGE INTO dbo.Clients AS target
        USING (VALUES (?, ?, ?)) AS source (ID_Client, Categorie, Nom)
    ON target.ID_Client = source.ID_Client
        WHEN MATCHED THEN
    UPDATE SET target.Categorie = source.Categorie, target.Nom = source.Nom
        WHEN NOT MATCHED THEN
    INSERT (ID_Client, Categorie, Nom) VALUES (source.ID_Client, source.Categorie, source.Nom);

    """
    QUERY_COMMANDE = f"""
            MERGE INTO dbo.Commandes AS target
USING (VALUES (?, ?, ?, ?)) AS source (Produit, ID_Facture, Quantité, Prix_unitaire)
    ON target.ID_Facture = source.ID_Facture AND target.Produit = source.Produit
WHEN MATCHED THEN
    UPDATE SET target.Quantité = source.Quantité, target.Prix_unitaire = source.Prix_unitaire
WHEN NOT MATCHED THEN
    INSERT (Produit, ID_Facture, Quantité, Prix_unitaire)
    VALUES (source.Produit, source.ID_Facture, source.Quantité, source.Prix_unitaire);

    """
    QUERY_FACTURE = f"""
            MERGE INTO dbo.Factures AS target
USING (VALUES (?, ?, ?, ?, ?)) AS source (ID_Facture, Date, ID_Client, Adresse, Total)
    ON target.ID_Facture = source.ID_Facture
WHEN MATCHED THEN
    UPDATE SET target.Date = source.Date, 
               target.ID_Client = source.ID_Client, 
               target.Adresse = source.Adresse, 
               target.Total = source.Total
WHEN NOT MATCHED THEN
    INSERT (ID_Facture, Date, ID_Client, Adresse, Total)
    VALUES (source.ID_Facture, source.Date, source.ID_Client, source.Adresse, source.Total);

    """
    
    cursor = conn.cursor()
    cursor.execute(QUERY_CLIENTS, ID_Client, Categorie, Nom)
    cursor.execute(QUERY_FACTURE, ID_Facture, Date, ID_Client, Adresse, Total)
    for element in Commande:
        Produit = element['Produit']
        Quantité = element['Quantité']
        Prix_unitaire = element['Prix']
        cursor.execute(QUERY_COMMANDE, Produit, ID_Facture, Quantité, Prix_unitaire )
    conn.commit()
    cursor.close()
    conn.close()

def getIDfromdb():
    # connection
    conn = pyodbc.connect( connectionString )
    SQL_QUERY = f"""
            SELECT ID_Facture FROM dbo.Factures
    """
    cursor = conn.cursor()
    cursor.execute(SQL_QUERY)
    rows = cursor.fetchall()
# Convert list of tuples to a list (assuming you're fetching only one column)
    facturesdb = [row[0] for row in rows]
# Close the connection
    cursor.close()
    conn.close()
    return facturesdb
