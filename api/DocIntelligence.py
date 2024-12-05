import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest

# use your `key` and `endpoint` environment variables
key = "e75ba2d7ffe441c183980ea468c6abea"
endpoint = "https://docparser-01.cognitiveservices.azure.com/"

class DocIntelligence():
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )

    def analyze_read(self, file_path):
        file = open(file_path, "rb")
        bytez = bytearray(file.read())

        # poller = client.begin_analyze_document(
        #     "prebuilt-read", AnalyzeDocumentRequest(url_source=formUrl
        # ))

        poller = self.client.begin_analyze_document(
            "prebuilt-receipt", AnalyzeDocumentRequest(bytes_source=bytez # "prebuilt-read"
        ))
        result: AnalyzeResult = poller.result()
        
        return result.as_dict()