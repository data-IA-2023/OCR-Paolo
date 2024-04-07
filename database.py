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
	QUERY_PRODUIT = f"""
			MERGE INTO dbo.Produits AS target
USING (VALUES (?, ?)) AS source (Produit, Prix)
	ON target.Produit = source.Produit
WHEN MATCHED THEN
	UPDATE SET target.Prix = source.Prix
WHEN NOT MATCHED THEN
	INSERT (Produit, Prix)
	VALUES (source.Produit, source.Prix);

	"""
	cursor = conn.cursor()
	cursor.execute(QUERY_CLIENTS, ID_Client, Categorie, Nom)
	cursor.execute(QUERY_FACTURE, ID_Facture, Date, ID_Client, Adresse, Total)
	for element in Commande:
		Produit = element['Produit']
		Quantité = element['Quantité']
		Prix_unitaire = element['Prix']
		cursor.execute(QUERY_COMMANDE, Produit, ID_Facture, Quantité, Prix_unitaire)
		cursor.execute(QUERY_PRODUIT, Produit, Prix_unitaire)
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

def getclientinfo(id_client):
	conn = pyodbc.connect( connectionString )
	SQL_FACT = """
		SELECT ID_Facture, Date, Total
		FROM dbo.Factures 
		WHERE ID_Client = ?
	"""
	# SQL query to fetch product information
	SQL_PROD = """
		SELECT f.ID_Facture, c.Produit, c.Quantité, c.Prix_unitaire
		FROM dbo.Factures f
		JOIN dbo.Commandes c ON f.ID_Facture = c.ID_Facture
		WHERE f.ID_Client = ?
	"""
	SQL_INFO = """
		SELECT Categorie, Nom
		FROM dbo.Clients
		WHERE ID_Client = ?
	"""

	# Dictionary to store product information
	product_info = {}
	cursor = conn.cursor()
	cursor.execute(SQL_PROD, id_client)

	# Fetch all rows
	rows = cursor.fetchall()

	# Iterate over the rows and aggregate product info
	for row in rows:
		id_facture, produit, quantite, prix_unitaire = row

		# If the product is not already in the dictionary, initialize its entry
		if produit not in product_info:
			product_info[produit] = {"Prix": prix_unitaire, "Quantité": 0}

		# Update the total quantity and price for the product
		product_info[produit]["Quantité"] += quantite
		product_info[produit]["Total_dépensé"] = round(quantite*prix_unitaire, 2)

	# Close cursor and connection
	cursor = conn.cursor()
	cursor.execute(SQL_FACT, id_client)
	rows = cursor.fetchall()
	
	# Create a dictionary to store results
	result_dict = {}
	
	# Fill the dictionary with data
	for row in rows:
		ID_Facture = row[0]
		Date = row[1]
		Total = row[2]
		result_dict[ID_Facture] = {'Date': Date, 'Total': Total}

	#--------infoclient---------
	cursor = conn.cursor()
	cursor.execute(SQL_INFO, id_client)
	row = cursor.fetchall()

	Categorie = row[0][0]
	Nom = row[0][1]
	client_info={"Nom":Nom, "Categorie":Categorie}

	# Close the connection
	cursor.close()
	conn.close()
	infoclient={}
	infoclient['Factures'] = result_dict
	infoclient["Produits"] = product_info
	infoclient['Info'] = client_info
	
	return infoclient

def getinfomonitoring():

	SQL_QUERY = """
	SELECT TOP 5 * 
    FROM dbo.Monitoring 
    ORDER BY Timestamp DESC
	"""
	conn = pyodbc.connect( connectionString )
	cursor = conn.cursor()
	cursor.execute(SQL_QUERY)
	rows = cursor.fetchall()
	monitresult = []
	for row in rows:
		monit={}
		Timestamp, Code_API_factures, ComVis_result, ComVis_status, QR_result = row
		monit["Timestamp"] = Timestamp
		monit["Code_API_factures"] = Code_API_factures
		monit["ComVis_result"] = ComVis_result
		monit["ComVis_status"] = ComVis_status
		monit["QR_result"] = QR_result
		monitresult.append(monit)
	return monitresult
