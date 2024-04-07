from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, ComputerVisionOcrErrorException
from msrest.authentication import CognitiveServicesCredentials
import time
from dotenv import load_dotenv
import os

load_dotenv()

computervision_client = ComputerVisionClient(os.getenv('ENDPOINT'),CognitiveServicesCredentials(os.getenv('SUBSCRIPTION_KEY')))

def extractTextFromImage(read_image_url):
    try:
        read_response = computervision_client.read(read_image_url, raw=True)
        result = ''
        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]
        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    result = result + " " + line.text
            return {'Result':result,'Status':read_result.status}
    except ComputerVisionOcrErrorException as error:
            return {'Result':'None','Status':error}
