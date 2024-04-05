import requests
from datetime import datetime

def getinvoices(allinvoices = []):
    api_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    date_str = '2019-12-18 09:28:00'
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    while date <= datetime.today().replace(hour=0, minute=0, second= 0):
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        response = requests.get(api_url, headers={'accept': 'application/json'}, params={'start_date': date})
        if response.status_code == 200:
            data = response.json()
            for item in data['invoices']:
                allinvoices.append(item['no'])
                date_str = item['dt']
        else:
            return f"Failed to fetch data from the API. Status code: {response.status_code}"
    return list(set(allinvoices))

def getinfo(facture):
    base_url = "https://invoiceocrp3.azurewebsites.net/invoices"
    url = f"{base_url}/{facture}"
    response = requests.get(url, headers={'accept': 'application/json'})

    if response.status_code == 200:
        invoices_data = response.json()
        return invoices_data
    else:
        return f"Failed to fetch data from the API. Status code: {response.status_code}"
