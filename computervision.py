from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, ComputerVisionOcrErrorException
from msrest.authentication import CognitiveServicesCredentials
import time
from dotenv import load_dotenv
import os
import re
from qrcode import decodeQR
import requests
from monitoring import monitoring

load_dotenv()

computervision_client = ComputerVisionClient(os.getenv('ENDPOINT'),CognitiveServicesCredentials(os.getenv('SUBSCRIPTION_KEY')))

def extractTextFromImage(read_image_url):
    try:
        read_response = computervision_client.read(read_image_url, raw=True)
        result = ''
        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]
        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)      
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    result = result + " " + line.text
            return {'Result':result,'Status':read_result.status}
    except ComputerVisionOcrErrorException as error:
            return {'Result':None,'Status':error} 

def regextodict(text):
    
    product_pattern = r'\b[A-Z](?![A-Z])[\w\s]+\. \d+\s?x?\s?\d+\.\d+ Euro\b'
    products = re.findall(product_pattern, text)
    extra_pattern = r'^(.*)\. (\d+) x (\d+\.\d+) Euro$'

    products_info = []

    for item in products:
        matches = re.match(extra_pattern, item)
        if matches:
            product = matches.group(1)
            quantity = int(matches.group(2))
            price = float(matches.group(3))
            product_info = {'Produit': product, 'Quantité': quantity, 'Prix': price}
            products_info.append(product_info)

    # Remove products from the text to get the address
    stripped_text = re.sub(product_pattern, '', text).strip()
	
    pattern = r'\b(?=Issue date|Bill to|Address|TOTAL\b)'
    parts = re.split(pattern, stripped_text, flags=re.IGNORECASE)
    invoice_data = {}

    # Process each part of the split text to fill the dictionary
    if len(parts) >= 5:
        invoice_data['ID Facture'] = parts[0].replace("INVOICE","").strip()
        invoice_data["Date d'émision"] = parts[1].replace("Issue date","").replace("issue date","").strip()
        # For 'Client', we assume 'Bill to' may include additional descriptors we want to exclude
        invoice_data['Client'] = parts[2].replace("Bill to","").replace("Brilllling", "").replace("Biilllling","").strip()
        invoice_data['Adresse'] = parts[3].replace("Address", "").strip()
        invoice_data['Commande'] = products_info
        # Assuming the total always follows 'TOTAL'
        invoice_data['Totale'] = re.search(r'\d+\.\d+(?=\s+Euro)', parts[-1]).group()
    return invoice_data

def infofacture(facture):
    base_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    url = f"{base_url}/{facture}"
    Code_API_factures = requests.get(url, headers={'accept': 'application/json'}).status_code
    ocr = extractTextFromImage(url)
    text = ocr['Result']
    status_ocr = ocr['Status']
    qr_info = decodeQR(url)
    #-----Car on utilise tous les services dans cette function, on appele notre monitoring maintenant------
    monitoring(Code_API_factures, ocr, status_ocr, qr_info)
    #la "magie" de tourner notre ligne de l'ocr a un dictionaire utilisable
    invoice_data = regextodict(text)
    #et avec .update on peut agreger un dictionaire a un autre pour combiner le code qr
    invoice_data.update(qr_info)
    return invoice_data





