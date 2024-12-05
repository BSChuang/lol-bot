from api import SQL

class SQLService():
    def __init__(self):
        self.db = SQL.DB()

    def insert_all(self, receipt, items):
        receipt_id = self.insert_receipt(receipt)
        self.insert_items(receipt_id, items)

    def insert_receipt(self, receipt):
        insert_query = """
            INSERT INTO receipts 
            (MerchantName, Subtotal, Total, TotalTax, TransactionDate, TransactionTime)
            VALUES (:MerchantName, :Subtotal, :Total, :TotalTax, :TransactionDate, :TransactionTime)
        """
        return self.db.write_query(insert_query, receipt)
    
    def insert_items(self, receiptId, items):
        insert_query = """
            INSERT INTO items 
            (ReceiptId, Description, Price, Quantity, TotalPrice)
            VALUES (:ReceiptId, :Description, :Price, :Quantity, :TotalPrice)
        """
        for item in items:
            item['ReceiptId'] = receiptId
            self.db.write_query(insert_query, item)