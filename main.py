from fastapi import FastAPI
import requests
from datetime import datetime

app = FastAPI()


@app.get("/")
async def get_image():
    allinvoices = []
    global date
    api_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    date = {'date': '2019-12-18 09:28:00'}
    while date['date'] < datetime.today().replace(hour=0, minute=0, second= 0):
        response = requests.get(api_url, headers={'accept': 'application/json'}, params={'start_date': date['date']})
        if response.status_code == 200:
            data = response.json()
            for item in data['invoices']:
                allinvoices.append(item['no'])
                date.update({'date': item['dt']})
        else:
            return {"error": "Failed to fetch data from the API"}
    return {'invoices': allinvoices}
