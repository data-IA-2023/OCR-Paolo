from PIL import Image
from pyzbar.pyzbar import decode
import re
import requests
from io import BytesIO

#---Function that gives you the json response of the qr code----#

def decodeQR(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))

        info = decode(img)[0][0].decode('utf-8')

        # Define the regex pattern to match the desired keys and values
        pattern = r'(CUST|CAT):(\w+)'

        # Use re.findall() to find all matches in the text
        matches = re.findall(pattern, info)

        # Convert the matches into a dictionary
        result = {'Id_Client': matches[0][1], 'Client_Category': matches[1][1]}
        return result
    except:
        return None

