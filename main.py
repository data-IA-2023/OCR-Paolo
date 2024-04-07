from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime
from computervision import infofacture
from database import infotodb, getIDfromdb
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.post("/refresh")
async def refresh(request: Request):
    allinvoices = []
    global date
    api_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    date = {'date': '2019-12-18 09:28:00'}
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
            if facture.split('-')[0] not in getIDfromdb():
                try:
            #-----OCR de facture----------
                    invoice = infofacture(facture)
                    invoice_data = invoice['invoice']
            #----Mettre a jour la base des données si il y a une facture qui est pas déjà-------
                    infotodb(invoice_data)
                except Exception as error:
                    print(error)
                    invoice_data = None
                    if invoice['codeapi'] != 200:
                        break
                    
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
        print(error)
        invoice_data = None
    return templates.TemplateResponse("invoice.html", {"request": request, "invoice_data": invoice_data})

