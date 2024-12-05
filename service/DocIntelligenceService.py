from api.DocIntelligence import DocIntelligence

def try_field(fields, keys):
    for key in keys:
        if key not in fields:
            return None
        else:
            fields = fields[key]
    return fields

class DocIntelligenceService():
    def __init__(self) -> None:
        self.docIntelligence = DocIntelligence()

    def image_to_df(self, file_path):
        doc = self.docIntelligence.analyze_read(file_path)
        fields = doc['documents'][0]['fields']

        receipt_dict = {}
        base_key_map = {
            'MerchantName': ['MerchantName', 'valueString'],
            'Subtotal': ['Subtotal', 'valueCurrency', 'amount'],
            'Total': ['Total', 'valueCurrency', 'amount'],
            'TotalTax': ['TotalTax', 'valueCurrency', 'amount'],
            'TransactionDate': ['TransactionDate', 'valueDate'],
            'TransactionTime': ['TransactionTime', 'valueTime']
        }
        for key, val in base_key_map.items():
            real_val = try_field(fields, val)
            receipt_dict[key] = real_val

        # Normalize the main dictionary

        item_key_map = {
            'Description': ['valueObject', 'Description', 'valueString'],
            'Price': ['valueObject', 'Price', 'valueCurrency', 'amount'],
            'Quantity': ['valueObject', 'Quantity', 'valueNumber'],
            'TotalPrice': ['valueObject', 'TotalPrice', 'valueCurrency', 'amount'],
        }
        
        items = []
        itemArray = fields['Items']['valueArray']
        for item in itemArray:
            item_dict = {}
            for key, val in item_key_map.items():
                real_val = try_field(item, val)
                item_dict[key] = real_val
            items.append(item_dict)

        return receipt_dict, items