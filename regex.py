import re

def regextodict(text):
    
    product_pattern = r'\b[A-ZÀÉÈÊËÎÏÔŒÙÛÜÇ][^\dA-ZÀÉÈÊËÎÏÔŒÙÛÜÇ]+\. \d+\s?x?\s?\d+\.\s?\d+ [Ee]uro\b'
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
        invoice_data['Client'] = parts[2].replace("Bill to","").replace("Brilllling", "").replace("Biilllling","").replace("Billlling", "").strip()
        invoice_data['Adresse'] = parts[3].replace("Address", "").strip()
        invoice_data['Commande'] = products_info
        # Assuming the total always follows 'TOTAL'
        invoice_data['Total'] = re.search(r'\d+\.\d+(?=\s+Euro)', parts[-1]).group()
    return invoice_data