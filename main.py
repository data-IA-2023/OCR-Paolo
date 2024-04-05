from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime
from computervision import infofacture

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/what")
async def get_image(request: Request):
    allinvoices = []
    global date
    api_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    date = {'date': '2019-12-18 09:28:00'}
    while datetime.strptime(date['date'], '%Y-%m-%d %H:%M:%S') <= datetime.today().replace(hour=0, minute=0, second= 0):
        response = requests.get(api_url, headers={'accept': 'application/json'}, params={'start_date': date['date']})
        if response.status_code == 200:
            data = response.json()
            for item in data['invoices']:
                allinvoices.append(item['no'])
                date.update({'date': item['dt']})
        else:
            return {"error": "Failed to fetch data from the API"}
    return templates.TemplateResponse("invoices.html", {"request": request, "invoices": allinvoices})

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
        invoice_data = infofacture(invoice_number)
    except:
        invoice_data = None
    return templates.TemplateResponse("invoice.html", {"request": request, "invoice_data": invoice_data})

