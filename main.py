from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime
from qrcode import decodeQR
from computervision import extractTextFromImage
from regex import regextodict
from database import infotodb, getIDfromdb, getclientinfo, getinfomonitoring, monitoring
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def infofacture(facture):
    base_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    url = f"{base_url}/{facture}"
    Code_API_factures = requests.get(url, headers={'accept': 'application/json'}).status_code
    ocr = extractTextFromImage(url)
    text = ocr['Result']
    status_ocr = str(ocr['Status'])
    qr = decodeQR(url)
    qr_info = qr['Result']
    qr_monitor = qr['Monitor']
    #-----Car on utilise tous les services dans cette function, on appele notre monitoring maintenant------
    monitoring(Code_API_factures, text, status_ocr, qr_monitor)
    #la "magie" de tourner notre ligne de l'ocr a un dictionaire utilisable
    invoice_data = regextodict(text)
    #et avec .update on peut agreger un dictionaire a un autre pour combiner le code qr
    invoice_data.update(qr_info)
    return {'codeapi':Code_API_factures, 'invoice':invoice_data}

@app.post("/refresh")
async def refresh(request: Request):
	allinvoices = []
	global date
	api_url = "https://invoiceocrp3.azurewebsites.net/invoices"
	date = {'date': '2024-01-01 00:00:00'}
	try:
		while datetime.strptime(date['date'], '%Y-%m-%d %H:%M:%S') <= datetime.today().replace(hour=0, minute=0, second= 0):
			response = requests.get(api_url, headers={'accept': 'application/json'}, params={'start_date': date['date']})
			if response.status_code == 200:
				data = response.json()
				for item in data['invoices']:
					allinvoices.append(item['no'])
					date.update({'date': item['dt']})
			else:
				logging.exception("Failed to fetch data from API:")
				return {"error": f"ERROR: Reponse API {response.status_code}"}
		for facture in allinvoices:
			if response.status_code != 403:
				if facture.split('-')[0] not in getIDfromdb():
					try:
				#-----OCR de facture----------
						invoice = infofacture(facture)
						invoice_data = invoice['invoice']
				#----Mettre a jour la base des données si il y a une facture qui est pas déjà-------
						infotodb(invoice_data)
					except Exception as error:
						print(f"ERROR:{error}")
						invoice_data = None
		return {"message": "Factures actualisées corréctement !"}            
	except Exception as error:
		logging.exception("An error occurred while refreshing invoices:")
		return {"error": "An error occurred while refreshing invoices. Please check logs for more information."}

@app.get("/")
async def home(request: Request):
	return templates.TemplateResponse("index.html", {"request": request})

@app.get("/invoice")
async def invoice(request: Request):
		return templates.TemplateResponse("invoice.html", {"request": request})

@app.post("/invoice/")
async def invoice(request: Request, invoice_number: str = Form(...)):
	try:
		#-----From computervision.py----------
		invoice_data = infofacture(invoice_number)['invoice']
		infotodb(invoice_data)
	except Exception as error:
		print(f"ERROR: {error}")
		invoice_data = None
	return templates.TemplateResponse("invoice.html", {"request": request, "invoice_data": invoice_data})


@app.get("/reporting")
async def details(request: Request):
	return templates.TemplateResponse("client.html", {"request": request})

@app.post("/reporting")
async def get_details(request: Request, client_id: str = Form(...), select_type: str = Form(...)):
	# Assuming you have a function called getclientinfo to fetch client info based on client_id
	client_info = getclientinfo(client_id)
	client = client_info.get("Info", {})
	if select_type == "factures":
		data = client_info.get("Factures", {})
	else:
		data = client_info.get("Produits", {})
	return templates.TemplateResponse("client.html", {"request": request, "data": data, "client":client})

@app.get("/monitoring")
async def monitorpage(request: Request):
	monitoring = getinfomonitoring()
	return templates.TemplateResponse("monitoring.html", {"request": request, "monitoring": monitoring})

